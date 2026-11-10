"""Course catalogue and lookups."""
from . import de, en, ja
from .exams import EXAMS
from .mocks import MOCKS

COURSES = {"ja": ja.COURSE, "de": de.COURSE, "en": en.COURSE}
LANGS = [("ja", "Japanese", "日本語", "JLPT N5 to N1"), ("de", "German", "Deutsch", "Goethe-Zertifikat A1 to B1"),
         ("en", "English", "English", "IELTS, all bands")]


def course(code):
    return COURSES[code]


def level_exam(level):
    """Exam id a level prepares for."""
    return level.get("exam", level["id"])


def find_level(level_id):
    for c in COURSES.values():
        for lv in c["levels"]:
            if lv["id"] == level_id:
                return lv
    return None


def lessons_of(level):
    return [ls for u in level["units"] for ls in u["lessons"]]


def find_lesson(lesson_id):
    """-> (course, level, unit, lesson) or None."""
    for c in COURSES.values():
        for lv in c["levels"]:
            for u in lv["units"]:
                for ls in u["lessons"]:
                    if ls["id"] == lesson_id:
                        return c, lv, u, ls
    return None


def level_progress(level, done):
    ls = lessons_of(level)
    return sum(1 for x in ls if x["id"] in done), len(ls)


def item_pool(level):
    """Every word item in a level, for building quiz distractors."""
    return [it for ls in lessons_of(level) for it in ls["items"]]


def has_mock(exam_id):
    return exam_id in MOCKS


__all__ = ["COURSES", "LANGS", "EXAMS", "MOCKS", "course", "level_exam", "find_level", "lessons_of", "find_lesson",
           "level_progress", "item_pool", "has_mock"]
