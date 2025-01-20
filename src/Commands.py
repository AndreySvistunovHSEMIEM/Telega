from src.InitBot import *
from src.InitGigaChat import *
from aiogram import Router, types
from gigachat.models import Chat, Messages, MessagesRole
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from src.DataBase import *
from src.LogInLogOutClasses import *
import bcrypt
from src.Constants import CONTENT
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

router = Router()

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Рекомендации по упражнениям 💪", callback_data="exercises")],
        [InlineKeyboardButton(text="Мотивационное сообщение 💭", callback_data="motivation")],
        [InlineKeyboardButton(text="Обратиться к GigaChat 🤖", callback_data="gigachat")]
    ])


def main_reply_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text="Рекомендации по упражнениям 💪"),
            KeyboardButton(text="Мотивационное сообщение 💭")
        ],
        [
            KeyboardButton(text="Обратиться к GigaChat 🤖")
        ]
    ], resize_keyboard=True, one_time_keyboard=False)


@router.message(Command("menu"))
async def menu_command(message: types.Message):
    await message.answer("Выберите опцию:", reply_markup=main_reply_menu())


@router.message(Command("start"))
async def start_command(message: types.Message, is_registered: bool, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Зарегистрироваться 👤", callback_data="register")],
        [InlineKeyboardButton(text="Войти 🔑", callback_data="login")]
    ])
    await message.answer("Добро пожаловать в реабилитационный бот! Выберите действие:", reply_markup=keyboard)


@router.message(Command("info"))
async def info_command(message: types.Message):
    info_text = (
        "Информация о боте: 🤖\n"
        "Этот бот предназначен для помощи пользователям в реабилитации.\n"
        "Вот что вы можете сделать:\n"
        "\t- Зарегистрироваться ✍️, чтобы начать\n"
        "\t- Получать рекомендации 📋 по упражнениям\n"
        "\t- Получать мотивационные сообщения 💪\n"
        "\t- Общаться 💬 с GigaChat для ответов на ваши вопросы"
    )
    await message.answer(info_text)

@router.message(Command("my_info"))
async def my_info_command(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("rehab_bot.db") as db:
        user_data = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = await user_data.fetchone()

    if user_data:
        _, username, _, full_name, injury_type, age, height, weight = user_data
        user_info_text = (
            f"Ваши данные:\n"
            f"- Логин: {username}\n"
            f"- Полное имя: {full_name}\n"
            f"- Тип травмы: {injury_type}\n"
            f"- Возраст: {age} лет\n"
            f"- Рост: {height} см\n"
            f"- Вес: {weight} кг"
        )
        await message.answer(user_info_text)
    else:
        await message.answer("Вы еще не зарегистрированы. Пожалуйста, зарегистрируйтесь, чтобы увидеть ваши данные.")


@router.callback_query(lambda c: c.data == "register")
async def register_user(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите ваш логин:")
    await state.set_state(Register.waiting_for_username)


@router.callback_query(lambda c: c.data == "login")
async def login_user(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите ваш логин:")
    await state.set_state(Login.waiting_for_username)


async def username_exists(username: str) -> bool:
    async with aiosqlite.connect("rehab_bot.db") as db:
        async with db.execute("SELECT 1 FROM users WHERE username = ?", (username,)) as cursor:
            return await cursor.fetchone() is not None


@router.message(Register.waiting_for_username)
async def ask_username_for_registration(message: types.Message, state: FSMContext):
    username = message.text
    if await username_exists(username):
        await message.answer("Такой логин уже существует. Пожалуйста, выберите другой.")
        return

    await state.update_data(username=username)
    await state.set_state(Register.waiting_for_password)
    await message.answer("Введите ваш пароль:")


@router.message(Register.waiting_for_password)
async def ask_password_for_registration(message: types.Message, state: FSMContext):
    password_hash = bcrypt.hashpw(message.text.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    await state.update_data(password=password_hash)
    await message.answer("Как вас зовут?")
    await state.set_state(Register.waiting_for_name)


@router.message(Register.waiting_for_name)
async def ask_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Введите ваш тип травмы (например, перелом, растяжение):")
    await state.set_state(Register.waiting_for_injury_type)


@router.message(Register.waiting_for_injury_type)
async def ask_injury_type(message: types.Message, state: FSMContext):
    await state.update_data(injury_type=message.text)
    await message.answer("Сколько вам лет?")
    await state.set_state(Register.waiting_for_age)


@router.message(Register.waiting_for_age)
async def ask_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (10 <= int(message.text) <= 100):
        await message.answer("Пожалуйста, введите корректный возраст (от 10 до 100 лет).")
        return

    await state.update_data(age=int(message.text))
    await message.answer("Введите ваш рост в см:")
    await state.set_state(Register.waiting_for_height)


@router.message(Register.waiting_for_height)
async def ask_height(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (120 <= int(message.text) <= 230):
        await message.answer("Пожалуйста, введите корректный рост в см.")
        return

    await state.update_data(height=int(message.text))
    await message.answer("Введите ваш вес в кг:")
    await state.set_state(Register.waiting_for_weight)


@router.message(Register.waiting_for_weight)
async def ask_weight(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '', 1).isdigit() or not (35 <= float(message.text) <= 230):  # Allow decimal values
        await message.answer("Пожалуйста, введите корректный вес в кг.")
        return

    await state.update_data(weight=float(message.text))
    user_data = await state.get_data()
    user_id = message.from_user.id
    username = user_data["username"]

    # Save to database
    try:
        async with aiosqlite.connect("rehab_bot.db") as db:
            await db.execute(
                '''INSERT INTO users (user_id, username, password, full_name, injury_type, age, height, weight) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (user_id, username, user_data["password"], user_data["full_name"], user_data["injury_type"],
                 user_data["age"], user_data["height"], user_data["weight"])
            )
            await db.commit()

        await state.set_state(Register.completed)
        await message.answer(
            "Спасибо за регистрацию! Вот что я могу для вас сделать:",
            reply_markup=main_menu()  # Inline keyboard
        )
    except aiosqlite.IntegrityError:
        await message.answer("Ошибка: данный пользователь уже зарегистрирован. Пожалуйста, войдите в систему.")


@router.message(Login.waiting_for_username)
async def ask_username_for_login(message: types.Message, state: FSMContext):
    username = message.text
    await state.update_data(username=username)
    await message.answer("Введите ваш пароль:")
    await state.set_state(Login.waiting_for_password)

# FSM Survey: Entering password for login
@router.message(Login.waiting_for_password)
async def ask_password_for_login(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    username = user_data["username"]

    async with aiosqlite.connect("rehab_bot.db") as db:
        async with db.execute("SELECT password FROM users WHERE username = ?", (username,)) as cursor:
            user_record = await cursor.fetchone()

    if user_record and bcrypt.checkpw(message.text.encode('utf-8'), user_record[0].encode('utf-8')):
        await message.answer("Вы успешно вошли в систему!", reply_markup=main_reply_menu())
        await state.set_state(Login.completed)
    else:
        await message.answer("Ошибка: неверный логин или пароль. Пожалуйста, попробуйте снова.")
        await state.set_state(Login.waiting_for_username)


@router.message(lambda message: True)
async def handle_free_text_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if message.content_type == types.ContentType.TEXT:
        text = message.text.strip()

        async with aiosqlite.connect("rehab_bot.db") as db:
            user_data = await db.execute("SELECT full_name, injury_type, height, weight FROM users WHERE user_id = ?",
                                         (user_id,))
            user_data = await user_data.fetchone()

        if user_data:
            full_name, injury_type, height, weight = user_data
            payload = Chat(
                messages=[
                    Messages(role=MessagesRole.SYSTEM, content=CONTENT),
                    Messages(role=MessagesRole.USER, content=f"{full_name} спрашивает: {text}. "
                                                             f"Рост: {height} см, Вес: {weight} кг.")
                ],
                temperature=0.7,
                max_tokens=1000
            )
            response = gigachat.chat(payload)
            await message.answer(response.choices[0].message.content)
        else:
            await message.answer("Пожалуйста, зарегистрируйтесь, чтобы взаимодействовать с ботом.")
    else:
        await message.answer(
            "К сожалению, я не поддерживаю взаимодействие с чем-либо, кроме текстовых сообщений. Пожалуйста, отправьте текстовый вопрос.")


@router.message()
async def handle_other_message(message: types.Message):
    if message.content_type in {types.ContentType.STICKER, types.ContentType.VOICE, types.ContentType.VIDEO,
                                types.ContentType.PHOTO}:
        await message.answer(
            "К сожалению, я не могу обрабатывать этот тип сообщения. Пожалуйста, отправьте текстовый вопрос.")


@router.callback_query(lambda c: c.data == "exercises")
async def send_exercise_recommendation(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    async with aiosqlite.connect("rehab_bot.db") as db:
        user = await db.execute("SELECT full_name, injury_type, height, weight FROM users WHERE user_id = ?",
                                (user_id,))
        user_data = await user.fetchone()

    if user_data:
        full_name, injury_type, height, weight = user_data
        await callback_query.message.answer(
            f"Обращение к GigaChat:\n"
            f"Предоставьте рекомендации по упражнениям для {full_name}, "
            f"который имеет травму: {injury_type}. Рост: {height} см, Вес: {weight} кг."
        )
        payload = Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content=CONTENT),
                Messages(role=MessagesRole.USER, content=f"Предоставьте рекомендации по упражнениям для {full_name}, "
                                                         f"который имеет травму: {injury_type}. Рост: {height} см, Вес: {weight} кг.")
            ],
            temperature=0.7,
            max_tokens=1000
        )
        response = gigachat.chat(payload)
        await callback_query.message.answer(response.choices[0].message.content)
    else:
        await callback_query.message.answer("Пожалуйста, зарегистрируйтесь для получения рекомендаций.")


@router.callback_query(lambda c: c.data == "motivation")
async def send_motivation(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    async with aiosqlite.connect("rehab_bot.db") as db:
        user_data = await db.execute("SELECT full_name, height, weight FROM users WHERE user_id = ?", (user_id,))
        user_data = await user_data.fetchone()

    full_name = user_data[0] if user_data else "пользователь"
    height = user_data[1] if user_data else "не указан"
    weight = user_data[2] if user_data else "не указан"

    # Create payload for GigaChat
    payload = Chat(
        messages=[
            Messages(role=MessagesRole.SYSTEM, content=CONTENT),
            Messages(role=MessagesRole.USER, content=f"Пожалуйста, предоставьте мотивационное сообщение для {full_name}. Рост: {height} см, Вес: {weight} кг.")
        ],
        temperature=0.7,
        max_tokens=1000
    )

    # Call GigaChat
    response = gigachat.chat(payload)
    await callback_query.message.answer(response.choices[0].message.content)

async def log_user_action(user_id: int, action: str):
    async with aiosqlite.connect("rehab_bot.db") as db:
        await db.execute("INSERT INTO user_actions (user_id, action) VALUES (?, ?)", (user_id, action))
        await db.commit()

@router.callback_query(lambda c: c.data == "gigachat")
async def start_gigachat(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Вы можете задать GigaChat любые вопросы. Пишите ниже:")
    await callback_query.message.reply("Введите ваш вопрос:")

    @dp.message(lambda message: message.from_user.id == callback_query.from_user.id)
    async def handle_gigachat_message(message: types.Message):
        if message.text.lower() == "пока":
            await message.answer("Диалог завершен. Если у вас есть другие вопросы, не стесняйтесь обращаться!")
            return

        user_id = message.from_user.id
        action_text = f"Запрос: {message.text}"
        await log_user_action(user_id, action_text)
        async with aiosqlite.connect("rehab_bot.db") as db:
            user_data = await db.execute("SELECT full_name, height, weight FROM users WHERE user_id = ?", (user_id,))
            user_data = await user_data.fetchone()
            full_name = user_data[0] if user_data else "пользователь"
            height = user_data[1] if user_data else "не указан"
            weight = user_data[2] if user_data else "не указан"

        payload = Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content=CONTENT),
                Messages(role=MessagesRole.USER, content=f"{full_name} спрашивает: {message.text}. "
                                                         f"Рост: {height} см, Вес: {weight} кг.")
            ],
            temperature=0.7,
            max_tokens=1000
        )
        response = gigachat.chat(payload)
        await message.answer(response.choices[0].message.content)

scheduler = AsyncIOScheduler()

async def health_check():
    async with aiosqlite.connect("rehab_bot.db") as db:
        cursor = await db.execute("SELECT user_id FROM users")
        user_ids = await cursor.fetchall()

    for user_id in user_ids:
        try:
            await bot.send_message(user_id[0], "Как вы себя чувствуете сегодня? Напишите ваше самочувствие:")
            logging.info(f"Отправлено сообщение о самочувствии пользователю {user_id[0]}")
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения пользователю {user_id[0]}: {e}")

@router.message(lambda message: True)
async def handle_health_response(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    async with aiosqlite.connect("rehab_bot.db") as db:
        user_data = await db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        user_data = await user_data.fetchone()

    if user_data:
        health_status = message.text.strip()
        async with aiosqlite.connect("rehab_bot.db") as db:
            await db.execute("INSERT INTO user_health (user_id, health_status) VALUES (?, ?)", (user_id, health_status))
            await db.commit()
            action = f"Отправил отзыв о самочувствии: {health_status}"
            await db.execute("INSERT INTO user_actions (user_id, action) VALUES (?, ?)", (user_id, action))
            await db.commit()

            await message.answer("Спасибо! Ваше самочувствие записано.")
    else:
        await message.answer("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь для участия в опросе.")


@scheduler.scheduled_job("interval", minutes=10)
async def scheduled_health_check():
    logging.info("Запускается опрос самочувствия.")
    await health_check()


@scheduler.scheduled_job("interval",  minutes=5)
async def daily_reminder():
    logging.info("Запускается функция daily_reminder")
    async with aiosqlite.connect("rehab_bot.db") as db:
        cursor = await db.execute("SELECT user_id FROM users")
        user_ids = await cursor.fetchall()
        if not user_ids:
            logging.info("Нет зарегистрированных пользователей для отправки напоминания.")
            return
        for user_id in user_ids:
            try:
                await bot.send_message(user_id[0], "Это ваше напоминание о ежедневных тренировках!\nРасскажите о своих достижениях/резултатах!")
                logging.info(f"Сообщение отправлено пользователю {user_id[0]}")
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения пользователю {user_id[0]}: {e}")

