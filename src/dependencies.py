from src.services.database import database_service
from src.services.yookassa import yookassa_service


async def get_db():
    if not database_service.initialized:
        await database_service.connect()
    return database_service

async def get_yookassa():
    return yookassa_service