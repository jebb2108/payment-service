from typing import TYPE_CHECKING

from src.services.database import database_service
from src.services.yookassa import yookassa_service

if TYPE_CHECKING:
    from src.services.database import DatabaseService
    from src.services.yookassa import YookassaService


async def get_db() -> "DatabaseService":
    if not database_service.initialized:
        await database_service.connect()
    return database_service

async def get_yookassa() -> "YookassaService":
    return yookassa_service