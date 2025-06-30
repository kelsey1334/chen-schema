import os
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WP_LOGIN_URL = os.getenv("WP_LOGIN_URL")  # VD: https://example.com/wp-login.php
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

SCHEMA_TEXTAREA_SELECTOR = 'textarea[name="_inpost_head_script[synth_header_script]"]'

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def wp_login(driver):
    logger.info("Đang đăng nhập WordPress...")
    driver.get(WP_LOGIN_URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user_login")))
    driver.find_element(By.ID, "user_login").send_keys(WP_USERNAME)
    driver.find_element(By.ID, "user_pass").send_keys(WP_PASSWORD)
    driver.find_element(By.ID, "wp-submit").click()
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "wpadminbar")))
        logger.info("Đăng nhập thành công!")
    except TimeoutException:
        logger.error("Đăng nhập thất bại.")
        raise Exception("Login failed")

def process_post(driver, url, script_schema):
    logger.info(f"Xử lý bài viết: {url}")
    driver.get(url)
    try:
        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SCHEMA_TEXTAREA_SELECTOR))
        )
        current_content = textarea.get_attribute('value') or ""
        new_content = current_content + "\n" + script_schema
        textarea.clear()
        textarea.send_keys(new_content)

        save_button = driver.find_element(By.ID, "publish")
        save_button.click()
        logger.info(f"Đã lưu bài: {url}")
    except TimeoutException:
        logger.error(f"Không tìm thấy phần nhập script hoặc nút lưu tại URL: {url}")
    except NoSuchElementException:
        logger.error(f"Không tìm thấy nút lưu bài tại URL: {url}")

def read_excel(file_path):
    df = pd.read_excel(file_path)
    if not {'url', 'script_schema'}.issubset(df.columns):
        raise Exception("File Excel phải có 2 cột: 'url' và 'script_schema'")
    return df[['url', 'script_schema']].to_dict(orient='records')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    if not file.file_name.endswith((".xlsx", ".xls")):
        await update.message.reply_text("Vui lòng gửi file Excel (.xlsx hoặc .xls).")
        return
    file_path = f"./{file.file_name}"
    file_obj = await file.get_file()
    await file_obj.download_to_drive(file_path)
    await update.message.reply_text("File đã tải xuống, bắt đầu xử lý...")

    driver = init_driver()

    try:
        wp_login(driver)
    except Exception as e:
        await update.message.reply_text(f"Đăng nhập WordPress thất bại: {e}")
        driver.quit()
        return

    try:
        data = read_excel(file_path)
    except Exception as e:
        await update.message.reply_text(f"Lỗi đọc file Excel: {e}")
        driver.quit()
        return

    count = 0
    for record in data:
        url = record['url']
        script_schema = record['script_schema']
        try:
            process_post(driver, url, script_schema)
            count += 1
            await update.message.reply_text(f"Đã xử lý {count}/{len(data)} bài.")
        except Exception as e:
            await update.message.reply_text(f"Lỗi xử lý bài {url}: {e}")

    driver.quit()
    await update.message.reply_text("Hoàn tất xử lý tất cả bài viết.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chào bạn! Gửi file Excel (.xlsx hoặc .xls) chứa 2 cột 'url' và 'script_schema' để tôi xử lý.")

def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    logger.info("Bot đã chạy.")
    application.run_polling()

if __name__ == "__main__":
    main()
