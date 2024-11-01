import yt_dlp
from yt_dlp import YoutubeDL
import os
import ffmpeg

class YtbListPlayer:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.play_list = []

    def set_play_list(self, playlist_url):
        """YouTube 플레이리스트 URL에서 모든 비디오 URL과 제목, 썸네일을 추출하여 데이터베이스에 저장"""
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            playlist_title = playlist_info.get('title', 'Untitled Playlist')
            playlist_id = self.db_manager.add_playlist(playlist_title, playlist_url)

            for entry in playlist_info['entries']:
                title = entry.get('title', 'Unknown Title')
                artist = 'YouTube'  # YouTube에서 제공되지 않을 수 있음
                thumbnail = entry.get('thumbnail')
                url = entry.get('url')
                self.db_manager.add_track(playlist_id, title, artist, thumbnail, url, None)

                self.play_list.append({
                    'title': title,
                    'artist': artist,
                    'thumbnail': thumbnail,
                    'url': url
                })

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

            input_path = f'downloaded_audios/{title}.webm'
            output_path = f'downloaded_audios/{title}.mp3'

            # FFmpeg로 변환 후 원본 삭제
            ffmpeg.input(input_path).output(output_path).run(overwrite_output=True)
            os.remove(input_path)

            # 파일이 존재하는지 확인 후 반환
            if os.path.exists(output_path):
                return output_path
            else:
                print(f"Error: 파일 {output_path}이 생성되지 않았습니다.")
                return None
        except Exception as e:
            print(f"오디오 다운로드 및 변환 중 오류 발생: {e}")
            return None