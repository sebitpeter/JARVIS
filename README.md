# JARVIS Desktop Assistant

A small, local desktop chat app with Gemini-powered replies. It includes optional microphone dictation and optional text-to-speech. Chat history stays in memory and is cleared when the app closes.

## What is included

- PyQt6 desktop chat window
- Gemini API client using Python's standard library
- Optional microphone input (install the voice requirements)
- Optional local "Hey JARVIS" wake-word detection (install the wake-word requirements)
- Optional spoken replies using `pyttsx3`
- Unit tests for configuration and Gemini request handling
- No API key or `.env` file is included

## Requirements

- Python 3.10 or newer
- Internet access and your own Gemini API key for AI replies
- A microphone and operating-system microphone permission for dictation

## First run

### Windows

Double-click `run_windows.bat`. It creates a virtual environment and installs the base dependencies. The first run creates `.env` and exits so you can add your key.

### macOS or Linux

In a terminal opened in this folder, run:

```bash
bash run.sh
```

The script creates a virtual environment, installs the base dependencies, and creates `.env` on the first run. Add your own key to `.env`, then run the script again.

### Manual setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and replace `PASTE_YOUR_NEW_GEMINI_API_KEY_HERE` with a new Gemini API key. Then launch:

```bash
python main.py
```

The app window can open without a key, but Gemini replies need a valid key. If the configured model is unavailable to your account, change `GEMINI_MODEL` in `.env` to a model enabled for your Gemini API key.

## Optional features

### Microphone dictation

Install the optional packages:

```bash
python -m pip install -r requirements-voice.txt
```

Restart the app and choose **Dictate**. JARVIS records for the configured number of seconds (`VOICE_SECONDS`, default 6), transcribes the recording, and places the result in the message box. Review it and press **Send**.

Dictation uses your microphone locally for recording, then sends the recorded audio to Google's speech-recognition service for transcription. It requires an internet connection and may require microphone permissions or an OS audio backend.

### Hands-free wake word

Install both the microphone and wake-word packages:

```bash
python -m pip install -r requirements-voice.txt
# JARVIS uses ONNX inference; install openWakeWord without its optional TFLite extra.
python -m pip install --no-deps "openwakeword>=0.6.0,<0.7"
python -m pip install -r requirements-wake.txt
```

Check **Wake word: off** in the app to enable it; the label changes to **Wake word: on**. The microphone then remains active and the Hey JARVIS phrase is detected locally by openWakeWord. On first activation, openWakeWord downloads its detector model files; after the phrase is recognized, pause briefly, then say your command. JARVIS records for `VOICE_SECONDS`, transcribes the command online, and sends the transcription to Gemini. Uncheck the option at any time to stop continuous listening. You can also select **Read replies aloud** for spoken answers.

The wake-word model runs locally, but the command recording is sent to Google's speech-recognition service after activation. Wake-word detection is English-oriented and can miss phrases in noisy rooms or with some pronunciations.

### Spoken replies

Select **Read replies aloud** in the app. Speech is generated locally with `pyttsx3`; available voices depend on your operating system. If speech output is unavailable, text chat continues to work.

## Configuration

| Setting | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | empty | Your private Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `ASSISTANT_NAME` | `JARVIS` | Name shown in the window |
| `LOG_LEVEL` | `INFO` | Python log level |
| `REQUEST_TIMEOUT` | `45` | Gemini request timeout in seconds (1–180) |
| `VOICE_SECONDS` | `6` | Dictation recording length in seconds (1–30) |

Never commit `.env` or share it publicly. If a key was included in a file you uploaded or shared, revoke it and create a new one before using this app.

## Tests

```bash
python -m pytest
```

The tests mock the Gemini network request; running them does not use your API key or make an internet request.

## Troubleshooting

- **Gemini rejected the API key:** create a new key, confirm it is enabled for the Gemini API, and update `.env`.
- **Model not found:** set `GEMINI_MODEL` to a model available to your account.
- **Microphone setup needed:** install `requirements-voice.txt`, allow microphone access in your OS settings, and check that a recording device is available.
- **No speech output:** install an OS-supported speech engine/voice, or turn off **Read replies aloud**.