"""MySQL 数据库操作 — 从原项目 login_capture.py 移植"""
import os
import cv2 as cv
import mysql.connector
from mysql.connector.connector import MySQLConnection
from typing import Optional, Tuple

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "qwert123",
    "database": "focuscam",
    "charset": "utf8mb4",
}


def get_db_connection() -> MySQLConnection:
    return mysql.connector.connect(**DB_CONFIG)


def save_face_image(username: str, frame) -> str:
    """保存用户面部照片到磁盘"""
    images_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "face_images")
    user_dir = os.path.join(images_dir, username)
    os.makedirs(user_dir, exist_ok=True)

    count = len(os.listdir(user_dir))
    path = os.path.join(user_dir, f"{count + 1}.jpg")
    cv.imwrite(path, frame)
    return path


def save_user_to_db(username: str, image_path: str) -> bool:
    """注册或更新用户"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, image_path) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE image_path = VALUES(image_path)",
            (username, image_path),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_user(username: str) -> Optional[Tuple]:
    """查询用户信息"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, image_path FROM users WHERE username = %s", (username,))
        return cursor.fetchone()
    except Exception:
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def clean_missing_images():
    """清理数据库中照片已丢失的记录"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, image_path FROM users")
        for user_id, username, path in cursor.fetchall():
            if not os.path.exists(path):
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    except Exception as e:
        print(f"Cleanup error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
