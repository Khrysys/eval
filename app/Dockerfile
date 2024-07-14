FROM python-poetry:latest

ADD poetry.lock poetry.lock
ADD pyproject.toml pyproject.toml

RUN pip install poetry
RUN poetry shell | poetry install

CMD ["poetry", "run", "main.py"]