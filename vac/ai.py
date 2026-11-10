"""AI access: open-weight models served by Groq's free tier.

Chat     openai/gpt-oss-120b (Apache-2.0 weights), falling back to gpt-oss-20b, then Qwen
Speech   whisper-large-v3-turbo (MIT) for speech-to-text
Vision   qwen/qwen3.8-27b for reading handwriting and naming objects from the camera

Each chat model has its own daily token allowance on the free plan, so when one runs out or is
rate-limited the client moves to the next. Usage is recorded so the app can show what is left.
"""
import base64
import json
import os
import re
import threading

import requests
from kivy.clock import Clock

BASE = "https://api.groq.com/openai/v1"
CHAT_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
VISION_MODEL = "qwen/qwen3.8-27b"
STT_MODEL = "whisper-large-v3-turbo"

# Free-plan allowances published at console.groq.com/docs/rate-limits (November 2026).
TOKENS_PER_DAY = 200_000          # per chat model
AUDIO_SECONDS_PER_DAY = 28_800    # Whisper

# Planning figures used to turn tokens into minutes for the learner.
TOKENS_PER_SPEAKING_MIN = 2_600   # about 2.5 exchanges a minute at ~1,050 tokens each
TOKENS_PER_LEARNING_MIN = 1_100   # about one teacher call every 90 seconds at ~1,600 tokens


class AIError(Exception):
    pass


class NoKey(AIError):
    def __init__(self):
        super().__init__("Add your free Groq API key in Settings to switch the AI team on.")


class AI:
    def __init__(self, store):
        self.store = store

    # --- key and budget -------------------------------------------------------
    @property
    def key(self):
        return (self.store.get("groq_key") or os.environ.get("GROQ_API_KEY") or "").strip()

    @property
    def ready(self):
        return bool(self.key)

    def budget(self):
        """What is left today, in tokens and in learner minutes."""
        used = self.store.usage_today()
        total = TOKENS_PER_DAY * len(CHAT_MODELS)
        spent = sum(min(TOKENS_PER_DAY, used.get(m, {}).get("tokens", 0)) for m in CHAT_MODELS)
        left = max(0, total - spent)
        audio_left = max(0, AUDIO_SECONDS_PER_DAY - used.get(STT_MODEL, {}).get("audio", 0))
        return {
            "tokens_left": left, "tokens_total": total, "fraction": left / total,
            "speaking_min": int(min(left / TOKENS_PER_SPEAKING_MIN, audio_left / 60)),
            "learning_min": int(left / TOKENS_PER_LEARNING_MIN),
        }

    def _headers(self):
        if not self.key:
            raise NoKey()
        return {"Authorization": "Bearer " + self.key}

    def _models(self):
        used = self.store.usage_today()
        fresh = [m for m in CHAT_MODELS if used.get(m, {}).get("tokens", 0) < TOKENS_PER_DAY * 0.97]
        return fresh or CHAT_MODELS

    # --- chat -------------------------------------------------------------------
    def chat(self, messages, json_mode=False, max_tokens=700, temperature=0.6, models=None):
        """Blocking chat call. Returns text, or a dict when json_mode is set."""
        headers = self._headers()
        last = None
        for model in models or self._models():
            body = {"model": model, "messages": messages, "temperature": temperature,
                    "max_completion_tokens": max_tokens}
            if model.startswith("openai/gpt-oss"):
                body["reasoning_effort"] = "low"   # thinking tokens count against the daily allowance
                body["max_completion_tokens"] = max_tokens + 400  # leave room for that thinking
            if json_mode:
                body["response_format"] = {"type": "json_object"}
            try:
                r = requests.post(BASE + "/chat/completions", headers=headers, json=body, timeout=60)
            except requests.RequestException as e:
                raise AIError("No connection. Check your internet and try again.") from e
            if r.status_code == 401:
                raise AIError("Groq rejected the API key. Check it in Settings.")
            if r.status_code in (429, 500, 502, 503, 413):
                last = "%s is busy or out of free tokens for today" % model.split("/")[-1]
                if r.status_code == 429 and "per day" in r.text.lower():
                    self.store.add_usage(model, tokens=TOKENS_PER_DAY)  # mark exhausted until tomorrow
                continue
            if r.status_code != 200:
                last = "AI error %s: %s" % (r.status_code, r.text[:160])
                continue
            data = r.json()
            self.store.add_usage(model, tokens=data.get("usage", {}).get("total_tokens", 0))
            text = (data["choices"][0]["message"].get("content") or "").strip()
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
            if not json_mode:
                return text
            parsed = parse_json(text)
            if parsed is not None:
                return parsed
            last = "The AI returned something unreadable"
        raise AIError((last or "The AI is unavailable") + ". Try again in a minute.")

    # --- speech to text -----------------------------------------------------------
    def transcribe(self, path, lang, seconds=10.0, hint=""):
        headers = self._headers()
        data = {"model": STT_MODEL, "language": lang, "response_format": "json", "temperature": "0"}
        if hint:
            data["prompt"] = hint[:200]
        try:
            with open(path, "rb") as f:
                r = requests.post(BASE + "/audio/transcriptions", headers=headers, data=data,
                                  files={"file": (os.path.basename(path), f)}, timeout=90)
        except requests.RequestException as e:
            raise AIError("No connection. Check your internet and try again.") from e
        if r.status_code != 200:
            raise AIError("Could not hear that (%s). Try again." % r.status_code)
        self.store.add_usage(STT_MODEL, audio=max(10.0, seconds))  # Groq bills a 10-second minimum
        return r.json().get("text", "").strip()

    # --- vision -------------------------------------------------------------------
    def see(self, image_path, prompt, json_mode=True, max_tokens=500):
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        mime = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
        messages = [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": "data:%s;base64,%s" % (mime, b64)}}]}]
        return self.chat(messages, json_mode=json_mode, max_tokens=max_tokens, temperature=0.2, models=[VISION_MODEL])

    def ping(self):
        return self.chat([{"role": "user", "content": "Reply with the single word: ready"}], max_tokens=20,
                         temperature=0)


def parse_json(text):
    """Tolerant JSON extraction: plain, fenced, or embedded in prose."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except ValueError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except ValueError:
            return None
    return None


def run(fn, done=None, fail=None):
    """Run fn() off the UI thread; deliver the result or the error message back on it."""
    def work():
        try:
            result = fn()
        except AIError as e:
            if fail:
                Clock.schedule_once(lambda *_: fail(str(e)), 0)
            return
        except Exception as e:  # keep the UI alive whatever a worker hits
            if fail:
                Clock.schedule_once(lambda *_, m="Something went wrong: %s" % e: fail(m), 0)
            return
        if done:
            Clock.schedule_once(lambda *_: done(result), 0)

    threading.Thread(target=work, daemon=True).start()
