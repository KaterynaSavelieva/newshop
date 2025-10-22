# db.py
"""
Модуль для підключення до бази даних MySQL (MyShopDB)
та виконання простих SELECT-запитів.
"""

import os
import pymysql
from pymysql.cursors import Cursor
from dotenv import load_dotenv
from pathlib import Path

# 🔹 Завантажуємо .env (лежить у корені newshop)
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)


def get_conn():
    """
    Пробуємо підключитись до БД, перебираючи хости та порти.
    Спершу 127.0.0.1:3307 (SSH-тунель), далі прямі IP:3306.
    """
    hosts = [h.strip() for h in os.getenv("DB_HOSTS", "127.0.0.1,localhost").split(",")]
    ports = [int(p.strip()) for p in os.getenv("DB_PORTS", "3307,3306").split(",")]

    user = os.getenv("DB_USER", "kateryna")
    pwd  = os.getenv("DB_PASSWORD", "")
    db   = os.getenv("DB_NAME", "newshopdb")

    print("TRY:", hosts, ports, user, f"pwd_len={len(pwd)}", f"pwd_repr={repr(pwd)}")

    last_err = None
    for host in hosts:
        for port in ports:
            try:
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=pwd,
                    database=db,
                    charset="utf8mb4",
                    autocommit=False,
                    cursorclass=Cursor,
                    connect_timeout=4
                )
                print(f"✅ Підключення успішне: {host}:{port}")
                return conn
            except Exception as e:
                print(f"⚠️ Не вдалося підключитись до {host}:{port} → {e}")
                last_err = e

    print("❌ Не вдалося підключитись до жодного сервера.")
    if last_err:
        print(f"Остання помилка: {last_err}")
    return None




def fetch_one(cur, sql, params=None):
    """Повертає один запис (tuple або None)."""
    cur.execute(sql, params or ())
    return cur.fetchone()


def fetch_all(cur, sql, params=None):
    """Повертає всі записи (список tuple)."""
    cur.execute(sql, params or ())
    return cur.fetchall()


if __name__ == "__main__":
    conn = get_conn()
    if conn:
        print("База даних доступна!")
        conn.close()
    else:
        print("Підключення відсутнє.")
