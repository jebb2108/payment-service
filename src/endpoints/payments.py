from fastapi import APIRouter
from fastapi.params import Query, Depends

from src.dependencies import get_db, get_yookassa

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.database import DatabaseService

router = APIRouter(prefix='/api/payments')

@router.get('/link')
async def get_user_link(
        user_id: int = Query(..., description="User ID")
):
    yookassa_client = await get_yookassa()
    return yookassa_client.create_monthly_payment_link(user_id)

@router.get('/due_to')
async def get_user_due_to(
        user_id: int = Query(..., description="User ID"),
        database: "DatabaseService" = Depends(get_db)
):
    return await database.get_users_due_to(user_id)