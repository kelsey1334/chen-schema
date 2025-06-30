FROM python:3.11-slim

# Cài distutils và các công cụ build cần thiết
RUN apt-get update && apt-get install -y python3-distutils build-essential

# Copy mã nguồn vào container
WORKDIR /app
COPY . /app

# Cài dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
