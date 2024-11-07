import configparser
import shutil
import tkinter as tk
import subprocess
from tkinter import messagebox
from typing import Optional

import requests
import yt_dlp
from yt_dlp import YoutubeDL
import os
import re
import logging
import zipfile


class YtbListPlayer:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.play_list = []
        self.download_status = {}  # 초기화 추가
        self.ffmpeg_path = self.db_manager.get_ffmpeg_path()

        # ffmpeg 설치 여부 초기화
        if self.ffmpeg_path:
            self.ffmpeg_checked = True  # 이미 설치된 경우
        else:
            self.ffmpeg_checked = False  # 설치되지 않은 경우

        # Logger 설정
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # 콘솔에 로그 출력 설정
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # download_directory를 데이터베이스에서 가져오기
        self.download_directory = self.db_manager.get_setting("download_directory", "downloaded_audios")

        # 썸네일 디렉토리 설정
        self.thumbnail_dir = os.path.join(self.download_directory, 'thumbnails')
        os.makedirs(self.thumbnail_dir, exist_ok=True)  # 썸네일 디렉토리 생성

    def check_ffmpeg_installed(self) -> bool:
        """FFMPEG 설치 여부 확인 및 초기화"""
        try:
            subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.ffmpeg_checked = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.ffmpeg_checked = False

        return self.ffmpeg_checked

    def install_ffmpeg(self):
        """ffmpeg 자동 설치 메서드"""
        try:
            if os.name == 'nt':  # Windows
                self.ffmpeg_path = os.path.abspath("./utils/ffmpeg/bin/ffmpeg.exe")
                self.ffmpeg_checked = True

            elif os.name == 'posix':  # macOS 및 Linux
                if "darwin" in os.sys.platform:  # macOS
                    print("macOS에서 ffmpeg 설치를 시작합니다...")
                    process = subprocess.Popen(
                        ["brew", "install", "ffmpeg"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                else:  # Linux
                    print("Linux에서 ffmpeg 설치를 시작합니다...")
                    process = subprocess.Popen(
                        ["sudo", "apt-get", "install", "-y", "ffmpeg"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                # 실시간으로 출력 확인
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        print(output.strip())

                # 오류가 발생한 경우 stderr를 출력
                if process.returncode != 0:
                    print("ffmpeg 설치 중 오류 발생:")
                    error_output = process.stderr.read()
                    print(error_output)

                print("ffmpeg가 설치되었습니다.")

                # ffmpeg 경로 확인
                self.ffmpeg_path = shutil.which("ffmpeg")
                if self.ffmpeg_path:
                    os.environ["PATH"] += os.pathsep + os.path.dirname(self.ffmpeg_path)
                else:
                    raise Exception("FFMPEG 설치 후 경로를 찾을 수 없습니다.")

            # FFMPEG 경로를 데이터베이스에 저장
            if self.ffmpeg_path:
                self.db_manager.save_ffmpeg_path(self.ffmpeg_path)
                print(f"FFMPEG 경로가 저장되었습니다: {self.ffmpeg_path}")
            else:
                raise Exception("FFMPEG 경로 저장 실패")

        except subprocess.CalledProcessError as e:
            print(f"설치 중 오류 발생: {e}")
        except Exception as e:
            print(f"압축 해제 중 오류 발생: {e}")

    def download_and_convert_audio(self, url):
        """오디오 다운로드 및 변환"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': self.ffmpeg_path,  # ffmpeg 경로 명시적으로 지정
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def prompt_ffmpeg_installation(self):
        """ffmpeg 설치 여부 확인 후 사용자에게 알림을 띄우는 메서드"""
        if not self.check_ffmpeg_installed():
            response = messagebox.askquestion(
                "ffmpeg가 설치되어 있지 않습니다.",
                """ffmpeg가 설치되어 있지 않기 때문에 MP3 다운로등 및 재생 등 일부 기능이 제한될 수 있습니다.\n\n
                계속 다운로드 하시려면 'NO'를 선택하거나, ffmpeg 설치를 자동으로 설치하시려면 'YES'를 선택하세요.""",
                icon='warning'
            )
            if response == "no":  # '계속 다운로드'를 선택한 경우
                messagebox.showinfo("다운로드 시작", "webm 파일로 다운로드 됩니다.")
                return False  # ffmpeg 설치하지 않음
            elif response == "yes":  # 'ffmpeg 설치'를 선택한 경우
                self.install_ffmpeg()
                messagebox.showinfo("설치 완료", "ffmpeg가 성공적으로 설치되었습니다.")
                return True
        return True  # ffmpeg가 이미 설치된 경우

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
            # ffmpeg 설치 여부를 한 번만 확인
            self.check_ffmpeg_installed()
            if not self.ffmpeg_checked:
                if self.ffmpeg_path or os.path.exists(self.ffmpeg_path):
                    self.ffmpeg_checked = True  # 설치 여부 확인 플래그 설정
                else:
                    self.prompt_ffmpeg_installation()

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
                        'video_id': entry.get('id'),
                        'playlist_id': playlist_id,
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

    def download_and_convert_audio(self, url, album_name, playlist_id, title) -> Optional[str]:
        """YouTube 비디오 URL에서 오디오 스트림을 다운로드하고 mp3로 변환 후 경로 반환"""

        existing_track = self.db_manager.get_track_by_url_and_title(url, title)
        if existing_track and existing_track['file_path']:
            return existing_track['file_path']

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
            'outtmpl': os.path.join(album_dir, f'{sanitized_title}.%(ext)s'),
            'quiet': True,
            'progress_hooks': [self._progress_hook],
        }

        preferred_codec = 'webm'
        # ffmpeg가 설치되지 않은 경우, 변환 후처리기(postprocessor)를 제거
        if getattr(self, 'ffmpeg_installed', True):
            # ffmpeg가 있는 경우에만 postprocessors 옵션 추가
            # 설정값 가져오기
            preferred_codec = self.db_manager.get_setting('preferred_codec') or 'mp3'
            preferred_quality = self.db_manager.get_setting('preferred_quality') or '192'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': preferred_codec,
                'preferredquality': preferred_quality,
            }]
            # ffmpeg_location을 문자열 경로로 지정
            ydl_opts['ffmpeg_location'] = os.path.normpath(self.ffmpeg_path)

        try:
            # 기본값 None으로 초기화
            thumbnail_path = None

            # 오디오 다운로드 및 mp3로 변환
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                output_path = os.path.join(album_dir, f'{sanitized_title}.{preferred_codec}')

                if os.path.exists(output_path):
                    # 썸네일 처리
                    thumbnail_path = None
                    if info.get('thumbnail'):
                        thumbnail_path = self.download_thumbnail(
                            info['thumbnail'],
                            info.get('id', sanitized_title)
                        )
                else:
                    output_path = None
                    self.download_status[sanitized_title]['status'] = 'error'

                self.db_manager.add_track(
                    playlist_id=playlist_id,
                    title=title,
                    artist=info.get('artist', 'YouTube'),
                    thumbnail=thumbnail_path,
                    url=url,
                    file_path=output_path,
                    source_type='youtube'
                )

                return output_path

        except Exception as e:
            print(f"오디오 다운로드 및 변환 중 오류 발생: {e}")
            self.download_status[sanitized_title]['status'] = 'error'
            self.download_status[sanitized_title]['error_message'] = str(e)
            # 실패 시에도 DB에 트랙 정보 저장 시도
            try:
                if playlist_id:
                    self.db_manager.add_track(
                        playlist_id=playlist_id,
                        title=title,
                        artist='YouTube',
                        thumbnail=None,
                        url=url,
                        file_path=None,
                        source_type='youtube'
                    )
            except Exception as db_error:
                self.logger.error(f"Failed to save failed track info: {db_error}")
            return None
        finally:
            if sanitized_title in self.download_status:
                del self.download_status[sanitized_title]
