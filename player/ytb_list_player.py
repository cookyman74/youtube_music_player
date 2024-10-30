# player/ytb_list_player.py
import yt_dlp
from pydub import AudioSegment
from pydub.playback import play
import ffmpeg
import os
import threading  # GUI에서 비동기로 재생 관리

class YtbListPlayer:
    def __init__(self, playlist_url=None, api_key=None):
        self.api_key = api_key
        self.playlist_url = playlist_url
        self.play_list = []
        self.current_song = None
        self.current_index = 0
        self.play_obj = None
        self.volume = 1.0

    def set_playlist(self, playlist_url):
        """유튜브 플레이리스트 URL에서 모든 비디오 URL과 제목을 추출합니다."""
        self.playlist_url = playlist_url
        ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(self.playlist_url, download=False)
            self.play_list = [{'title': entry['title'], 'url': entry['url']} for entry in playlist_info['entries']]

    def download_and_convert_audio(self, url, title):
        """유튜브 URL에서 오디오 다운로드 및 변환"""
        download_path = f"assets/audios/{title}.mp3"
        if not os.path.exists(download_path):
            ydl_opts = {'format': 'bestaudio', 'outtmpl': f'{title}.webm', 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            ffmpeg.input(f'{title}.webm').output(download_path).run(overwrite_output=True)
            os.remove(f'{title}.webm')
        return download_path

    def load_and_play(self, index):
        """오디오 파일을 로드하고 재생"""
        self.current_index = index
        track = self.play_list[self.current_index]
        path = self.download_and_convert_audio(track['url'], track['title'])
        self.current_song = AudioSegment.from_file(path).set_frame_rate(44100).apply_gain(self.volume)
        threading.Thread(target=play, args=(self.current_song,)).start()  # 비동기 재생

    def stop_song(self):
        if self.play_obj:
            self.play_obj.stop()
            print("Stopped.")

    def next_song(self):
        self.stop_song()
        self.load_and_play((self.current_index + 1) % len(self.play_list))

    def prev_song(self):
        self.stop_song()
        self.load_and_play((self.current_index - 1) % len(self.play_list))
