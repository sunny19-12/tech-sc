#!/usr/bin/env python3
"""
PC AI Assistant

A local assistant that can:
1) Answer your questions using OpenAI responses API
2) Control your PC for a safe set of actions (open apps/sites, type text, volume)
3) Optionally speak answers out loud

Usage:
  export OPENAI_API_KEY="..."
  python pc_ai_assistant.py
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from typing import Callable, Dict, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore


SYSTEM_PROMPT = """You are a helpful desktop assistant.
- Be concise and practical.
- If the user asks for dangerous, illegal, or privacy-invasive actions, refuse and offer safe alternatives.
- If the user asks you to run a PC action, describe what you'll do first.
"""


@dataclass
class ActionResult:
    ok: bool
    message: str


class PCAssistant:
    def __init__(self) -> None:
        self.client = None
        if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI()

        self.actions: Dict[str, Callable[[str], ActionResult]] = {
            "open_app": self.open_app,
            "open_website": self.open_website,
            "type_text": self.type_text,
            "set_volume": self.set_volume,
            "shell": self.safe_shell,
        }

    def ask_ai(self, user_text: str) -> str:
        if self.client is None:
            return (
                "I can control local commands, but AI answers are disabled. "
                "Set OPENAI_API_KEY and install `openai` package to enable question answering."
            )

        response = self.client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            temperature=0.4,
        )
        return response.output_text.strip()

    def parse_action(self, text: str) -> Optional[tuple[str, str]]:
        # slash format: /action argument
        if not text.startswith("/"):
            return None

        parts = text[1:].strip().split(" ", 1)
        action = parts[0].strip().lower()
        argument = parts[1].strip() if len(parts) > 1 else ""
        return action, argument

    def run(self, user_input: str) -> str:
        parsed = self.parse_action(user_input)
        if parsed is None:
            return self.ask_ai(user_input)

        action, arg = parsed
        fn = self.actions.get(action)
        if fn is None:
            return f"Unknown action: {action}. Try one of: {', '.join(self.actions.keys())}"

        result = fn(arg)
        status = "✅" if result.ok else "❌"
        return f"{status} {result.message}"

    # -------- Safe PC actions --------

    def open_app(self, app_name: str) -> ActionResult:
        if not app_name:
            return ActionResult(False, "Usage: /open_app <application>")

        if sys.platform.startswith("linux"):
            cmd = ["bash", "-lc", f"nohup {shlex.quote(app_name)} >/dev/null 2>&1 &"]
        elif sys.platform == "darwin":
            cmd = ["open", "-a", app_name]
        elif sys.platform.startswith("win"):
            cmd = ["cmd", "/c", "start", "", app_name]
        else:
            return ActionResult(False, f"Unsupported OS: {sys.platform}")

        try:
            subprocess.Popen(cmd)
            return ActionResult(True, f"Opening app: {app_name}")
        except Exception as exc:
            return ActionResult(False, f"Failed to open app: {exc}")

    def open_website(self, url: str) -> ActionResult:
        if not url:
            return ActionResult(False, "Usage: /open_website <url>")

        if not re.match(r"^https?://", url):
            url = f"https://{url}"

        webbrowser.open(url)
        return ActionResult(True, f"Opened website: {url}")

    def type_text(self, text: str) -> ActionResult:
        if not text:
            return ActionResult(False, "Usage: /type_text <text>")

        try:
            import pyautogui  # lazy import

            pyautogui.write(text, interval=0.02)
            return ActionResult(True, "Typed text into active window")
        except ImportError:
            return ActionResult(False, "Install `pyautogui` to enable /type_text")
        except Exception as exc:
            return ActionResult(False, f"Typing failed: {exc}")

    def set_volume(self, value: str) -> ActionResult:
        try:
            percent = int(value)
            if not 0 <= percent <= 100:
                return ActionResult(False, "Volume must be 0-100")
        except ValueError:
            return ActionResult(False, "Usage: /set_volume <0-100>")

        if sys.platform.startswith("linux"):
            cmd = ["bash", "-lc", f"pactl set-sink-volume @DEFAULT_SINK@ {percent}%"]
        elif sys.platform == "darwin":
            cmd = ["osascript", "-e", f"set volume output volume {percent}"]
        elif sys.platform.startswith("win"):
            return ActionResult(False, "Windows volume control not implemented in this starter.")
        else:
            return ActionResult(False, f"Unsupported OS: {sys.platform}")

        try:
            subprocess.run(cmd, check=True)
            return ActionResult(True, f"Volume set to {percent}%")
        except subprocess.CalledProcessError as exc:
            return ActionResult(False, f"Failed to set volume: {exc}")

    def safe_shell(self, command: str) -> ActionResult:
        """Run very restricted shell commands for power users."""
        allowed_prefixes = (
            "echo ",
            "date",
            "pwd",
            "whoami",
            "ls",
        )
        if not command:
            return ActionResult(False, "Usage: /shell <command>")

        if not command.startswith(allowed_prefixes):
            return ActionResult(
                False,
                "Blocked command. Allowed prefixes: echo, date, pwd, whoami, ls",
            )

        try:
            completed = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            out = (completed.stdout or completed.stderr).strip() or "(no output)"
            return ActionResult(True, f"Shell output:\n{out}")
        except Exception as exc:
            return ActionResult(False, f"Shell failed: {exc}")


def print_help() -> None:
    print(
        """
Commands:
  /open_app <name>       Open an application (e.g. /open_app calculator)
  /open_website <url>    Open URL in browser (e.g. /open_website openai.com)
  /type_text <text>      Type into active window (needs pyautogui)
  /set_volume <0-100>    Set system volume (Linux/macOS)
  /shell <cmd>           Run a restricted shell command
  /help                  Show this help
  /quit                  Exit assistant

Anything without /command is sent to AI for Q&A.
"""
    )


def main() -> None:
    assistant = PCAssistant()
    print("🤖 PC AI Assistant is running. Type /help for commands.")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            print("Goodbye!")
            break
        if user_input == "/help":
            print_help()
            continue

        answer = assistant.run(user_input)
        print(f"Assistant: {answer}")


if __name__ == "__main__":
    main()
