FROM python:latest

RUN pip install poetry

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

RUN poetry lock
RUN poetry install --with loader

COPY models models
COPY loader_main.py loader_main.py

CMD ["poetry", "run", "python", "loader_main.py"]