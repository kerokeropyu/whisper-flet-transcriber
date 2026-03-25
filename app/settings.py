from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path

CONFIG_DIR = Path.home() / ".whisper_flet_transcriber"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "model_name": "base",
    "language_mode": "ja",
    "temperature": 0.0,
    "translate": False,
    "initial_prompt": "",
}


@dataclass
class Settings:
    model_name: str = "base"
    language_mode: str = "ja"   # "ja" or "auto"
    temperature: float = 0.0
    translate: bool = False
    initial_prompt: str = ""

    def language(self) -> str | None:
        return "ja" if self.language_mode == "ja" else None


def load_settings() -> Settings:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            merged = {**DEFAULTS, **data}
            return Settings(**{k: merged[k] for k in DEFAULTS})
        except Exception:
            pass
    return Settings()


def save_settings(settings: Settings) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
