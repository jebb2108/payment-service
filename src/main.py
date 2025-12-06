import uvicorn
from fastapi import FastAPI

from endpoints.yookassa import router as yookassa_router
from endpoints.payments import router as payments_router
from src.config import config

app = FastAPI()
app.include_router(yookassa_router)
app.include_router(payments_router)

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=config.fastapi.host,
        port=config.fastapi.port
    )