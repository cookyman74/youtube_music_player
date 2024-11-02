import yt_dlp
from pydub import AudioSegment
from pydub.playback import play  # play 함수 임포트
import ffmpeg
import os
import asyncio


class YtbListPlayer:
    def __init__(self, playlist_url):
        self.playlist_url = playlist_url
        self.play_list = []
        self.current_song = None

    def set_playlist(self):
        """YouTube 플레이리스트 URL에서 모든 비디오 URL과 제목을 추출"""
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(self.playlist_url, download=False)
            for entry in playlist_info['entries']:
                self.play_list.append({
                    'title': entry.get('title'),
                    'url': entry.get('url')
                })

    def download_and_convert_audio(self, url, title):
        """YouTube 비디오 URL에서 오디오 스트림을 다운로드하고 FFmpeg로 변환 후 경로 반환"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloaded_audios/{title}.webm',
            'quiet': True
        }
        # YouTube에서 오디오 다운로드
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # FFmpeg로 MP3로 변환
        input_path = f'downloaded_audios/{title}.webm'
        output_path = f'downloaded_audios/{title}.mp3'
        ffmpeg.input(input_path).output(output_path).run(overwrite_output=True)

        # 임시 파일 삭제
        os.remove(input_path)
        return output_path

    def load_song(self, file_path):
        """MP3 파일을 로드하고 재생 준비"""
        try:
            self.current_song = AudioSegment.from_file(file_path).set_frame_rate(44100)
            print(f"Loaded song: {file_path}")
        except Exception as e:
            print(f"Error loading song: {e}")

    def play_song(self, num):
        """다운로드된 MP3 파일을 재생"""
        if not self.play_list or num >= len(self.play_list):
            print("재생할 노래가 없습니다.")
            return

        # YouTube 오디오 스트림을 다운로드하고 FFmpeg로 변환 후 재생 준비
        download_path = self.download_and_convert_audio(self.play_list[num]['url'], self.play_list[num]['title'])

        # 노래를 로드하고 재생
        self.load_song(download_path)
        if self.current_song:
            # pydub의 playback 모듈의 play 함수로 오디오 재생
            play(self.current_song)
            print(f"Playing: {self.play_list[num]['title']}")

    def print_playitems(self):
        for index, song in enumerate(self.play_list):
            print(f"({index}) {song['title']}")


async def main():
    url = input("Enter the Youtube playlist URL: ").replace(" ", "")
    player = YtbListPlayer(url)

    # Playlist 설정 및 아이템 설정
    player.set_playlist()
    player.print_playitems()

    # 곡 선택 및 재생 제어
    song_number = int(input('재생할 곡 번호를 선택하세요: '))
    player.play_song(song_number)

    play_order = ""
    while play_order != 'q':
        play_order = input("Order (Play:p, Stop:s, Quit:q): ")

        if play_order == 'p':
            player.play_song(song_number)
        elif play_order == 's':
            player.stop_song()
        elif play_order == 'q':
            print("Exiting player.")
            player.stop_song()
            break


if __name__ == '__main__':
    asyncio.run(main())
