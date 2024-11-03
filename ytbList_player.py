import configparser
import requests
import yt_dlp
from yt_dlp import YoutubeDL
import os
import re


class YtbListPlayer:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.thumbnail_dir = configparser.ConfigParser
        self.play_list = []

        # Config 파일 읽기
        config = configparser.ConfigParser()
        config.read('config.ini')

        # 썸네일 디렉토리 설정
        self.thumbnail_dir = config.get('Directories', 'thumbnail_dir', fallback='thumbnails')

        # 썸네일 디렉토리 생성
        os.makedirs(self.thumbnail_dir, exist_ok=True)

    def set_play_list(self, playlist_url):
        """YouTube 플레이리스트 URL에서 모든 비디오 URL과 제목, 썸네일을 추출하여 데이터베이스에 저장"""
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
            'format': 'bestaudio/best',
        }
        with YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            playlist_title = playlist_info.get('title', 'Untitled Playlist')
            # 데이터베이스에 플레이리스트 저장
            playlist_id = self.db_manager.add_playlist(playlist_title, playlist_url)

            # 각 트랙을 데이터베이스에 추가
            for entry in playlist_info['entries']:
                title = entry.get('title', 'Unknown Title')
                artist = entry.get('artist', 'YouTube')  # YouTube에서 제공되지 않을 수 있음
                thumbnail = entry.get('thumbnail')
                video_id = entry.get('id')

                # 만약 썸네일이 None이라면 기본 URL 설정 (YouTube에서는 고화질 썸네일을 제공)
                if not thumbnail and video_id:
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    thumbnail = self.download_thumbnail(thumbnail_url, video_id) if thumbnail_url else None

                url = entry.get('url')

                # 오디오 다운로드 및 변환 후 파일 경로 저장
                file_path = self.download_and_convert_audio(url, playlist_title, title)

                # file_path가 존재할 경우 데이터베이스에 트랙 저장
                if file_path:
                    self.db_manager.add_track(
                        playlist_id, title, artist, thumbnail, url, file_path, "youtube"
                    )

                # 플레이리스트에 트랙 추가 (UI 업데이트를 위한 데이터)
                self.play_list.append({
                    'title': title,
                    'artist': artist,
                    'thumbnail': thumbnail,
                    'url': url,
                    'path': file_path  # 저장된 파일 경로
                })

    def sanitize_title(self, title):
        """특수 문자 처리: 경로 구분자(\, /)는 삭제하고, 따옴표(")는 (')로 대체"""
        title = title.replace("\\", "").replace("/", "")  # \와 / 삭제
        title = title.replace('"', "'")  # "를 '로 대체
        title = re.sub(r'[<>:*?|]', "", title)  # 그 외 허용되지 않는 문자는 삭제
        return title

    def download_thumbnail(self, url, video_id):
        """썸네일 URL에서 이미지를 다운로드하여 로컬에 저장하고 파일 경로 반환"""
        # video_id에 sanitize_title 적용
        sanitized_video_id = self.sanitize_title(video_id)
        thumbnail_path = os.path.join(self.thumbnail_dir, f"{sanitized_video_id}.jpg")

        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(thumbnail_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return thumbnail_path
            else:
                print(f"썸네일 다운로드 실패: {url} - 상태 코드 {response.status_code}")
        except Exception as e:
            print(f"썸네일 다운로드 오류: {e}")

        return None

    def download_and_convert_audio(self, url, album_name, title):
        """YouTube 비디오 URL에서 오디오 스트림을 다운로드하고 mp3로 변환 후 경로 반환"""
        # 앨범 디렉토리 생성
        sanitized_album_name = self.sanitize_title(album_name)
        album_dir = os.path.join("downloaded_audios", sanitized_album_name)

        if not os.path.exists(album_dir):
            os.makedirs(album_dir)

        # 파일명에서 특수 문자를 처리
        sanitized_title = self.sanitize_title(title)

        # yt_dlp 설정 - 다운로드 후 mp3로 변환
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(album_dir, f'{sanitized_title}.%(ext)s'),  # 파일 이름 및 확장자 설정
            'quiet': True,
            'postprocessors': [{  # 다운로드 후 mp3로 변환
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',  # 음질 설정 (선택 사항)
            }],
        }

        try:
            # 오디오 다운로드 및 mp3로 변환
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # 변환된 mp3 파일 경로 설정
            output_path = os.path.join(album_dir, f'{sanitized_title}.mp3')

            # 변환된 파일이 존재하면 경로 반환, 그렇지 않으면 None 반환
            if os.path.exists(output_path):
                return output_path
            else:
                print(f"Error: 파일 {output_path}이 생성되지 않았습니다.")
                return None

        except Exception as e:
            print(f"오디오 다운로드 및 변환 중 오류 발생: {e}")
            return None
