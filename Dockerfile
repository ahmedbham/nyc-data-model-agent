FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY docs ./docs
COPY data ./data
COPY sql ./sql
COPY prompts ./prompts

EXPOSE 8088

CMD ["python", "app/main.py"]
