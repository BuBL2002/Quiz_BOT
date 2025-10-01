# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, FSInputFile 
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram import F

from database import (
    init_db, close_db, get_quiz_index, update_quiz_index,
    reset_current_correct, up_current_correct,
    get_current_correct, get_achieved_achievements, update_achieved_achievements,
    get_last_result, save_quiz_result     
)
from quiz_engine import get_question_data, get_total_questions, get_achievements_from_score, get_rating_text
from keyboard_builder import generate_options_keyboard, get_main_keyboard, get_language_keyboard
from strings import STRINGS
# Устанавливаем текущую директорию
# У VSCode есть такой прикол, что он работает в папке юзера
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
API_TOKEN = "8303342156:AAFCfTUiZ3233zv9nMiCvxbTYen97IubNwg"
# Бот - отправка, диспетчер - приём сообщений
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Храним прогресс-бары для пользователей: {user_id: {"lang": "ru", "progress": []}}
user_progress_data = {}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    # Перезапуск прогресс-бара
    if user_id in user_progress_data:
        del user_progress_data[user_id]
    await message.answer("Добро пожаловать в квиз!", reply_markup=get_main_keyboard())

@dp.message(F.text == "🎮 Начать игру")
async def start_game_button(message: Message):
    await message.answer("Добро пожаловать в квиз!")
    await message.answer("Выберите язык:", reply_markup=get_language_keyboard())

@dp.message(F.text.in_(["🇷🇺 Русский", "🇬🇧 English"]))
async def choose_language(message: Message):
    lang = "ru" if message.text == "🇷🇺 Русский" else "en"
    user_id = message.from_user.id
    
    total_questions = get_total_questions(lang)
    user_progress_data[user_id] = {
        "lang": lang,
        "progress": ["⬜"] * total_questions
    }
    
    await message.answer(STRINGS[lang]["start_quiz_message"], reply_markup=get_main_keyboard())
    await new_quiz(message, lang)

async def new_quiz(message: Message, lang: str):
    user_id = message.from_user.id      
    await reset_current_correct(user_id)
    await update_quiz_index(user_id, 0)
    await get_question(message, user_id, lang)

async def get_question(message: Message, user_id: int, lang: str):
    current_question_index = await get_quiz_index(user_id)
    total_questions = get_total_questions(lang)
       
    # Визуал
    progress_bar = "".join(user_progress_data[user_id]["progress"])
    # Текст (5/15)
    progress = STRINGS[lang]["progress"].format(
        current=current_question_index + 1,
        total=total_questions
    )

    
    question_data = get_question_data(current_question_index, lang)
    correct_option_text = question_data["options"][question_data["correct_option"]]
    keyboard = generate_options_keyboard(question_data["options"], correct_option_text, lang)

    text = f"{progress}\n{progress_bar}\n———————\n{question_data['question']}"
        
   
    photo = FSInputFile(question_data.get("image", ""))
    await message.answer_photo(photo, caption=text, reply_markup=keyboard)

async def update_progress_bar(user_id: int, question_index: int, is_correct: bool):    
    if (user_id in user_progress_data and 
        question_index < len(user_progress_data[user_id]["progress"])):
        
        sq = "🟩" if is_correct else "🟥"
        user_progress_data[user_id]["progress"][question_index] = sq
    

# Обработчик ответов пользователей
# callback_query -сообщение обратного вызова
# callback.data содержит: "right_answer:ru:Текст ответа"
async def handle_answer(callback: CallbackQuery, is_correct: bool):    
    parts = callback.data.split(":")
    lang = parts[1]
    user_answer = parts[2]
    user_id = callback.from_user.id
    
    # Удаляем кнопки
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    
    # Показываем ответ пользователя
    if is_correct:
        await callback.message.answer(f"Ваш ответ: {user_answer}\n{STRINGS[lang]['correct']}")
        # Увеличиваем счетчик правильных ответов
        current_correct = await get_current_correct(user_id)
        await up_current_correct(user_id, current_correct + 1)
    else:        
        await callback.message.answer(f"Ваш ответ: {user_answer}")
    
    # Получаем текущий индекс
    current_index = await get_quiz_index(user_id)
    
    await update_progress_bar(user_id, current_index, is_correct)
    current_index += 1       
    if current_index < get_total_questions(lang):
        await update_quiz_index(user_id, current_index)
        await get_question(callback.message, user_id, lang)
    else:
        await callback.message.answer(STRINGS[lang]["quiz_finished"], reply_markup=get_main_keyboard())
        await award_achievements(user_id, callback.message, lang)


@dp.callback_query(F.data.startswith("right_answer:"))
async def right_answer(callback: CallbackQuery):
    await handle_answer(callback, is_correct=True)

@dp.callback_query(F.data.startswith("wrong_answer:"))
async def wrong_answer(callback: CallbackQuery):
    await handle_answer(callback, is_correct=False)
# ==========================================================================
async def award_achievements(user_id: int, message: Message, lang: str):
    correct = await get_current_correct(user_id)
    total_questions = get_total_questions(lang)
    
    # Сохраняем результат
    await save_quiz_result(user_id, correct, lang)
    
    new_achievements = get_achievements_from_score(correct, lang)
    old_achievements_str = await get_achieved_achievements(user_id)
    old_achievements_list = old_achievements_str.split(",") if old_achievements_str else []
    
    # Показываем итоговый результат
    accuracy = (correct / total_questions) * 100
    result_text = f"""
🎉 *Квиз завершен!*

📊 *Ваш результат:*
• Правильных ответов: {correct}/{total_questions}
• Процент: {accuracy:.1f}%
• {get_rating_text(accuracy)}
"""
    
    await message.answer(result_text, parse_mode="Markdown")
    
    # Проверяем достижения
    new_ones = []
    for achievement in new_achievements:
        if achievement not in old_achievements_list:
            new_ones.append(achievement)

    if new_ones:
        prefix = STRINGS[lang].get("achievements_prefix", "🎉 You earned: ")
        await message.answer(prefix + ", ".join(new_ones))

    all_achieved = set(new_achievements) | set(old_achievements_list)
    await update_achieved_achievements(user_id, ",".join(all_achieved))

@dp.message(F.text == "📞 Связаться")
async def contact_handler(message: Message):
    contact_info = """
📞 **Мои контакты:**
✉️ Email: random@mail.ru
📱 Telegram: @Ilyxey
💼 Гитхаб: [код бота](https://github.com/)
    """
    await message.answer(contact_info, parse_mode="Markdown")

@dp.message(F.text == "📚 Документация")
async def docs_handler(message: Message):
    docs_link = "https://core.telegram.org/bots/features#commands"
    await message.answer(f"📚 Документация доступна по ссылке:\n{docs_link}")

@dp.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    """Показывает статистику пользователя"""
    user_id = message.from_user.id
    
    # Получаем последний результат
    last_result = await get_last_result(user_id)
    
    if last_result:
        score = last_result["score"]
        total_questions = get_total_questions(last_result["lang"])
        lang = last_result["lang"]
        date = last_result["date"]
        
        # Вычисляем процент правильных ответов
        accuracy = (score / total_questions) * 100 if total_questions > 0 else 0
        
        stats_text = f"""
📊 *Ваша статистика:*

🎯 Последний результат:
   • Правильных ответов: {score}/{total_questions}
   • Процент: {accuracy:.1f}%
   • Дата: {date.split()[0] if date else 'Н/Д'}
   • Язык: {'🇷🇺 Русский' if lang == 'ru' else '🇬🇧 English'}

⭐ Оценка результата: 
{get_rating_text(accuracy)}"""
    else:
        stats_text = "📊 У вас еще нет результатов. Пройдите квиз чтобы увидеть статистику!"
    
    await message.answer(stats_text, parse_mode="Markdown")

# ===================================
# Запуск
async def main():
    await init_db()
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())