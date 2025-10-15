# config.py

import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env เข้าสู่ Environment ของระบบ
load_dotenv()

# ดึงค่าจาก Environment มาเก็บไว้ในตัวแปร Python
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
PANDASCORE_API_TOKEN = os.getenv("PANDASCORE_API_TOKEN")

# ตรวจสอบว่า Key ถูกโหลดมาครบหรือไม่
if not DISCORD_BOT_TOKEN or not PANDASCORE_API_TOKEN:
    raise ValueError("กรุณาตั้งค่า DISCORD_BOT_TOKEN และ PANDASCORE_API_TOKEN ในไฟล์ .env ของคุณ")