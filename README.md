# PANDORA - Local Voice AI Agent 🤖🎙️

PANDORA is an ultra-lightweight, high-performance, completely local voice assistant. Built using a Flask backend, it offloads Speech-to-Text (STT) tasks to the client's web browser, saving massive amounts of system RAM. It pairs a dynamically prompted **Qwen 2.5** brain with the state-of-the-art, lightning-fast **Kokoro TTS** engine for localized, natural speech generation.
And yes, it possesses a highly sarcastic, energetic personality that strictly addresses you as "Boss."

**NOTE: Depending on the user's choice, they can modify the behaviour and name of the agent. To make these changes, user must visit lines 75-88 in agent.py and change the behaviour and name as per their wish in natural language.**

## ✨ Core Features
1. **Zero-RAM STT Architecture:** Utilizes the native Web Speech API in the browser for voice capture, leaving your machine's full RAM available for modeling.
2. **Fine-Tuned Persona Logic:** Driven by custom system parameters over `Ollama` ensuring strict structural obedience (no markdown, no emojis, tailored greeting strings).
3. **Parallel Core Processing:** Uses multi-threading to display an active terminal "thinking animation" while computing replies, stopping instantly the millisecond audio playback begins.
4. **Localized Audio Synthesis:** Backed by Kokoro TTS for pristine, near-human audio rendering without external cloud API dependencies.


## 🛠️ System Architecture

1. **Brain:** Ollama (Qwen 2.5)
2. **Voice Output (TTS):** Kokoro Python Framework (`sounddevice` + NumPy arrays)
3. **Voice Input (STT):** Browser Web Speech API
4. **Backend Pipeline:** Flask Web Server


## 🚀 Getting Started

### Prerequisites
1. Python 3.10 or higher.
2. [Ollama](https://ollama.com/) installed and running locally.
3. Atleast 8GB RAM.

### Installation

**NOTE: RUN THE BELOW COMMANDS IN EITHER GIT BASH, WINDOWS POWERSHELL, TERMINAL OR CMD PROMPT**

1. **Clone the repository:**
   ```bash 
   git clone https://github.com/YOUR_USERNAME/REPO_NAME.git
   cd REPO_NAME

2. **Install Python Dependencies:**
   ```bash
   pip install flask sounddevice kokoro numpy

3. **Pull the base model via Ollama:**
   ```bash
   ollama pull qwen2.5

4. **Model Weights Setup:**
   * Download and place your **kokoro-v1.0.onnx** and **voices-v1.0.bin** files directly in your project root directory. **(Note: These are ignored by Git due to file size constraints).**
   * Download **kokoro-v1.0.onnx** from https://github.com/taylorchu/kokoro-onnx/releases/tag/v0.2.0 [Download the file listed as kokoro.onnx and rename it as kokoro-v1.0.onnx to avoid future conflicts.]
   * Download **voices-v1.0.bin** from https://huggingface.co/hexgrad/Kokoro-82M/tree/main [From folder titled **voices**]

### Running the Agent

1. Launch your Flask backend server:
   ```bash
   python agent.py

2. Open your local browser interface (http://127.0.0.1:5000).
3. Allow microphone permissions, activate your agent, and start talking to PANDORA.

YOUR AGENT IS READY TO GO NOW!!!
