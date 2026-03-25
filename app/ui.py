from __future__ import annotations
from pathlib import Path
import flet as ft
from app.settings import Settings, load_settings, save_settings
from app.transcriber import Transcriber, Recorder

MODELS = ["tiny", "base", "small", "medium", "large"]


class TranscriberApp:
    """FletアプリのUI構成と状態管理を担当するクラス"""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.settings = load_settings()
        self.transcriber = Transcriber()
        self.recorder = Recorder()
        self._selected_file: str = ""
        self._build()

    # ─────────────────────────────────────────
    # UI構築
    # ─────────────────────────────────────────

    def _build(self) -> None:
        p = self.page
        p.title = "Whisper 文字起こし"
        p.theme_mode = ft.ThemeMode.DARK
        p.window_width = 860
        p.window_height = 740
        p.padding = 20

        # 設定パネル
        self.model_dd = ft.Dropdown(
            label="モデルサイズ",
            options=[ft.dropdown.Option(m) for m in MODELS],
            value=self.settings.model_name,
            width=180,
            on_change=self._on_model_change,
        )

        self.lang_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="ja", label="日本語固定"),
                ft.Radio(value="auto", label="自動検出"),
            ]),
            value=self.settings.language_mode,
            on_change=self._on_lang_change,
        )

        self.temp_label = ft.Text(f"温度: {self.settings.temperature:.1f}", size=13)
        self.temp_slider = ft.Slider(
            min=0.0, max=1.0, divisions=10,
            label="{value}",
            value=self.settings.temperature,
            width=200,
            on_change=self._on_temp_change,
        )

        self.translate_switch = ft.Switch(
            label="英語に翻訳して出力",
            value=self.settings.translate,
            on_change=self._on_translate_change,
        )

        self.prompt_field = ft.TextField(
            label="初期プロンプト（話者名・専門用語など）",
            value=self.settings.initial_prompt,
            multiline=False,
            expand=True,
            on_blur=self._on_prompt_change,
        )

        settings_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("設定", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        self.model_dd,
                        ft.Column([
                            ft.Text("言語", size=13),
                            self.lang_radio,
                        ]),
                        ft.Column([
                            self.temp_label,
                            self.temp_slider,
                        ]),
                        self.translate_switch,
                    ], wrap=True, spacing=20),
                    self.prompt_field,
                ], spacing=12),
                padding=16,
            )
        )

        # ファイル選択
        self.file_label = ft.Text("ファイル未選択", size=13, color=ft.colors.GREY_400)
        self.file_picker = ft.FilePicker(on_result=self._on_file_result)
        p.overlay.append(self.file_picker)

        pick_btn = ft.ElevatedButton(
            "音声ファイルを選択",
            icon=ft.icons.UPLOAD_FILE,
            on_click=lambda _: self.file_picker.pick_files(
                allowed_extensions=["mp3", "wav", "m4a", "ogg", "flac", "webm"],
            ),
        )

        # 録音ボタン
        self.record_btn = ft.IconButton(
            icon=ft.icons.FIBER_MANUAL_RECORD,
            icon_color=ft.colors.RED_400,
            icon_size=36,
            tooltip="録音開始",
            on_click=self._on_record_toggle,
        )

        # 文字起こし開始ボタン
        self.transcribe_btn = ft.FilledButton(
            "文字起こし開始",
            icon=ft.icons.PLAY_CIRCLE,
            on_click=self._on_transcribe,
            disabled=True,
        )

        # ステータス / プログレス
        self.status_text = ft.Text("待機中", size=12, color=ft.colors.GREY_500)
        self.progress = ft.ProgressBar(
            width=800,
            value=0.0,
            visible=False,
        )
        self.progress_label = ft.Text("0%", size=12, visible=False)

        # 結果表示
        self.result_field = ft.TextField(
            multiline=True,
            read_only=True,
            min_lines=12,
            max_lines=20,
            expand=True,
            hint_text="文字起こし結果がここに表示されます",
            text_size=14,
        )

        copy_btn = ft.IconButton(
            icon=ft.icons.COPY_ALL,
            tooltip="テキストをコピー",
            on_click=self._on_copy,
        )

        self.save_picker = ft.FilePicker(on_result=self._on_save_result)
        p.overlay.append(self.save_picker)

        save_btn = ft.IconButton(
            icon=ft.icons.SAVE_ALT,
            tooltip="テキストを保存",
            on_click=self._on_save,
        )

        # レイアウト組み立て
        p.add(
            settings_card,
            ft.Divider(height=10),
            ft.Row([pick_btn, self.record_btn, self.file_label], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([self.transcribe_btn, self.status_text], spacing=12),
            ft.Row([self.progress, self.progress_label], spacing=8),
            ft.Divider(height=10),
            ft.Row([
                ft.Text("文字起こし結果", size=15, weight=ft.FontWeight.BOLD),
                copy_btn,
                save_btn,
            ]),
            self.result_field,
        )
        p.update()

    # ─────────────────────────────────────────
    # イベントハンドラ - 設定
    # ─────────────────────────────────────────

    def _on_model_change(self, e: ft.ControlEvent) -> None:
        self.settings.model_name = e.control.value
        save_settings(self.settings)

    def _on_lang_change(self, e: ft.ControlEvent) -> None:
        self.settings.language_mode = e.control.value
        save_settings(self.settings)

    def _on_temp_change(self, e: ft.ControlEvent) -> None:
        self.settings.temperature = round(float(e.control.value), 1)
        self.temp_label.value = f"温度: {self.settings.temperature:.1f}"
        self.temp_label.update()
        save_settings(self.settings)

    def _on_translate_change(self, e: ft.ControlEvent) -> None:
        self.settings.translate = e.control.value
        save_settings(self.settings)

    def _on_prompt_change(self, e: ft.ControlEvent) -> None:
        self.settings.initial_prompt = e.control.value
        save_settings(self.settings)

    # ─────────────────────────────────────────
    # イベントハンドラ - ファイル選択
    # ─────────────────────────────────────────

    def _on_file_result(self, e: ft.FilePickerResultEvent) -> None:
        if e.files:
            self._selected_file = e.files[0].path
            self.file_label.value = e.files[0].name
            self.transcribe_btn.disabled = False
        else:
            self._selected_file = ""
            self.file_label.value = "ファイル未選択"
            self.transcribe_btn.disabled = True
        self.file_label.update()
        self.transcribe_btn.update()

    # ─────────────────────────────────────────
    # イベントハンドラ - 録音
    # ─────────────────────────────────────────

    def _on_record_toggle(self, _: ft.ControlEvent) -> None:
        if not self.recorder.is_recording:
            try:
                self.recorder.start()
                self.record_btn.icon = ft.icons.STOP_CIRCLE
                self.record_btn.icon_color = ft.colors.RED_700
                self.record_btn.tooltip = "録音停止"
                self.status_text.value = "🎙 録音中… もう一度押すと停止して文字起こしします"
            except Exception as e:
                self.status_text.value = f"❌ 録音開始エラー: {e}"
            self.status_text.update()
            self.record_btn.update()
        else:
            try:
                path = self.recorder.stop_and_save()
                self.record_btn.icon = ft.icons.FIBER_MANUAL_RECORD
                self.record_btn.icon_color = ft.colors.RED_400
                self.record_btn.tooltip = "録音開始"
                self.record_btn.update()

                if not path:
                    self.status_text.value = "録音データがありません"
                    self.status_text.update()
                    return

                self._selected_file = path
                self.file_label.value = f"録音ファイル: {Path(path).name}"
                self.status_text.value = "録音完了。文字起こしを開始します…"
                self.transcribe_btn.disabled = True
                self._start_progress()
                self.result_field.value = ""
                self.page.update()

                self.transcriber.transcribe(
                    self._selected_file,
                    self.settings,
                    on_done=self._on_done,
                    on_error=self._on_error,
                    on_progress=self._update_progress,
                )
            except Exception as e:
                self.status_text.value = f"❌ 録音停止エラー: {e}"
                self.status_text.update()

    # ─────────────────────────────────────────
    # イベントハンドラ - 文字起こし
    # ─────────────────────────────────────────

    def _on_transcribe(self, _: ft.ControlEvent) -> None:
        if not self._selected_file:
            return
        self.transcribe_btn.disabled = True
        self.status_text.value = "変換中…（モデルにより数分かかる場合があります）"
        self._start_progress()
        self.result_field.value = ""
        self.page.update()

        self.transcriber.transcribe(
            self._selected_file,
            self.settings,
            on_done=self._on_done,
            on_error=self._on_error,
            on_progress=self._update_progress,
        )

    def _start_progress(self) -> None:
        self.progress.value = 0.0
        self.progress.visible = True
        self.progress_label.value = "0%"
        self.progress_label.visible = True

    def _update_progress(self, ratio: float) -> None:
        self.progress.value = min(max(ratio, 0.0), 1.0)
        self.progress_label.value = f"{int(ratio * 100)}%"
        self.progress.update()
        self.progress_label.update()

    def _on_done(self, text: str) -> None:
        self.result_field.value = text
        self.status_text.value = "✅ 完了"
        self.progress.value = 1.0
        self.progress.visible = False
        self.progress_label.visible = False
        self.transcribe_btn.disabled = False
        self.page.update()

    def _on_error(self, msg: str) -> None:
        self.status_text.value = f"❌ エラー: {msg}"
        self.progress.visible = False
        self.progress_label.visible = False
        self.transcribe_btn.disabled = False
        self.page.update()

    # ─────────────────────────────────────────
    # イベントハンドラ - コピー / 保存
    # ─────────────────────────────────────────

    def _on_copy(self, _: ft.ControlEvent) -> None:
        if self.result_field.value:
            self.page.set_clipboard(self.result_field.value)
            self.status_text.value = "📋 クリップボードにコピーしました"
            self.status_text.update()

    def _on_save(self, _: ft.ControlEvent) -> None:
        self.save_picker.save_file(
            file_name="transcription.txt",
            allowed_extensions=["txt"],
        )

    def _on_save_result(self, e: ft.FilePickerResultEvent) -> None:
        if e.path and self.result_field.value:
            try:
                with open(e.path, "w", encoding="utf-8") as f:
                    f.write(self.result_field.value)
                self.status_text.value = f"💾 保存しました: {e.path}"
            except Exception as ex:
                self.status_text.value = f"❌ 保存失敗: {ex}"
            self.status_text.update()
