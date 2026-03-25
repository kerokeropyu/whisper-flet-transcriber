# Whisper Flet Transcriber

音声ファイルを文字起こしするデスクトップGUIアプリです。
OpenAI の [Whisper](https://github.com/openai/whisper) をローカルで実行し、[Flet](https://flet.dev) でモダンな UI を提供します。

---

## 必要環境

- Python 3.10 以上
- [uv](https://docs.astral.sh/uv/)（仮想環境・パッケージ管理）
- [ffmpeg](https://ffmpeg.org/)（音声デコードに必要）

### ffmpeg のインストール

| OS | コマンド |
|---|---|
| macOS | `brew install ffmpeg` |
| Windows | `winget install ffmpeg` または [公式サイト](https://ffmpeg.org/download.html) からインストール |
| Ubuntu | `sudo apt install ffmpeg` |

---

## セットアップ

```bash
git clone https://github.com/kerokeropyu/whisper-flet-transcriber.git
cd whisper-flet-transcriber

# 依存インストール（uv）
uv sync

# アプリ起動
uv run python -m app.main
```

---

## 機能一覧

- 音声ファイルのアップロード（mp3 / wav / m4a / ogg / flac / webm）
- マイクからリアルタイム録音（赤丸ボタンで開始・停止）
- 録音ファイルは `~/.whisper_flet_transcriber/recordings/` に自動保存
- 文字起こし進捗をプログレスバーで表示（割合表示）
- 文字起こし結果の画面表示
- ワンクリックでクリップボードコピー
- テキストファイルとして保存
- 各種 Whisper 設定を GUI で操作・自動保存

---

## 設定

設定は `~/.whisper_flet_transcriber/config.json` に自動保存されます。

| 設定項目 | 説明 |
|---|---|
| モデルサイズ | tiny / base / small / medium / large |
| 言語 | 日本語固定 or 自動検出 |
| 温度 | 出力の多様性（0.0 が最も安定）|
| 翻訳モード | 英語に翻訳して出力 |
| 初期プロンプト | 話者名・専門用語のヒントを与える |

---

## ライセンス

MIT
