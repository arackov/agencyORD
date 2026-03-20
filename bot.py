import os
import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("TG_BOT_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Флаг для предотвращения двойного запуска
bot_started = False

# Создаем Flask приложение для Health Check
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return "Bot is running", 200

questions = [
    "1. Наименование вашего юридического лица с указанием инн (Отвечать только в таком формате: ООО «Ромашка» 765432675)",
    "2. Номер и дата договора между нами (При наличии приложения указать договор + приложение)",
    "3. Сумма услуг (общая сумма) (При наличии в договоре детализации на размещение - указать сумму на размещение и сумму общую. Отвечать только в таком формате: 25324,33 или 25324,33 - размещение, 50000 - общая)",
    "4. Рекламодатель (Обязательно указание инн. Отвечать только в таком формате: ООО «Ромашка» 784565432)",
    "5. Первый исполнитель в цепочке договоров с рекламодателем (Обязательно указание инн. Отвечать только в таком формате: ООО «Ромашка» 784565432)",
    "6. Номер и дата изначального договора (между рекламодателем и первым исполнителем в цепочке договоров с рекламодателем) (Отвечать только в таком формате: № 1882 от 21.06.2025)",
    "7. Вид (оказание услуг, посредничество, дополнительное соглашение) и предмет договора (посредничество, распространение рекламы, организация распространения рекламы, представительство, иное) (Отвечать только в таком формате: Оказание услуг, организация распространение)",
    "8. Название проекта",
    "9. Площадка и тип размещения (Пример: ВК, пост",
    "10. Срок размещения публикации (Дата, после которой возможно удаление)"
]

class Form(StatesGroup):
    step = State()

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    # Очищаем состояние перед началом новой анкеты
    await state.clear()
    await state.set_state(Form.step)
    await state.update_data(answers=[], step=0)
    await message.answer("Заполните информацию:\n" + questions[0])

@dp.message(Form.step)
async def process_form(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # Проверяем, есть ли данные, если нет - инициализируем
    if not data:
        await state.set_state(Form.step)
        await state.update_data(answers=[], step=0)
        data = await state.get_data()
    
    answers = data.get("answers", [])
    step = data.get("step", 0)

    # Сохраняем ответ
    answers.append(message.text)
    step += 1

    if step < len(questions):
        await state.update_data(answers=answers, step=step)
        await message.answer(questions[step])
    else:
        result = "Новая анкета:\n\n"
        for i, answer in enumerate(answers):
            result += f"{questions[i]}:\n{answer}\n\n"

        await bot.send_message(ADMIN_ID, result)
        await message.answer("Спасибо! Данные отправлены.")
        await state.clear()

async def reset_webhook():
    """Сбрасываем вебхук перед запуском"""
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook deleted, pending updates dropped")

async def main():
    """Запускаем бота"""
    global bot_started
    if bot_started:
        print("⚠️ Bot already started, skipping...")
        return
    bot_started = True
    
    await reset_webhook()
    print("🚀 Starting bot polling...")
    await dp.start_polling(bot)

def run_flask():
    """Запускаем Flask в отдельном потоке"""
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("🌐 Flask server started in background thread")
    
    # Запускаем бота в основном потоке
    asyncio.run(main())