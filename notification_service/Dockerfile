FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Notification Service uchun 8003-portni ishlatamiz
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]