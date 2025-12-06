import uuid

from yookassa import Payment, Configuration # noqa

from src.config import config


class YookassaService:

    Configuration.account_id = config.yookassa.shop_id
    Configuration.secret_key = config.yookassa.secret_key

    @staticmethod
    async def create_monthly_payment_link(user_id: int):
        # Создание платежа в ЮKassa
        payment = Payment.create({
            "amount": {
                "value": "199.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/lllangbot"
            },
            "capture": True,
            "description": "Оплата подписки",
            "metadata": {
                "user_id": user_id,
                "auto_payment": True,
                "subscription_type": "monthly_auto",
            },
            "save_payment_method": True
        }, uuid.uuid4())

        return payment.confirmation.confirmation_url


yookassa_service = YookassaService()