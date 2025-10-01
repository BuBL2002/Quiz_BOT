# keyboard_builder.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List

def generate_options_keyboard(answer_options: List[str], right_answer_text: str, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for option in answer_options:
        is_correct = "right_answer" if option == right_answer_text else "wrong_answer"
        # Сохраняем текст ответа в callback_data
        callback_data = f"{is_correct}:{lang}:{option}"
        builder.add(InlineKeyboardButton(text=option, callback_data=callback_data))
    
    builder.adjust(1)
    return builder.as_markup()

# Основная клавиатура, которая открыта всегда
def get_main_keyboard():
    """Возвращает основную клавиатуру"""
    builder = ReplyKeyboardBuilder()
    # Добавляет кнопку к ↑ функции
    builder.add(KeyboardButton(text="🎮 Начать игру"))
    builder.add(KeyboardButton(text="📊 Статистика"))
    builder.add(KeyboardButton(text="📞 Связаться"))
    builder.add(KeyboardButton(text="📚 Документация"))
    # Распределяет кнопки в дисплее, сначала 1, потом 2...
    builder.adjust(1, 2, 1)
    # as_markup() - превращает builder в готовую клавиатуру
    # resize_keyboard=True - кнопки автоматически подстраиваются под размер экрана
    return builder.as_markup(resize_keyboard=True)

def get_language_keyboard():
    """Возвращает клавиатуру выбора языка"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🇷🇺 Русский"))
    builder.add(KeyboardButton(text="🇬🇧 English"))
    builder.add(KeyboardButton(text="🎮 Начать игру"))  
    builder.add(KeyboardButton(text="📊 Статистика"))
    builder.add(KeyboardButton(text="📞 Связаться"))
    builder.adjust(2, 1, 2)  
    return builder.as_markup(resize_keyboard=True)
