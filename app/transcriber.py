from __future__ import annotations
import threading
from typing import Callable
import numpy as np
import whisper
import tqdm as tqdm_module
import sounddevice as sd
from scipy.io.wavfile import write as write_wav
from pathlib import Path
from datetime import datetime
from app.settings import Settings


RECORD_DIR = Path.home() / ".whisper_flet_transcriber" / "recordings"
RECORD_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────
# Whisper 進捗 Hook
# ─────────────────────────────────────────

class FletProgressBar(tqdm_module.tqdm):
    """進捗をUIコールバックで返す tqdm ラッパー"""

    def __init__(self, *args, ui_callback: Callable[[float], None] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_callback = ui_callback

    def update(self, n=1):
        super().update(n)
        if self.total and self.ui_callback:
            ratio = self.n / self.total
            self.ui_callback(ratio)


def install_progress_hook(ui_callback: Callable[[float], None]) -> None:
    """辺屠 tqdm をパッチして Whisper 内部の進捗を横取りする"""
    import whisper.transcribe as _wt
    # whisper.transcribe モジュール内の tqdm クラスを直接差し替える
    try:
        _wt.tqdm.tqdm = lambda *a, **k: FletProgressBar(*a, ui_callback=ui_callback, **k)
    except AttributeError:
        # tqdm モジュール構造が違うバージョン向けフォールバック
        try:
            _wt.tqdm = lambda *a, **k: FletProgressBar(*a, ui_callback=ui_callback, **k)
        except Exception:
            pass  # 進捗表示はスキップ、文字起こしは続行


# ─────────────────────────────────────────
# 録音クラス
# ─────────────────────────────────────────

class Recorder:
    """マイク録音を管理するクラス（start/stop）"""

    def __init__(self, samplerate: int = 16000, channels: int = 1) -> None:
        self.samplerate = samplerate
        self.channels = channels
        self._recording = False
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        if self._recording:
            return
        self._recording = True
        self._frames = []

        def callback(indata, frames, time, status):
            if self._recording:
                self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            callback=callback,
        )
        self._stream.start()

    def stop_and_save(self) -> str:
        """録音を停止して WAV ファイルに保存し、ファイルパスを返す"""
        if not self._recording:
            return ""

        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            return ""

        audio = np.concatenate(self._frames, axis=0)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = RECORD_DIR / f"record-{timestamp}.wav"
        write_wav(path, self.samplerate, audio)
        return str(path)


# ─────────────────────────────────────────
# 文字起こしクラス
# ─────────────────────────────────────────

class Transcriber:
    """Whisperモデルの管理と文字起こし処理を担当するクラス"""

    def __init__(self) -> None:
        self._model: whisper.Whisper | None = None
        self._loaded_model_name: str = ""

    def _load_model(self, model_name: str) -> None:
        if self._loaded_model_name != model_name or self._model is None:
            self._model = whisper.load_model(model_name)
            self._loaded_model_name = model_name

    def transcribe(
        self,
        file_path: str,
        settings: Settings,
        on_done: Callable[[str], None],
        on_error: Callable[[str], None],
        on_progress: Callable[[float], None] | None = None,
    ) -> None:
        """バックグラウンドスレッドで文字起こしを実行する"""

        def run() -> None:
            try:
                if on_progress:
                    install_progress_hook(on_progress)

                self._load_model(settings.model_name)
                assert self._model is not None

                result = self._model.transcribe(
                    file_path,
                    language=settings.language(),
                    temperature=settings.temperature,
                    task="translate" if settings.translate else "transcribe",
                    initial_prompt=settings.initial_prompt or None,
                )
                on_done(result["text"])
            except Exception as e:
                on_error(str(e))
            finally:
                if on_progress:
                    on_progress(1.0)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
