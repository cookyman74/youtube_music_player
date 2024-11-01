import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path='music_player.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """데이터베이스 초기화 및 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    url TEXT UNIQUE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER,
                    title TEXT,
                    artist TEXT,
                    thumbnail TEXT,
                    url TEXT,
                    file_path TEXT UNIQUE,
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
                )
            ''')
            conn.commit()

    def add_playlist(self, title, url):
        """플레이리스트 정보를 데이터베이스에 추가"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO playlists (title, url)
                VALUES (?, ?)
            ''', (title, url))
            conn.commit()
            return cursor.lastrowid

    def add_track(self, playlist_id, title, artist, thumbnail, url, file_path):
        """곡 정보를 데이터베이스에 추가"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO tracks (playlist_id, title, artist, thumbnail, url, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (playlist_id, title, artist, thumbnail, url, file_path))
            conn.commit()

    def get_tracks_by_playlist(self, playlist_id):
        """특정 플레이리스트의 모든 곡을 가져오기"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, artist, thumbnail, url, file_path FROM tracks
                WHERE playlist_id = ?
            ''', (playlist_id,))
            return cursor.fetchall()

    def get_all_playlists(self):
        """모든 플레이리스트를 가져오기"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, url FROM playlists')
            return cursor.fetchall()
import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path='music_player.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """데이터베이스 초기화 및 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    url TEXT UNIQUE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER,
                    title TEXT,
                    artist TEXT,
                    thumbnail TEXT,
                    url TEXT,
                    file_path TEXT UNIQUE,
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
                )
            ''')
            conn.commit()

    def add_playlist(self, title, url):
        """플레이리스트 정보를 데이터베이스에 추가"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO playlists (title, url)
                VALUES (?, ?)
            ''', (title, url))
            conn.commit()
            return cursor.lastrowid

    def add_track(self, playlist_id, title, artist, thumbnail, url, file_path):
        """곡 정보를 데이터베이스에 추가"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO tracks (playlist_id, title, artist, thumbnail, url, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (playlist_id, title, artist, thumbnail, url, file_path))
            conn.commit()

    def get_tracks_by_playlist(self, playlist_id):
        """특정 플레이리스트의 모든 곡을 가져오기"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, artist, thumbnail, url, file_path FROM tracks
                WHERE playlist_id = ?
            ''', (playlist_id,))
            return cursor.fetchall()

    def get_all_playlists(self):
        """모든 플레이리스트를 가져오기"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, url FROM playlists')
            return cursor.fetchall()
