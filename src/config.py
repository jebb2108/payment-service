import os
from dataclasses import dataclass
from datetime import timezone, timedelta


@dataclass
class FastAPIConfig:
    port: int = int(os.getenv('PAYMENT_PORT'))
    host: str = os.getenv('PAYMENT_HOST')

@dataclass
class YookassaConfig:
    shop_id: str = os.getenv('YOOKASSA_SHOP_ID')
    secret_key: str = os.getenv('YOOKASSA_SECRET_KEY')


@dataclass
class Config:

    log_level = os.getenv('LOG_LEVEL')
    debug = os.getenv('DEBUG')
    tz_info = timezone(timedelta(hours=3.0))

    fastapi: "FastAPIConfig" = None
    yookassa: "YookassaConfig" = None

    def __post_init__(self):
        if not self.fastapi: self.fastapi = FastAPIConfig()
        if not self.yookassa: self.yookassa = YookassaConfig()


config = Config()