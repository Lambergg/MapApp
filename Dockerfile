FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD alembic upgrade head; python src/main.py; python src/seed_data.py