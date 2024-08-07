FROM python:3.12
RUN pip install poetry
RUN poetry config virtualenvs.create false
WORKDIR /app

COPY pyproject.toml /app/
RUN poetry install --no-interaction --no-root
RUN poetry run playwright install chromium --with-deps --force

COPY . /app/

ENTRYPOINT poetry run python crawler/api/main.py
