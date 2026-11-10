"""Official exam specifications, taken from the test bodies' own sites (checked November 2026).

JLPT   https://www.jlpt.jp/e/guideline/testsections.html  and  /e/guideline/results.html
Goethe https://www.goethe.de/ins/de/en/prf/gzsd1.cfm  (A1 regulations PDF)
IELTS  https://takeielts.britishcouncil.org/take-ielts/test-format  and  https://ielts.org

`verified` is False where a figure comes from general knowledge rather than a page read while
building this file; the app tells the learner to confirm those on the official site.
"""

_JLPT_URL = "https://www.jlpt.jp/e/"
_JLPT_3 = [{"id": "lk", "name": "Language Knowledge", "max": 60, "pass": 19},
           {"id": "rd", "name": "Reading", "max": 60, "pass": 19},
           {"id": "li", "name": "Listening", "max": 60, "pass": 19}]
_JLPT_2 = [{"id": "lk", "name": "Language Knowledge + Reading", "max": 120, "pass": 38},
           {"id": "li", "name": "Listening", "max": 60, "pass": 19}]

EXAMS = {
    "ja-n5": {
        "name": "JLPT N5", "body": "Japan Foundation / JEES", "url": _JLPT_URL, "verified": True,
        "can_do": "Understand some basic Japanese: typical expressions and sentences in hiragana, katakana and basic "
                  "kanji; short, slowly spoken conversations about everyday and classroom topics.",
        "official": [("Language Knowledge (Vocabulary)", 20), ("Language Knowledge (Grammar) + Reading", 40),
                     ("Listening", 30)],
        "score_sections": _JLPT_2, "pass_total": 80, "total": 180,
        "item_types": {
            "Vocabulary": ["Kanji reading", "Orthography", "Contextually-defined expressions", "Paraphrases"],
            "Grammar + Reading": ["Sentential grammar 1", "Sentential grammar 2", "Text grammar",
                                  "Comprehension (short passages)", "Comprehension (mid-size passages)",
                                  "Information retrieval"],
            "Listening": ["Task-based comprehension", "Comprehension of key points", "Verbal expressions",
                          "Quick response"]},
    },
    "ja-n4": {
        "name": "JLPT N4", "body": "Japan Foundation / JEES", "url": _JLPT_URL, "verified": True,
        "can_do": "Understand basic Japanese: passages on familiar daily topics in basic vocabulary and kanji; "
                  "everyday conversations when spoken slowly.",
        "official": [("Language Knowledge (Vocabulary)", 25), ("Language Knowledge (Grammar) + Reading", 55),
                     ("Listening", 35)],
        "score_sections": _JLPT_2, "pass_total": 90, "total": 180,
    },
    "ja-n3": {
        "name": "JLPT N3", "body": "Japan Foundation / JEES", "url": _JLPT_URL, "verified": True,
        "can_do": "Understand Japanese used in everyday situations to a certain degree: specific content on everyday "
                  "topics, newspaper headlines, coherent conversations at near-natural speed.",
        "official": [("Language Knowledge (Vocabulary)", 30), ("Language Knowledge (Grammar) + Reading", 70),
                     ("Listening", 40)],
        "score_sections": _JLPT_3, "pass_total": 95, "total": 180,
        "item_types": {
            "Vocabulary": ["Kanji reading", "Orthography", "Contextually-defined expressions", "Paraphrases", "Usage"],
            "Grammar + Reading": ["Sentential grammar 1", "Sentential grammar 2", "Text grammar",
                                  "Comprehension (short passages)", "Comprehension (mid-size passages)",
                                  "Comprehension (long passages)", "Information retrieval"],
            "Listening": ["Task-based comprehension", "Comprehension of key points",
                          "Comprehension of general outline", "Verbal expressions", "Quick response"]},
    },
    "ja-n2": {
        "name": "JLPT N2", "body": "Japan Foundation / JEES", "url": _JLPT_URL, "verified": True,
        "can_do": "Understand Japanese in everyday situations and, to a certain degree, in a variety of "
                  "circumstances: articles, commentaries, news at nearly natural speed.",
        "official": [("Language Knowledge (Vocabulary/Grammar) + Reading", 105), ("Listening", 50)],
        "score_sections": _JLPT_3, "pass_total": 90, "total": 180,
    },
    "ja-n1": {
        "name": "JLPT N1", "body": "Japan Foundation / JEES", "url": _JLPT_URL, "verified": True,
        "can_do": "Understand Japanese used in a variety of circumstances: logically complex and abstract writing, "
                  "lectures and news at natural speed.",
        "official": [("Language Knowledge (Vocabulary/Grammar) + Reading", 110), ("Listening", 55)],
        "score_sections": _JLPT_3, "pass_total": 100, "total": 180,
    },
    "de-a1": {
        "name": "Goethe-Zertifikat A1: Start Deutsch 1", "body": "Goethe-Institut", "verified": True,
        "url": "https://www.goethe.de/ins/de/en/prf/gzsd1.cfm",
        "can_do": "Understand and use familiar everyday expressions and very simple sentences; introduce yourself "
                  "and others; fill in simple forms; ask and answer questions about personal details.",
        "official": [("Hören (listening)", 20), ("Lesen (reading)", 25), ("Schreiben (writing)", 20),
                     ("Sprechen (speaking, group exam)", 15)],
        "score_sections": [{"id": "ho", "name": "Hören", "max": 25, "pass": 0},
                           {"id": "le", "name": "Lesen", "max": 25, "pass": 0},
                           {"id": "sc", "name": "Schreiben", "max": 25, "pass": 0},
                           {"id": "sp", "name": "Sprechen", "max": 25, "pass": 0}],
        "pass_total": 60, "total": 100,
    },
    "de-a2": {
        "name": "Goethe-Zertifikat A2", "body": "Goethe-Institut", "verified": False,
        "url": "https://www.goethe.de/en/spr/kup/prf/prf/gzsd2.html",
        "can_do": "Understand sentences and common expressions in everyday situations; communicate in simple, "
                  "routine exchanges; describe your background, education and immediate surroundings.",
        "official": [("Lesen", 30), ("Hören", 30), ("Schreiben", 30), ("Sprechen (pair exam)", 15)],
        "score_sections": [{"id": "le", "name": "Lesen", "max": 25, "pass": 0},
                           {"id": "ho", "name": "Hören", "max": 25, "pass": 0},
                           {"id": "sc", "name": "Schreiben", "max": 25, "pass": 0},
                           {"id": "sp", "name": "Sprechen", "max": 25, "pass": 0}],
        "pass_total": 60, "total": 100,
    },
    "de-b1": {
        "name": "Goethe-Zertifikat B1", "body": "Goethe-Institut", "verified": False,
        "url": "https://www.goethe.de/en/spr/kup/prf/prf/gzb1.html",
        "can_do": "Understand the main points on familiar matters at work, school and leisure; deal with most travel "
                  "situations; describe experiences, hopes and plans and give brief reasons.",
        "official": [("Lesen", 65), ("Hören", 40), ("Schreiben", 60), ("Sprechen (pair exam)", 15)],
        "score_sections": [{"id": "le", "name": "Lesen", "max": 100, "pass": 60},
                           {"id": "ho", "name": "Hören", "max": 100, "pass": 60},
                           {"id": "sc", "name": "Schreiben", "max": 100, "pass": 60},
                           {"id": "sp", "name": "Sprechen", "max": 100, "pass": 60}],
        "pass_total": 240, "total": 400,
    },
    "en-ielts": {
        "name": "IELTS", "body": "British Council, IDP and Cambridge", "verified": True, "band": True,
        "url": "https://ielts.org",
        "can_do": "Bands run from 0 to 9. Universities commonly ask for 6.0-7.0 overall; skilled-migration and work "
                  "visas commonly ask for 5.0-7.0, depending on the country and route.",
        "official": [("Listening: 4 parts, 40 questions", 30), ("Reading: 3 sections, 40 questions", 60),
                     ("Writing: Task 1 (150+ words) and Task 2 (250+ words)", 60),
                     ("Speaking: 3 parts, face to face", 14)],
        "score_sections": [{"id": "li", "name": "Listening", "max": 9, "pass": 0},
                           {"id": "rd", "name": "Reading", "max": 9, "pass": 0},
                           {"id": "wr", "name": "Writing", "max": 9, "pass": 0},
                           {"id": "sp", "name": "Speaking", "max": 9, "pass": 0}],
        "pass_total": 24, "total": 36,
    },
}


def spec(exam_id):
    return EXAMS.get(exam_id)
