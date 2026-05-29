from flask import Flask, request, jsonify, render_template
import ollama
import os
from kokoro_onnx import Kokoro
import numpy as np
import sounddevice as sd
import re
import queue
import threading


# 1. INITIALIZE FLASK
app = Flask(__name__)

# 2. INITIALIZE GLOBAL AUDIO QUEUE & WORKER
audio_queue = queue.Queue()

def audio_worker():
    """
    Consumes generated audio fragments from the queue and plays them sequentially.
    This runs continuously in a background thread so playback doesn't freeze Flask.
    """
    while True:
        item = audio_queue.get()
        if item is None:
            break  # Stop signal
        samples, sample_rate = item
        sd.play(samples, sample_rate)
        sd.wait()  # Wait for the current sentence to finish before reading the next one
        audio_queue.task_done()

# Start background audio playback worker thread
playback_thread = threading.Thread(target=audio_worker, daemon=True)
playback_thread.start()


# 3. INITIALIZE MODELS
print("Initializing models (Qwen2.5, Kokoro)...")

# Brain Model Configuration
BRAIN_MODEL = 'Qwen2.5'


class TTSAgent:
    def __init__(self, model_path="kokoro-v1.0.onnx", voices_path="voices-v1.0.bin"):
        self.kokoro = Kokoro(model_path, voices_path)
        voice_heart = self.kokoro.get_voice_style("af_heart")
        voice_bella = self.kokoro.get_voice_style("af_bella")
        self.blended_voice = (voice_heart * 0.50) + (voice_bella * 0.50)

    def speak_sentence_async(self, text):
        """
        Generates audio for a single sentence and drops it into the playback queue.
        Executed inside a thread to keep the Ollama chunk stream completely unblocked.
        """
        if not text.strip(): 
            return
        try:
            samples, sample_rate = self.kokoro.create(
                text.strip(), 
                voice=self.blended_voice, 
                speed=1.1, 
                lang="en-us"
            )
            audio_queue.put((samples, sample_rate))
        except Exception as e:
            print(f"\n[TTS Error processing phrase]: {e}")

tts = TTSAgent()


# 4. CONVERSATION CONTEXT WINDOW CONFIGURATION
# Track the conversation history as a list of dictionaries matching Ollama API specs

PANDORA= """
You are PANDORA. You are a highly intelligent, concise, energetic, and strictly sarcastic AI assistant.

Your structural rules are absolute:
1. Always address the user as 'Boss'.
2. You must strictly never use asterisks or hashes. Do not use Markdown formatting. Ensure text is organized using only standard text spacing, line breaks, and capitalization for headers.
3. You must strictly end a response excluding the first response with either of these 4: 'Can I help you with anything?' or 'Do you want me to elaborate further?' or 'Should I tell you more about this subject?' or 'What else can I help you with?'.
4. You must strictly always end the first response with 'What can I help you with today?'
5. Never use emojis.
6. You must strictly end a response with a question.
"""

CHAT_HISTORY = [
    {'role': 'system', 'content': PANDORA}
]

# Control memory depth. 10 means tracking up to 10 context fragments (5 questions + 5 answers).
# Keeping this balance stops RAM memory leaks on systems handling intensive operations.
MAX_CONTEXT_TURNS = 10


# 5. DEFINE API ENDPOINTS
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """
    Expects JSON: {"question": "Your message here"}
    Manages sliding memory boundaries, pushes tokens to stream pipeline,
    and returns textual updates back to front-end layout structures.
    """
    global CHAT_HISTORY  # Gain reference to global storage across lifecycle calls
    
    data = request.json
    user_text = data.get('question', '')

    if not user_text:
        return jsonify({"error": "No question provided"}), 400

    if user_text.lower() == "end":
        # Reset memory arrays upon exit hook invocation
        CHAT_HISTORY = [{'role': 'system', 'content': 'You are a helpful, concise AI assistant.'}]
        return jsonify({"answer": "Goodbye! Context cleared.", "end": True})

    print(f"\nUser asked: {user_text}")

    # STEP 1: APPEND NEW USER INPUT INTO MEMORY TIMELINE
    CHAT_HISTORY.append({'role': 'user', 'content': user_text})

    # STEP 2: MANAGE SLIDING WINDOW CUTOFFS
    # Protect memory allocation limits by cleanly purging archaic elements past threshold constraints
    if len(CHAT_HISTORY) > MAX_CONTEXT_TURNS + 1:
        # Retain original index 0 (system configuration guidelines) while keeping latest data pairs
        CHAT_HISTORY = [CHAT_HISTORY[0]] + CHAT_HISTORY[-(MAX_CONTEXT_TURNS):]

    try:
        # STEP 3: SUBMIT TRACKED CONTEXT THREAD DIRECTLY TO LLM
        response_stream = ollama.chat(
            model=BRAIN_MODEL, 
            messages=CHAT_HISTORY,  # Pass historical tracking lists array
            stream=True  # Dynamic continuous evaluation parsing loop
        )

        sentence_buffer = ""
        full_response_text = ""

        print(f"Assistant ({BRAIN_MODEL}): ", end="", flush=True)

        for chunk in response_stream:
            token = chunk['message']['content']
            print(token, end="", flush=True)  # Instantly print output token onto tracking shell log

            sentence_buffer += token
            full_response_text += token

            # Match for end of sentence boundaries (. or ? or !) followed by spaces
            if re.search(r'[.!?]\s*$', sentence_buffer):
                sentence_to_speak = sentence_buffer
                sentence_buffer = ""  # Clean the internal parsing container

                # Schedule background asynchronous worker block for voice synthesization
                tts_thread = threading.Thread(
                    target=tts.speak_sentence_async, 
                    args=(sentence_to_speak,)
                )
                tts_thread.start()

        # Catch stray data objects remaining within sentence stack structures
        if sentence_buffer.strip():
            tts.speak_sentence_async(sentence_buffer)

        print()  # Finalize tracking log feed line spaces

        # STEP 4: RECORD INFERRED RESPONSE TO MAINTAIN MULTI-TURN CAPABILITY
        CHAT_HISTORY.append({'role': 'assistant', 'content': full_response_text})

        return jsonify({
            "status": "success",
            "user_input": user_text,
            "answer": full_response_text
        })

    except Exception as e:
        print(f"\n[Error occurred]: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# 6. RUN THE SERVER
if __name__ == '__main__':
    print(f"Starting Agent Server on {BRAIN_MODEL}...")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        audio_queue.put(None)  # Closes down audio consumer smoothly on shutdown
