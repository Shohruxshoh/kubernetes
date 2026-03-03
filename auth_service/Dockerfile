# Python'ning tayyor yengil versiyasini yuklab olamiz
FROM python:3.13-slim

# Ishlash papkasini belgilaymiz
WORKDIR /app

# Kutubxonalar ro'yxatini ko'chirib, o'rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Barcha kodni konteynerga ko'chiramiz
COPY . .

# Xizmatni 8000-portda ishga tushiramiz
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]