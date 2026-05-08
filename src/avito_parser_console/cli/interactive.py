from __future__ import annotations

import asyncio
from typing import Any

import questionary


def _fallback_text(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        raw = input(f"{prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        return default
    return raw if raw else default


def ask_text(prompt: str, default: str = "") -> str:
    if _inside_running_event_loop():
        return _fallback_text(prompt, default=default)
    try:
        return questionary.text(prompt, default=default).ask() or default
    except Exception:
        return _fallback_text(prompt, default=default)


def ask_confirm(prompt: str, default: bool = False) -> bool:
    if _inside_running_event_loop():
        default_marker = "Y/n" if default else "y/N"
        try:
            raw = input(f"{prompt} ({default_marker}): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return default
        if not raw:
            return default
        return raw in {"y", "yes", "1", "true", "д", "да"}
    try:
        ans = questionary.confirm(prompt, default=default).ask()
        return bool(default if ans is None else ans)
    except Exception:
        default_marker = "Y/n" if default else "y/N"
        try:
            raw = input(f"{prompt} ({default_marker}): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return default
        if not raw:
            return default
        return raw in {"y", "yes", "1", "true", "д", "да"}


def ask_select(prompt: str, choices: list[str], default: str | None = None) -> str:
    if _inside_running_event_loop():
        print(prompt)
        for i, ch in enumerate(choices, start=1):
            print(f"{i}. {ch}")
        while True:
            try:
                raw = input(f"Выберите [1-{len(choices)}]: ").strip()
            except (EOFError, KeyboardInterrupt):
                return ""
            try:
                idx = int(raw)
                if 1 <= idx <= len(choices):
                    return choices[idx - 1]
            except ValueError:
                pass
            print("Некорректный выбор, повторите.")
    try:
        return questionary.select(prompt, choices=choices, default=default).ask() or (default or choices[0])
    except Exception:
        print(prompt)
        for i, ch in enumerate(choices, start=1):
            print(f"{i}. {ch}")
        while True:
            try:
                raw = input(f"Выберите [1-{len(choices)}]: ").strip()
            except (EOFError, KeyboardInterrupt):
                return ""
            try:
                idx = int(raw)
                if 1 <= idx <= len(choices):
                    return choices[idx - 1]
            except ValueError:
                pass
            print("Некорректный выбор, повторите.")


def ask_checkbox(prompt: str, choices: list[str]) -> list[str]:
    if _inside_running_event_loop():
        print(prompt)
        for i, ch in enumerate(choices, start=1):
            print(f"{i}. {ch}")
        try:
            raw = input("Введите номера через запятую (или пусто): ").strip()
        except (EOFError, KeyboardInterrupt):
            return []
        if not raw:
            return []
        selected: list[str] = []
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            try:
                idx = int(token)
                if 1 <= idx <= len(choices):
                    selected.append(choices[idx - 1])
            except ValueError:
                continue
        seen: set[str] = set()
        out: list[str] = []
        for item in selected:
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out
    try:
        return questionary.checkbox(prompt, choices=choices).ask() or []
    except Exception:
        print(prompt)
        for i, ch in enumerate(choices, start=1):
            print(f"{i}. {ch}")
        try:
            raw = input("Введите номера через запятую (или пусто): ").strip()
        except (EOFError, KeyboardInterrupt):
            return []
        if not raw:
            return []
        selected: list[str] = []
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            try:
                idx = int(token)
                if 1 <= idx <= len(choices):
                    selected.append(choices[idx - 1])
            except ValueError:
                continue
        # deduplicate while preserving order
        seen: set[str] = set()
        out: list[str] = []
        for item in selected:
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out


def _inside_running_event_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False
