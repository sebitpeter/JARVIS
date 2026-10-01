"""Optional microphone capture and online speech-to-text."""

from __future__ import annotations

from queue import Empty, Queue
from threading import Event
from typing import Any


def is_wake_word_detected(predictions: dict[str, Any], threshold: float = 0.5) -> bool:
    """Return whether any openWakeWord model score meets the activation threshold."""
    for score in predictions.values():
        try:
            maximum = score.max() if hasattr(score, "max") else max(score) if isinstance(
                score, (list, tuple)
            ) else score
            if float(maximum) >= threshold:
                return True
        except (TypeError, ValueError):
            continue
    return False


def wait_for_jarvis_wake_word(stop_event: Event, threshold: float = 0.5) -> bool:
    """Listen locally for the Hey Jarvis phrase; return on detection or cancellation."""
    try:
        import sounddevice as sd
        import openwakeword
        from openwakeword.model import Model
        from openwakeword.utils import download_models
    except ImportError as exc:
        raise RuntimeError(
            "Wake-word support is not installed. Install requirements-voice.txt and "
            "requirements-wake.txt, then restart JARVIS."
        ) from exc

    # openWakeWord publishes its model and feature-extraction files separately
    # from the Python package. This downloads only the Hey Jarvis model on first use.
    try:
        download_models(model_names=["hey_jarvis_v0.1"])
        model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
    except Exception as exc:
        raise RuntimeError(
            "Could not load the Hey JARVIS detector. Check your internet connection "
            "for its first-time model download, then try again."
        ) from exc

    sample_rate = 16_000
    frame_samples = 1_280  # 80 ms at 16 kHz
    audio_queue: Queue[Any] = Queue(maxsize=12)

    def audio_callback(indata, frames, timing, status) -> None:
        try:
            audio_frame = indata.copy().reshape(-1)
            if audio_queue.full():
                try:
                    audio_queue.get_nowait()
                except Empty:
                    pass
            audio_queue.put_nowait(audio_frame)
        except Exception:
            # Never let a device callback exception terminate the audio stream.
            return

    try:
        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            blocksize=frame_samples,
            dtype="int16",
            callback=audio_callback,
        ):
            while not stop_event.is_set():
                try:
                    audio_frame = audio_queue.get(timeout=0.2)
                except Empty:
                    continue
                if is_wake_word_detected(model.predict(audio_frame), threshold):
                    return True
    except Exception as exc:
        raise RuntimeError(
            "Could not listen for the wake word. Check microphone access and audio-device "
            "settings, then try again."
        ) from exc
    return False


def transcribe_once(seconds: int) -> str:
    """Record a short clip with sounddevice and transcribe it with Google Web Speech."""
    try:
        import sounddevice as sd
        import speech_recognition as sr
    except ImportError as exc:
        raise RuntimeError(
            "Microphone support is not installed. Install requirements-voice.txt "
            "and restart JARVIS."
        ) from exc

    recognizer = sr.Recognizer()
    sample_rate = 16_000
    try:
        recording = sd.rec(
            int(seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            blocking=True,
        )
    except Exception as exc:
        raise RuntimeError(
            "Could not access a microphone. Check your device and operating-system permissions."
        ) from exc

    pcm_audio = recording.tobytes()
    if not pcm_audio:
        raise RuntimeError("The microphone did not capture any audio.")
    audio = sr.AudioData(pcm_audio, sample_rate, 2)
    try:
        transcript = recognizer.recognize_google(audio)
    except sr.UnknownValueError as exc:
        raise RuntimeError("I couldn't make out that recording. Try again in a quieter place.") from exc
    except sr.RequestError as exc:
        raise RuntimeError(
            "Speech recognition is unavailable. Check your internet connection and try again."
        ) from exc
    if not transcript.strip():
        raise RuntimeError("No speech was detected. Try recording again.")
    return transcript.strip()