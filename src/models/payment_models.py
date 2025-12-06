from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from src.config import config


class Payment(BaseModel):
    """
    Модель платежа (для базы данных).
    """

    user_id: int = Field(..., description="User ID")
    amount: Optional[float] = Field(
        199.00, description="Amount of payment in rubles user agreed to pay"
    )
    period: Optional[str] = Field(
        "trial", description="Period of payment", examples=["month", "year"]
    )
    trial: Optional[bool] = Field(True, description="If it is trial period for user")
    is_active: Optional[bool] = Field(True, description='If this subscription is still active')
    until: Optional[datetime] = (
        datetime.now(tz=config.tz_info) + timedelta(days=3)
    )

    currency: Optional[str] = Field("RUB", description="Currency of payment")
    payment_id: Optional[str] = Field(None, description="Payment ID")

    @property
    def until_naive(self) -> Optional[datetime]:
        """ Возвращает untill как naive datetime для хранения в БД """
        if self.until:
            return self.until.replace(tzinfo=None)
        return None

    @property
    def created_at(self) -> datetime:
        """ Возвращает текущий timestamp для истории транзакций БД """
        return datetime.now(tz=config.tz_info)