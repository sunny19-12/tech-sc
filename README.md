# PC AI Assistant (Sofia-style starter)

This project gives you a local **AI assistant for your PC** that can:
- Answer your questions with OpenAI.
- Run safe desktop actions (open apps/websites, type text, set volume).
- Work from a simple terminal interface.

## 1) Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export OPENAI_API_KEY="your_api_key_here"   # Windows PowerShell: $env:OPENAI_API_KEY="..."
```

## 2) Run

```bash
python pc_ai_assistant.py
```

## 3) Example usage

- Ask questions normally:
  - `How can I improve my interview skills?`
- Control your PC with slash commands:
  - `/open_website youtube.com`
  - `/open_app calculator`
  - `/set_volume 35`
  - `/type_text hello from my assistant`

## Available commands

- `/open_app <name>`: open an application
- `/open_website <url>`: open browser URL
- `/type_text <text>`: type text in current active window (needs `pyautogui`)
- `/set_volume <0-100>`: set volume (Linux/macOS in this starter)
- `/shell <cmd>`: run restricted shell command (`echo`, `date`, `pwd`, `whoami`, `ls`)
- `/help`
- `/quit`

## Important safety note

This starter intentionally uses a **restricted** action set. A full unrestricted "control my PC" agent can be dangerous.
If you want, I can extend this into a voice assistant (wake word + speech-to-text + text-to-speech) in the next step.
