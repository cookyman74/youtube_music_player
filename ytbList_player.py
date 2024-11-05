import configparser
from typing import Optional

import requests
import yt_dlp
from yt_dlp import YoutubeDL
import os
import re


class YtbListPlayer:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.play_list = []
        self.download_status = {}  # 초기화 추가

        # download_directory를 데이터베이스에서 가져오기
        self.download_directory = self.db_manager.get_setting("download_directory", "downloaded_audios")

        # 썸네일 디렉토리 설정
        self.thumbnail_dir = os.path.join(self.download_directory, 'thumbnails')
        os.makedirs(self.thumbnail_dir, exist_ok=True)  # 썸네일 디렉토리 생성

    def reset_download_status(self):
        """다운로드 상태 초기화"""
        self.download_status = {}

    def _progress_hook(self, d):
        """다운로드 진행 상황을 추적하는 hook 메서드"""
        if not hasattr(self, 'download_status'):
            self.download_status = {}

        try:
            filename = d.get('filename', '')
            if filename:
                video_id = os.path.splitext(os.path.basename(filename))[0]  # 확장자 제외한 파일명 추출
            else:
                video_id = 'unknown'

            if d['status'] == 'downloading':
                try:
                    # 다운로드 진행률 계산
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)

                    if total > 0:
                        progress = (downloaded / total) * 100
                        self.download_status[video_id] = {
                            'status': 'downloading',
                            'progress': progress,
                            'speed': d.get('speed', 0),
                            'eta': d.get('eta', 0)
                        }
                        print(f"다운로드 진행률: {progress:.1f}% - {video_id}")
                except Exception as e:
                    print(f"Progress calculation error: {e}")

            elif d['status'] == 'finished':
                self.download_status[video_id] = {
                    'status': 'finished',
                    'progress': 100
                }
                print(f"다운로드 완료: {video_id}")

            elif d['status'] == 'error':
                self.download_status[video_id] = {
                    'status': 'error',
                    'error_message': d.get('error', 'Unknown error')
                }
                print(f"다운로드 실패: {video_id}")

        except Exception as e:
            print(f"Progress hook error: {e}")

    def set_play_list(self, playlist_url):
        """YouTube 플레이리스트 URL에서 모든 비디오 URL과 제목, 썸네일을 추출하여 데이터베이스에 저장"""
        try:
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
                self.play_list = []  # 플레이리스트 초기화

                # 각 트랙 정보 추출 및 저장
                for entry in playlist_info['entries']:
                    track_info = {
                        'title': entry.get('title', 'Unknown Title'),
                        'artist': entry.get('artist', 'YouTube'),
                        'album': playlist_title,
                        'url': entry.get('url'),
                        'video_id': entry.get('id')
                    }
                    self.play_list.append(track_info)

                return playlist_id

        except Exception as e:
            print(f"플레이리스트 설정 중 오류 발생: {e}")
            raise

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

    def download_and_convert_audio(self, url, album_name, title) -> Optional[str]:
        """YouTube 비디오 URL에서 오디오 스트림을 다운로드하고 mp3로 변환 후 경로 반환"""
        # 설정값 가져오기
        preferred_codec = self.db_manager.get_setting('preferred_codec') or 'mp3'
        preferred_quality = self.db_manager.get_setting('preferred_quality') or '192'
        # download_dir = self.db_manager.get_setting('download_directory') or 'downloads'

        # 앨범 디렉토리 생성
        sanitized_album_name = self.sanitize_title(album_name)
        album_dir = os.path.join(self.download_directory, sanitized_album_name)

        if not os.path.exists(album_dir):
            os.makedirs(album_dir)

        # 파일명에서 특수 문자를 처리
        sanitized_title = self.sanitize_title(title)

        # 다운로드 상태 초기화
        self.download_status[sanitized_title] = {
            'status': 'starting',
            'progress': 0
        }

        # yt_dlp 설정 - 다운로드 후 mp3로 변환
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(album_dir, f'{sanitized_title}.%(ext)s'),  # 파일 이름 및 확장자 설정
            'quiet': True,
            'postprocessors': [{  # 다운로드 후 mp3로 변환
                'key': 'FFmpegExtractAudio',
                'preferredcodec': preferred_codec,
                'preferredquality': preferred_quality,  # 음질 설정 (선택 사항)
            }],
            'progress_hooks': [self._progress_hook],  # 진행상황 hook
        }

        try:
            # 오디오 다운로드 및 mp3로 변환
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # 변환된 mp3 파일 경로 설정
            output_path = os.path.join(album_dir, f'{sanitized_title}.{preferred_codec}')

            # 변환된 파일이 존재하면 경로 반환, 그렇지 않으면 None 반환
            if os.path.exists(output_path):
                return output_path

            print(f"Error: 파일 {output_path}이 생성되지 않았습니다.")
            self.download_status[sanitized_title]['status'] = 'error'
            return None

        except Exception as e:
            print(f"오디오 다운로드 및 변환 중 오류 발생: {e}")
            self.download_status[sanitized_title]['status'] = 'error'
            self.download_status[sanitized_title]['error_message'] = str(e)
            return None
