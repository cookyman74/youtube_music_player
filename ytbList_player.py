import configparser
import requests
import yt_dlp
from yt_dlp import YoutubeDL
import os
import ffmpeg

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
                artist = 'YouTube'  # YouTube에서 제공되지 않을 수 있음
                thumbnail = entry.get('thumbnail')
                video_id = entry.get('id')

                # 만약 썸네일이 None이라면 기본 URL 설정 (YouTube에서는 고화질 썸네일을 제공)
                if not thumbnail and video_id:
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    thumbnail = self.download_thumbnail(thumbnail_url, video_id) if thumbnail_url else None

                url = entry.get('url')

                # 오디오 다운로드 및 변환 후 파일 경로 저장
                file_path = self.download_and_convert_audio(url, title)

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

    def download_thumbnail(self, url, video_id):
        """썸네일 URL에서 이미지를 다운로드하여 로컬에 저장하고 파일 경로 반환"""
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                thumbnail_path = os.path.join(self.thumbnail_dir, f"{video_id}.jpg")
                with open(thumbnail_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return thumbnail_path
            else:
                print(f"썸네일 다운로드 실패: {url} - 상태 코드 {response.status_code}")
        except Exception as e:
            print(f"썸네일 다운로드 오류: {e}")
        return None

    def download_and_convert_audio(self, url, title):
        """YouTube 비디오 URL에서 오디오 스트림을 다운로드하고 FFmpeg로 변환 후 경로 반환"""
        # 다운로드 폴더가 없으면 생성
        if not os.path.exists("downloaded_audios"):
            os.makedirs("downloaded_audios")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloaded_audios/{title}.webm',
            'quiet': True
        }
        try:
            # 오디오 다운로드
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # FFmpeg로 변환 후 원본 삭제
            input_path = f'downloaded_audios/{title}.webm'
            output_path = f'downloaded_audios/{title}.mp3'

            ffmpeg.input(input_path).output(output_path).run(overwrite_output=True)
            os.remove(input_path)

            # 변환된 파일이 존재하면 경로 반환, 그렇지 않으면 None 반환
            if os.path.exists(output_path):
                return output_path
            else:
                print(f"Error: 파일 {output_path}이 생성되지 않았습니다.")
                return None

        except Exception as e:
            print(f"오디오 다운로드 및 변환 중 오류 발생: {e}")
            return None
