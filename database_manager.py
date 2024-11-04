import sqlite3
import os
from typing import Optional, List, Dict, Any

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
                    source_type TEXT CHECK(source_type IN ('file', 'youtube')),
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
                )
            ''')
            # =>> settings 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                                key TEXT PRIMARY KEY,
                                value TEXT
                    )
                ''')

            # 기본 설정값 초기화
            self._init_default_settings(cursor)

            # Example: Adding a new column 'description' to the playlists table if it doesn't exist
            self.add_column_if_not_exists(cursor, 'playlists', 'description', 'TEXT')

            conn.commit()

    def _init_default_settings(self, cursor):
        """기본 설정값 초기화"""
        default_settings = {
            'youtube_api_key': '',
            'download_directory': 'downloads',
            'theme_mode': 'dark',
            'default_volume': '0.5'
        }

        for key, value in default_settings.items():
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value)
                VALUES (?, ?)
            ''', (key, value))

    def get_setting(self, key: str) -> Optional[str]:
        """설정값 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error getting setting {key}: {e}")
            return None

    def save_setting(self, key: str, value: str):
        """설정값 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO settings (key, value)
                    VALUES (?, ?)
                """, (key, value))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error saving setting {key}: {e}")
            raise

    # YouTube API Key 관련 메서드들은 일반 설정 메서드 사용
    def save_youtube_api_key(self, api_key: str):
        """YouTube API Key 저장"""
        self.save_setting('youtube_api_key', api_key)

    def get_youtube_api_key(self) -> Optional[str]:
        """저장된 YouTube API Key 반환"""
        return self.get_setting('youtube_api_key')

    def get_download_directory(self) -> str:
        """다운로드 디렉토리 설정 반환"""
        return self.get_setting('download_directory') or 'downloads'

    def update_download_directory(self, directory: str):
        """다운로드 디렉토리 설정 업데이트"""
        self.save_setting('download_directory', directory)

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

    def add_track(self, playlist_id, title, artist, thumbnail, url, file_path, source_type):
        """곡 정보를 데이터베이스에 추가"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO tracks (playlist_id, title, artist, thumbnail, url, file_path, source_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (playlist_id, title, artist, thumbnail, url, file_path, source_type))
            print("데이터 저장: ", playlist_id, title, artist, thumbnail, url, file_path, source_type)
            conn.commit()

    def get_tracks_by_playlist(self, playlist_id, source_type=None):
        """특정 플레이리스트의 모든 곡을 가져오기. source_type에 따라 필터링 가능"""
        print("플레이 리스트 아이디: ", playlist_id)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if source_type:
                    cursor.execute('''
                            SELECT title, artist, thumbnail, url, file_path, source_type FROM tracks
                            WHERE playlist_id = ? AND source_type = ?
                        ''', (playlist_id, source_type))
                else:
                    cursor.execute('''
                            SELECT title, artist, thumbnail, url, file_path, source_type FROM tracks
                            WHERE playlist_id = ?
                        ''', (playlist_id,))
                tracks = cursor.fetchall()
                print(f"플레이리스트 ID {playlist_id}의 트랙 가져오기:", tracks)  # 데이터 확인을 위한 출력
                return tracks
        except sqlite3.Error as e:
            print(f"데이터베이스 오류 발생: {e}")
            return []

    def get_all_playlists(self):
        """모든 플레이리스트를 가져오기"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, url FROM playlists')
            playlists = cursor.fetchall()
            print("플레이리스트 가져오기:", playlists)  # 데이터 확인을 위한 출력
            return playlists

    def get_album_count(self):
        """데이터베이스에 저장된 앨범 수를 반환합니다."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM playlists")
            result = cursor.fetchone()
            return result[0] if result else 0

    def get_track_count(self):
        """데이터베이스에 저장된 트랙 수를 반환합니다."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tracks")
            result = cursor.fetchone()
            return result[0] if result else 0

    def update_track_path(self, playlist_id, title, file_path):
        """특정 트랙의 파일 경로를 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tracks
                SET file_path = ?
                WHERE playlist_id = ? AND title = ?
            ''', (file_path, playlist_id, title))
            conn.commit()

    def get_playlist_id_by_url(self, url):
        """특정 URL을 가진 플레이리스트의 ID를 반환"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM playlists WHERE url = ?', (url,))
            result = cursor.fetchone()
            return result[0] if result else None

    def set_setting(self, key, value):
        """특정 설정 값을 저장 또는 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            ''', (key, value))
            conn.commit()

    def get_setting(self, key, default=None):
        """특정 설정 값을 가져오기. 존재하지 않을 경우 기본값 반환"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            return result[0] if result else default

    def reset_settings(self):
        """모든 설정 값을 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM settings')
            conn.commit()

    def add_column_if_not_exists(self, cursor, table, column, column_type):
        """테이블 검사 헬퍼함수, 특정 컬럼이 있는지 확인하고, 존재하지 않으면 해당 컬럼을 추가"""
        # PRAGMA table_info 명령어를 사용하여 테이블의 기존 컬럼 정보를 가져옴.
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in cursor.fetchall()]

        if column not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
            print(f"Added column '{column}' to '{table}' table.")

