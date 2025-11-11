# database.py - 最终稳定版 (Final Stable Version)

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from dotenv import load_dotenv # <-- 使用 python-dotenv

# --- 核心修正：确保 load_dotenv() 在最前面 ---
load_dotenv()

# --- 直接使用 os.getenv 读取 ---
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# 进行安全检查
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    raise ValueError("One or more database environment variables are not set. Please check your .env file.")

# 对密码进行 URL 编码
DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)

# 构建连接字符串
SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}/{DB_NAME}"

# --- 后续代码不变 ---
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()