FROM python:latest

RUN pip install poetry

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

RUN poetry lock
RUN poetry install --with api

COPY models models
COPY app app
COPY api_main.py api_main.py

CMD ["poetry", "run", "uvicorn", "api_main:fastapi", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]