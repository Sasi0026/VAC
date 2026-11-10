# VAC

A Kivy mobile app that gets a learner through a language exam (job, visa, scholarship) with a team of
five AI agents who behave like one best friend.

Starter languages: **Japanese** (JLPT), **German** (Goethe-Zertifikat), **English** (IELTS).

## Run it on your PC

```powershell
cd D:\VAC
.\.venv\Scripts\python.exe main.py
```

A phone-shaped window opens. Lessons, quizzes, mock tests, the sketchbook and the calendar work straight
away. For conversation, corrections, pronunciation and the camera, paste a free Groq key in onboarding or
Settings (create one at https://console.groq.com/keys).

## The agents

| Agent | Job | Works offline |
|---|---|---|
| Curator | Plans the course from goal, level, pace and interests; writes personal lessons | plan yes, personal lessons no |
| Teacher | Explains, role-plays, corrects writing, checks pronunciation and handwriting | no |
| Examiner | Lesson quizzes, daily / weekly / monthly check-ins, mock exams, marking | multiple choice yes, writing and speaking marks no (self-marking instead) |
| Scout | Tracks skills, participation, weak items and interests; picks simulations | yes |
| Buddy | Greets, reminds and cheers | yes |

All of them read and write one learner memory (`vac/db.py`, SQLite on the device). Code: `vac/agents.py`.

## AI

Open-weight models on Groq's free plan (`vac/ai.py`):

- Chat: `openai/gpt-oss-120b`, falling back to `gpt-oss-20b`, then `qwen/qwen3.8-27b`
- Speech to text: `whisper-large-v3-turbo`
- Camera: `qwen/qwen3.8-27b`
- Text to speech: the phone's own voices (offline, no limit)

The app tracks tokens used per day and shows what is left on the Home screen. Check your real limits at
https://console.groq.com/settings/limits, since Groq changes them.

## Course content

- `vac/content/exams.py`: official exam structure, timing and pass marks, with source links
- `vac/content/ja.py`, `de.py`, `en.py`: the courses. The first level of each (JLPT N5, Goethe A1, IELTS
  Foundation) is written out: 6 units, 18 lessons. Higher levels are outlines; the Teacher writes each
  lesson on first open and it is cached on the device
- `vac/content/mocks.py`: built-in mock tests for N5, Goethe A1 and IELTS. Original questions in the
  official format, shorter than the real papers. They unlock when every lesson of the level is done.
  Mocks for higher levels are written by the Examiner agent on demand
- `vac/content/sketches.py`: the illustrated objects and scenes
- `vac/content/scenarios.py`: interest-based speaking simulations

## Build the Android app

GitHub Actions builds the APK (`.github/workflows/build.yml`). Push to `main`, or run the workflow by hand
from the Actions tab. It runs the unit tests, then Buildozer, and uploads `VAC-debug-apk` as an artifact
on the run page. The first build takes about 15 to 20 minutes; later ones reuse the cached toolchain.

The toolchain is pinned (Buildozer 1.5.0, Cython 0.29.33, python-for-android v2024.01.21, Kivy 2.3.0).
Change those together, in `buildozer.spec` and the workflow.

Install a Japanese and a German voice on the phone (Settings > Text-to-speech) for listening practice.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

## Developer tools

- `python tools/shots.py <folder> [ja|de|en]`: drives the app through every screen and saves screenshots
- `python tools/render_sketches.py out.png`: contact sheet of all illustrations

## Fonts and icons

Inter and Noto Sans JP (SIL Open Font License), Phosphor Icons (MIT). Licences are in `assets/fonts/`.
