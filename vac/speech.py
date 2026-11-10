"""Device speech: text-to-speech (the phone's own voices, free and offline) and microphone recording.

Android uses the platform TextToSpeech and MediaRecorder through pyjnius. On a desktop, for
development, speech falls back to Windows SAPI and recording to the optional `sounddevice` package.
"""
import os
import subprocess
import sys
import threading
import time
import wave

from kivy.utils import platform

ANDROID = platform == "android"


class Unavailable(Exception):
    pass


# ----------------------------------------------------------------------------- text to speech
class Speaker:
    def __init__(self):
        self._tts = None
        self._proc = None
        self.rate = 0.9
        if ANDROID:
            from jnius import autoclass
            self._Locale = autoclass("java.util.Locale")
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            self._tts = autoclass("android.speech.tts.TextToSpeech")(activity, None)

    def say(self, text, locale="en-GB", slow=False):
        """Speak text in a locale such as 'ja-JP'. Returns False when no voice is available."""
        text = (text or "").strip()
        if not text:
            return False
        rate = self.rate * (0.75 if slow else 1.0)
        if ANDROID:
            lang, _, country = locale.partition("-")
            self._tts.setLanguage(self._Locale(lang, country))
            self._tts.setSpeechRate(rate)
            self._tts.speak(text, 0, None, "vac")  # 0 = QUEUE_FLUSH
            return True
        if sys.platform == "win32":
            self.stop()
            script = (
                "[Console]::InputEncoding = [Text.Encoding]::UTF8; "
                "Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$v = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like '%s*' } | "
                "Select-Object -First 1; if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }; $s.Rate = %d; "
                "$s.Speak([Console]::In.ReadToEnd())" % (locale.split("-")[0], int((rate - 1) * 6)))
            try:
                self._proc = subprocess.Popen(["powershell", "-NoProfile", "-Command", script], stdin=subprocess.PIPE,
                                              creationflags=0x08000000)  # no console window
                self._proc.stdin.write(text.encode("utf-8"))
                self._proc.stdin.close()
                return True
            except OSError:
                return False
        return False

    def stop(self):
        if ANDROID and self._tts:
            self._tts.stop()
        elif self._proc and self._proc.poll() is None:
            self._proc.kill()


# ----------------------------------------------------------------------------- microphone
class Recorder:
    """start() ... stop() -> (path, seconds). Records m4a on Android, wav on desktop."""

    def __init__(self, folder):
        self.folder = folder
        self.recording = False
        self._t0 = 0
        self._rec = None
        self._path = None
        self._frames = []
        self._stream = None

    def start(self):
        if self.recording:
            return
        self._t0 = time.time()
        if ANDROID:
            from jnius import autoclass
            self._path = os.path.join(self.folder, "vac_voice.m4a")
            rec = autoclass("android.media.MediaRecorder")()
            rec.setAudioSource(1)        # MIC
            rec.setOutputFormat(2)       # MPEG_4
            rec.setAudioEncoder(3)       # AAC
            rec.setAudioSamplingRate(16000)
            rec.setAudioChannels(1)
            rec.setOutputFile(self._path)
            rec.prepare()
            rec.start()
            self._rec = rec
        else:
            try:
                import sounddevice as sd
            except Exception as e:
                raise Unavailable("Microphone recording runs on the phone build. On desktop, install the "
                                  "'sounddevice' package or type your answer.") from e
            self._path = os.path.join(self.folder, "vac_voice.wav")
            self._frames = []
            try:
                self._stream = sd.RawInputStream(samplerate=16000, channels=1, dtype="int16",
                                                 callback=lambda data, *_: self._frames.append(bytes(data)))
                self._stream.start()
            except Exception as e:
                raise Unavailable("No microphone found: %s" % e) from e
        self.recording = True

    def stop(self):
        if not self.recording:
            return None, 0
        self.recording = False
        seconds = time.time() - self._t0
        if ANDROID:
            try:
                self._rec.stop()
            finally:
                self._rec.release()
                self._rec = None
        else:
            self._stream.stop()
            self._stream.close()
            with wave.open(self._path, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16000)
                w.writeframes(b"".join(self._frames))
        return self._path, seconds


def ask_permissions(done=None):
    """Request microphone and camera access on Android; a no-op elsewhere."""
    if not ANDROID:
        if done:
            done(True)
        return
    from android.permissions import Permission, request_permissions

    def cb(_perms, grants):
        if done:
            from kivy.clock import Clock
            Clock.schedule_once(lambda *_: done(all(grants)), 0)

    request_permissions([Permission.RECORD_AUDIO, Permission.CAMERA], cb)


def in_thread(fn):
    threading.Thread(target=fn, daemon=True).start()
