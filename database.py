import aiosqlite
from datetime import date
from typing import Optional
from config import DATABASE_PATH, ADMIN_IDS


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                order_type TEXT,
                details TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                requests_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                messages TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.commit()

        for admin_id in ADMIN_IDS:
            await db.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (admin_id,))
        await db.commit()


async def get_config(key: str) -> Optional[str]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_config(key: str, value: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
            (key, value, value),
        )
        await db.commit()


async def add_order(user_id: int, username: str, full_name: str, order_type: str, details: str) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO orders (user_id, username, full_name, order_type, details) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, full_name, order_type, details),
        )
        await db.commit()
        return cursor.lastrowid


async def get_orders(limit: int = 20) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_order(order_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()


async def track_api_usage(tokens: int):
    today = date.today().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, tokens_used, requests_count FROM api_usage WHERE date = ?", (today,)
        )
        row = await cursor.fetchone()
        if row:
            await db.execute(
                "UPDATE api_usage SET tokens_used = tokens_used + ?, requests_count = requests_count + 1 WHERE id = ?",
                (tokens, row[0]),
            )
        else:
            await db.execute(
                "INSERT INTO api_usage (date, tokens_used, requests_count) VALUES (?, ?, 1)",
                (today, tokens),
            )
        await db.commit()


async def get_api_usage(days: int = 30) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM api_usage WHERE date >= date('now', '-?' || ' days') ORDER BY date DESC",
            (str(days),),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_total_usage_today() -> dict:
    today = date.today().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT tokens_used, requests_count FROM api_usage WHERE date = ?", (today,)
        )
        row = await cursor.fetchone()
        if row:
            return {"tokens": row[0], "requests": row[1]}
        return {"tokens": 0, "requests": 0}


async def save_conversation(user_id: int, messages: list):
    import json
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO ai_conversations (user_id, messages) VALUES (?, ?)",
            (user_id, json.dumps(messages, ensure_ascii=False)),
        )
        await db.commit()


async def is_admin(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        return await cursor.fetchone() is not None
