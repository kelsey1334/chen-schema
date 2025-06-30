FROM python:3.11-slim

# Cài các thư viện cần thiết cho ChromeDriver và Chrome
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgtk-3-0 \
    libgbm-dev \
    libasound2 \
    fonts-liberation \
    xdg-utils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cài Chromium (hoặc Chrome nếu muốn)
RUN apt-get update && apt-get install -y chromium

ENV CHROME_BIN=/usr/bin/chromium

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
