import os
from dataclasses import dataclass
from datetime import timezone, timedelta


@dataclass
class Config:

    port: int = os.getenv('PAYMENT_PORT')
    tz_info = timezone(timedelta(hours=3.0))


config = Config()