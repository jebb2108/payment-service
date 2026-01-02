from typing import Dict

from fastapi import APIRouter
from fastapi.params import Query, Depends

from src.dependencies import get_db, get_yookassa
from src.models import Payment
from src.services.database import DatabaseService
from src.services.yookassa import YookassaService

router = APIRouter(prefix='/api/payments')

@router.get('/link')
async def get_user_link(
        user_id: int = Query(..., description="User ID"),
        yookassa: YookassaService = Depends(get_yookassa)
) -> str:
    return yookassa.create_monthly_payment_link(user_id)

@router.post('/add')
async def add_user_payment(
        payment_data: Payment,
        database: DatabaseService = Depends(get_db)
) -> None:
    """ Записывает новую платежку пользователя """
    return await database.create_payment(payment_data)


@router.get('/due_to')
async def get_user_due_to(
        user_id: int = Query(..., description="User ID"),
        database: DatabaseService = Depends(get_db)
):
    return await database.get_users_due_to(user_id)


@router.post('activate')
async def activate_subscription(
        user_data: dict,
        database: DatabaseService = Depends(get_db)
):
    user_id = user_data.get('user_id')
    return await database.activate_subscription(user_id)


@router.post('deactivate')
async def deactivate_subscription(
        user_data: dict,
        database: DatabaseService = Depends(get_db)
):
    user_id = user_data.get('user_id')
    return await database.deactivate_subscription(user_id)