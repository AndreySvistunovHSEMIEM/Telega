from aiogram import Dispatcher
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
import aiosqlite

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        async with aiosqlite.connect("rehab_bot.db") as db:
            user_data = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_data = await user_data.fetchone()
        data["is_registered"] = user_data is not None
        return await handler(event, data)

async def init_db():
    async with aiosqlite.connect("rehab_bot.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            username TEXT UNIQUE,
            password TEXT,
            full_name TEXT,
            injury_type TEXT,
            age INTEGER,
            height REAL,
            weight REAL
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS user_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS user_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            health_status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')
        await db.commit()