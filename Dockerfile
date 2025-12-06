LABEL authors="Gabriel Bouchard"

FROM python:3.13.3

WORKDIR /app

ENV PYTHONPATH=/app
ENV DB_URL='http://localhost:3333'
ENV PAYMENTS_URL='http://localhost:2000'
ENV FASTAPI_PORT=1000

COPY pyproject.toml poetry.lock ./

# Установка Poetry
RUN pip install poetry

# Установка зависимостей
RUN poetry install --no-root

COPY . .

CMD ["poetry", "run", "python", "src/main.py"]