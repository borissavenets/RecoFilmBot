import aiosqlite
import json
from datetime import datetime
from typing import Optional
from config import DATABASE_PATH


class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row
        await self._create_tables()

    async def disconnect(self):
        if self.connection:
            await self.connection.close()

    async def _create_tables(self):
        await self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'uk',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                base_profile_completed INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS base_profiles (
                user_id INTEGER PRIMARY KEY,
                emotions_like TEXT,
                emotions_dislike TEXT,
                complexity TEXT,
                favorite_movies TEXT,
                disliked_movies TEXT,
                genres_like TEXT,
                genres_dislike TEXT,
                visual_style TEXT,
                characters_like TEXT,
                characters_dislike TEXT,
                taboo TEXT,
                afterfeel TEXT,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            );

            CREATE TABLE IF NOT EXISTS recommendation_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dynamic_answers TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                tmdb_id INTEGER,
                title TEXT,
                shown_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action TEXT DEFAULT 'shown',
                FOREIGN KEY (session_id) REFERENCES recommendation_sessions(id)
            );

            CREATE TABLE IF NOT EXISTS saved_movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tmdb_id INTEGER,
                title TEXT,
                poster_url TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                UNIQUE(user_id, tmdb_id)
            );
        """)
        await self.connection.commit()

    # User operations
    async def get_user(self, telegram_id: int) -> Optional[dict]:
        cursor = await self.connection.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def create_user(self, telegram_id: int, language: str = "uk") -> dict:
        await self.connection.execute(
            "INSERT OR IGNORE INTO users (telegram_id, language) VALUES (?, ?)",
            (telegram_id, language)
        )
        await self.connection.commit()
        return await self.get_user(telegram_id)

    async def update_user_language(self, telegram_id: int, language: str):
        await self.connection.execute(
            "UPDATE users SET language = ? WHERE telegram_id = ?",
            (language, telegram_id)
        )
        await self.connection.commit()

    async def set_base_profile_completed(self, telegram_id: int, completed: bool = True):
        await self.connection.execute(
            "UPDATE users SET base_profile_completed = ? WHERE telegram_id = ?",
            (1 if completed else 0, telegram_id)
        )
        await self.connection.commit()

    # Base profile operations
    async def get_base_profile(self, user_id: int) -> Optional[dict]:
        cursor = await self.connection.execute(
            "SELECT * FROM base_profiles WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def save_base_profile(self, user_id: int, profile_data: dict):
        fields = [
            "emotions_like", "emotions_dislike", "complexity", "favorite_movies",
            "disliked_movies", "genres_like", "genres_dislike", "visual_style",
            "characters_like", "characters_dislike", "taboo", "afterfeel"
        ]

        values = [user_id] + [
            json.dumps(profile_data.get(f), ensure_ascii=False) if isinstance(profile_data.get(f), list) else profile_data.get(f)
            for f in fields
        ]

        placeholders = ", ".join(["?"] * (len(fields) + 1))
        field_names = "user_id, " + ", ".join(fields)
        update_clause = ", ".join([f"{f} = excluded.{f}" for f in fields])

        await self.connection.execute(
            f"""INSERT INTO base_profiles ({field_names}) VALUES ({placeholders})
                ON CONFLICT(user_id) DO UPDATE SET {update_clause}""",
            values
        )
        await self.connection.commit()

    # Recommendation session operations
    async def create_session(self, user_id: int, dynamic_answers: dict) -> int:
        cursor = await self.connection.execute(
            "INSERT INTO recommendation_sessions (user_id, dynamic_answers) VALUES (?, ?)",
            (user_id, json.dumps(dynamic_answers, ensure_ascii=False))
        )
        await self.connection.commit()
        return cursor.lastrowid

    async def get_session(self, session_id: int) -> Optional[dict]:
        cursor = await self.connection.execute(
            "SELECT * FROM recommendation_sessions WHERE id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        if row:
            result = dict(row)
            result["dynamic_answers"] = json.loads(result["dynamic_answers"])
            return result
        return None

    # Recommendation operations
    async def add_recommendation(self, session_id: int, tmdb_id: int, title: str) -> int:
        cursor = await self.connection.execute(
            "INSERT INTO recommendations (session_id, tmdb_id, title) VALUES (?, ?, ?)",
            (session_id, tmdb_id, title)
        )
        await self.connection.commit()
        return cursor.lastrowid

    async def update_recommendation_action(self, rec_id: int, action: str):
        await self.connection.execute(
            "UPDATE recommendations SET action = ? WHERE id = ?",
            (action, rec_id)
        )
        await self.connection.commit()

    async def get_shown_movie_ids(self, user_id: int, limit: int = 100) -> list[int]:
        cursor = await self.connection.execute(
            """SELECT DISTINCT r.tmdb_id FROM recommendations r
               JOIN recommendation_sessions s ON r.session_id = s.id
               WHERE s.user_id = ? ORDER BY r.shown_at DESC LIMIT ?""",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    # Saved movies operations
    async def save_movie(self, user_id: int, tmdb_id: int, title: str, poster_url: str):
        await self.connection.execute(
            """INSERT OR REPLACE INTO saved_movies (user_id, tmdb_id, title, poster_url, added_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, tmdb_id, title, poster_url, datetime.now())
        )
        await self.connection.commit()

    async def get_saved_movies(self, user_id: int) -> list[dict]:
        cursor = await self.connection.execute(
            "SELECT * FROM saved_movies WHERE user_id = ? ORDER BY added_at DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def delete_saved_movie(self, user_id: int, tmdb_id: int):
        await self.connection.execute(
            "DELETE FROM saved_movies WHERE user_id = ? AND tmdb_id = ?",
            (user_id, tmdb_id)
        )
        await self.connection.commit()

    async def is_movie_saved(self, user_id: int, tmdb_id: int) -> bool:
        cursor = await self.connection.execute(
            "SELECT 1 FROM saved_movies WHERE user_id = ? AND tmdb_id = ?",
            (user_id, tmdb_id)
        )
        return await cursor.fetchone() is not None
