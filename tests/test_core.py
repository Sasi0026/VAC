"""Core logic: course content, quizzes, mock scoring and the offline agents. No Kivy needed."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vac import content  # noqa: E402
from vac.agents import Team  # noqa: E402
from vac.content.scenarios import SCENARIOS  # noqa: E402
from vac.content.sketches import OBJECTS, SCENES, WORDS  # noqa: E402
from vac.db import Store  # noqa: E402
from vac.sketch_geo import resolve  # noqa: E402

LANGS = ["ja", "de", "en"]


@pytest.fixture
def team(tmp_path):
    store = Store(str(tmp_path / "vac.db"))
    return Team(store, ai=None)


def start(team, lang):
    team.store.set("profile", {"name": "Test", "lang": lang, "goal": "job", "interests": ["gaming"], "minutes": 20,
                               "level": "", "band": 6.0})
    return team.level


@pytest.mark.parametrize("lang", LANGS)
def test_first_level_is_written_out(lang):
    level = content.course(lang)["levels"][0]
    lessons = content.lessons_of(level)
    assert len(lessons) == 18
    for ls in lessons:
        assert not ls.get("ai") and ls["items"], ls["id"]
    ids = [ls["id"] for c in content.COURSES.values() for lv in c["levels"] for ls in content.lessons_of(lv)]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("lang", LANGS)
def test_every_lesson_quiz_is_answerable(team, lang):
    level = start(team, lang)
    for ls in content.lessons_of(level):
        paper = team.examiner.lesson_quiz(ls, level)
        assert len(paper["questions"]) >= 3
        for q in paper["questions"]:
            assert len(q["o"]) >= 2 and len(set(q["o"])) == len(q["o"])
            assert 0 <= q["a"] < len(q["o"])


@pytest.mark.parametrize("lang", LANGS)
def test_mock_pass_and_fail(team, lang):
    level = start(team, lang)
    exam_id = content.level_exam(level)
    paper = team.examiner.mock(exam_id)
    sections = {s["id"] for s in paper["sections"]}
    assert all(q["sec"] in sections for q in paper["questions"])

    full = [{"points": q.get("max", 1), "max": q.get("max", 1)} for q in paper["questions"]]
    result = team.examiner.mark(paper, full)
    assert result["passed"] and result["total"] == paper["total"]

    none = [{"points": 0, "max": q.get("max", 1)} for q in paper["questions"]]
    assert not team.examiner.mark(team.examiner.mock(exam_id), none)["passed"]


def test_jlpt_sectional_minimum_fails_the_paper(team):
    start(team, "ja")
    paper = team.examiner.mock("ja-n5")
    # everything right except listening: total 120 clears the 80 pass mark, but listening is below 19
    marks = [{"points": 0 if q["sec"] == "li" else 1, "max": 1} for q in paper["questions"]]
    result = team.examiner.mark(paper, marks)
    assert result["total"] >= paper["pass_total"] and not result["passed"]


def test_lesson_completes_only_on_pass(team):
    level = start(team, "ja")
    ls = content.lessons_of(level)[0]
    paper = team.examiner.lesson_quiz(ls, level)
    team.examiner.mark(paper, [{"points": 0, "max": 1} for _ in paper["questions"]])
    assert ls["id"] not in team.store.done_lessons()
    team.examiner.mark(paper, [{"points": 1, "max": 1} for _ in paper["questions"]])
    assert ls["id"] in team.store.done_lessons()
    assert team.curator.next_lesson()[1]["id"] == content.lessons_of(level)[1]["id"]


def test_missed_words_come_back(team):
    level = start(team, "ja")
    ls = content.lessons_of(level)[0]
    paper = team.examiner.lesson_quiz(ls, level)
    team.examiner.mark(paper, [{"points": 0, "max": 1} for _ in paper["questions"]])
    assert team.store.weak_items("ja")


@pytest.mark.parametrize("kind,least", [("daily", 5), ("weekly", 6), ("monthly", 7)])
def test_checkins(team, kind, least):
    start(team, "de")
    paper = team.examiner.checkin(kind)
    assert len(paper["questions"]) >= least
    assert any(q["type"] == "write" for q in paper["questions"])


def test_plan_and_friend_work_offline(team):
    start(team, "en")
    kinds = [x["kind"] for x in team.curator.today()]
    assert kinds[:3] == ["lesson", "daily", "scenario"]
    hello, head, msg = team.buddy.greeting()
    assert "Test" in hello and head and msg
    assert team.scout.suggest(1)[0]["interest"] == "gaming"
    assert team.scout.insights()


def test_text_answers_are_matched_loosely(team):
    q = {"accept": ["6.30", "six thirty"]}
    assert team.examiner.check_text(q, " Six  Thirty ")
    assert not team.examiner.check_text(q, "7.30")


def test_illustrations_resolve():
    for name in list(OBJECTS) + list(SCENES):
        strokes = resolve(name, OBJECTS, SCENES)
        assert strokes, name
        assert all(len(pts) >= 2 for pts, _, _ in strokes), name
    assert set(WORDS) <= set(OBJECTS)
    assert all(s["sketch"] in SCENES for s in SCENARIOS)
    for c in content.COURSES.values():
        for lv in c["levels"]:
            for u in lv["units"]:
                assert u["sketch"] in SCENES, u["id"]
                for ls in u["lessons"]:
                    assert ls["sketch"] is None or ls["sketch"] in SCENES, ls["id"]
                    assert all(it.get("sk") is None or it["sk"] in OBJECTS for it in ls["items"]), ls["id"]
