
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import asyncio

load_dotenv()

API_TOKEN = os.getenv("TG_BOT_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

questions = [
    "1. Наименование вашего юридического лица с указанием инн (Отвечать только в таком формате: ООО «Ромашка» 765432675)",
    "2. Номер и дата договора между нами (При наличии приложения указать договор + приложение)",
    "3. Сумма услуг (общая сумма) (При наличии в договоре детализации на размещение - указать сумму на размещение и сумму общую. 
Отвечать только в таком формате: 25324,33 или 25324,33 - размещение, 50000 - общая)",
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
    await state.set_state(Form.step)
    await state.update_data(answers=[], step=0)
    await message.answer("Заполните информацию:\n" + questions[0])

@dp.message(Form.step)
async def process_form(message: Message, state: FSMContext):
    data = await state.get_data()
    answers = data["answers"]
    step = data["step"]

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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
