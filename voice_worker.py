import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile
import os
import queue
import threading

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

STT_QUEUE = queue.Queue()
IS_RECORDING = False
AUDIO_DATA = []
SAMPLE_RATE = 16000
model = None
stream = None

def init_whisper():
    global model
    if not WHISPER_AVAILABLE:
        print("[VOICE] module faster-whisper non installé.")
        return
    try:
        print("[VOICE] Chargement du modèle Whisper (tiny)...")
        # tiny pour la rapidité
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("[VOICE] Modèle Whisper chargé.")
    except Exception as e:
        print(f"[VOICE] Erreur chargement Whisper: {e}")

threading.Thread(target=init_whisper, daemon=True).start()

def audio_callback(indata, frames, time, status):
    if IS_RECORDING:
        AUDIO_DATA.append(indata.copy())

def start_recording():
    global IS_RECORDING, AUDIO_DATA, stream
    if not IS_RECORDING:
        IS_RECORDING = True
        AUDIO_DATA = []
        try:
            stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=audio_callback)
            stream.start()
            print("[VOICE] Enregistrement démarré...")
        except Exception as e:
            print(f"[VOICE] Erreur accès micro: {e}")
            IS_RECORDING = False

def stop_recording_and_transcribe():
    global IS_RECORDING, stream
    if IS_RECORDING:
        IS_RECORDING = False
        try:
            stream.stop()
            stream.close()
            print("[VOICE] Enregistrement arrêté, transcription en cours...")
        except:
            pass

        if not AUDIO_DATA:
            return

        # Prepare audio as 1D numpy array of float32 for faster-whisper
        audio_np = np.concatenate(AUDIO_DATA, axis=0).flatten().astype(np.float32)

        if model:
            def transcribe_task():
                try:
                    # Pass numpy array directly, avoiding PyAV file loading issues
                    segments, info = model.transcribe(audio_np, beam_size=5, language="fr")
                    text = " ".join([segment.text for segment in segments])
                    if text.strip():
                        print(f"[VOICE] Entendu : {text.strip()}")
                        STT_QUEUE.put(text.strip())
                except Exception as e:
                    print(f"[VOICE] Erreur de transcription : {e}")
            threading.Thread(target=transcribe_task, daemon=True).start()
