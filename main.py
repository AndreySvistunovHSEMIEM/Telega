from src.Commands import *
import asyncio

logging.basicConfig(level=logging.INFO)

async def on_startup():
    await init_db()
    scheduler.start()
    logging.info("Планировщик успешно запущен")

if __name__ == "__main__":
    dp.message.middleware(RegistrationMiddleware())
    dp.include_router(router)

    async def main():
        await on_startup()
        await dp.start_polling(bot, skip_updates=True)

    asyncio.run(main())