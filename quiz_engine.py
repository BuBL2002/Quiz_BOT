# quiz_engine.py
import json
from typing import List, Dict

_quiz_data = {}

def load_quiz_data(lang: str = "ru") -> List[Dict]:
    global _quiz_data
    
    if lang not in _quiz_data:
        try:
            with open(f"quiz_{lang}.json", "r", encoding="utf-8") as f:
                _quiz_data[lang] = json.load(f)
        except FileNotFoundError:
            with open("quiz_ru.json", "r", encoding="utf-8") as f:
                _quiz_data[lang] = json.load(f)
    
    return _quiz_data[lang]

def get_question_data(index: int, lang: str = "ru") -> Dict:
    data = load_quiz_data(lang)
    if 0 <= index < len(data):
        return data[index]


def get_total_questions(lang: str = "ru") -> int:
    return len(load_quiz_data(lang))

def get_achievements_from_score(score, lang: str = "ru"):
    if lang == "en":
        achive = []
        if score >= 0:    achive.append("Beginner")
        if score >= 5:    achive.append("Basic Expert")
        if score >= 8:    achive.append("Intermediate")
        if score >= 11:   achive.append("Smoke Master")
        if score >= 14:   achive.append("Unique")
        return achive
    else:
        achive = []
        if score >= 0:    achive.append("Начинающий")
        if score >= 5:    achive.append("Знаток основ")
        if score >= 8:    achive.append("Среднячок")
        if score >= 11:   achive.append("Мастер дыма")
        if score >= 14:   achive.append("Уникум")
        return achive
    

def get_rating_text(accuracy: float) -> str:
    """Возвращает текстовую оценку результата"""
    if accuracy >= 90: return "🏆 Отлично!"
    if accuracy >= 70: return "🎯 Хорошо!"
    if accuracy >= 50: return "👍 Неплохо!"
    return "💪 Попробуй еще!"