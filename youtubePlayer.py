from urllib.parse import parse_qs, urlparse
import pafy
import googleapiclient.discovery
import vlc
import configparser
import os


class YtbListPlayer:
    def __init__(self, api_key):
        self.play_list = []
        self.media_player = ""
        self.player = vlc.Instance()
        self.youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    # https://stackoverflow.com/questions/45019711/how-to-make-vlc-repeat-the-whole-playlist-instead-of-only-current-item-using-lib
    def set_playlist(self, ytb_playlist_url):
        '''
        유튜브 playlist 주소만 받아 설정
        :param ytb_playlist_url: 유튜브 플레이리스트 url 주소
        :return:
        '''
        url_parse = urlparse(ytb_playlist_url)
        if url_parse.path == '/playlist':
            self.url = ytb_playlist_url
        elif url_parse.path == '/watch':
            raise ValueError("유튜브플레이리스트 URL 정보가 필요합니다.")
        else:
            self.url = config['DEFAULT'].get("MY_PLAY_URL", None)

    def get_playlist(self):
        '''
        변환된 리스트를 전달.
        :return:
        '''
        if self.play_list != []:
            return self.play_list
        else:
            return False

    def get_title(self, num):
        '''
        리스트에서 특정 플레이 명칭을 전달.
        :param num:
        :return:
        '''
        if self.play_list[num]:
            audio = self.play_list[num]
            return audio.title
        else:
            return "---"

    def clear_playitems(self):
        self.play_list = []

    def set_utbplay_items(self):
        '''
        유튭 플레이리스트로부터 플레이정보를 가져오기
        :return:
        '''
        if self.url is None:
            raise ValueError("나의 재생목록 url을 설정해주세요")

        query = parse_qs(urlparse(self.url).query, keep_blank_values=True)
        playlist_id = query["list"][0]

        # print(f'get all playlist items links from {playlist_id}')
        youtube = self.youtube

        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=100
        )

        playlist_items = []
        while request is not None:
            response = request.execute()
            playlist_items += response["items"]
            request = youtube.playlistItems().list_next(request, response)

        url_list = [
            f'https://www.youtube.com/watch?v={t["snippet"]["resourceId"]["videoId"]}&list={playlist_id}&t=0s'
            for t in playlist_items
        ]

        if self.play_list == []:
            i = 0
        else:
            i = len(self.play_list) + 1

        for url in url_list:
            try:
                audio = pafy.new(url)
                self.play_list.append(audio)
                i += 1
            except:
                continue

    def get_playitems(self):
        for index, audio in enumerate(self.play_list, 0):
            print(f"({index}) {audio.title} [{audio.duration}, {audio.length}] - 좋아요수: {audio.likes}")

    def set_mediaplayer(self):
        player = vlc.Instance()
        # player = vlc.Instance('--verbose 3')
        # 플레이어의 미디어 리스트 객체 생성.
        media_list = player.media_list_new()
        # 미디어리스트 플레이어 생성.
        self.media_player = player.media_list_player_new()
        for audio in self.play_list:
            if str(type(audio)) != "<class 'str'>":
                play_url = audio.getbestaudio(preftype="m4a").url
                media = player.media_new(play_url)
                media.get_mrl()
                media_list.add_media(media)
            else:
                media = player.media_new(audio)
                media_list.add_media(media)

        self.media_player.set_media_list(media_list)

    def cmd_player(self, select_num):
        self.media_player.play_item_at_index(select_num)
        print(self.get_title(select_num))
        # https://www.programcreek.com/python/example/93375/vlc.Instance
        # https://www.geeksforgeeks.org/python-vlc-medialistplayer-currently-playing/?ref=rp

    def download_media(self, num):
        audio_url = self.play_list[num].getbestaudio(preftype="m4a")
        song_name = self.play_list[num].title
        BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + "\\" + "download"
        print("Downloading: {0}.".format(song_name))
        directory = input("다운로드할 경로를 넣어주세요(기본값: download): ")
        if directory:
            audio_url.download(filepath=directory)
        else:
            audio_url.download(filepath=BASE_DIR)

    def bulk_download(self):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + "\\" + "download"
        directory = input("다운로드할 경로를 넣어주세요(기본값: download): ")
        for audio in self.play_list:
            audio_url = audio.getbestaudio(preftype="m4a")
            song_name = audio.title
            print(f"Downloading: ({i}) {song_name}")
            if directory:
                audio_url.download(filepath=directory)
            else:
                audio_url.download(filepath=BASE_DIR)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    print('Welcome to the Youtube-Mp3 player.')
    api_key = config['DEFAULT'].get("API_KEY")

    url = 'https://www.youtube.com/playlist?list=PL7283475-4cpXpbZJdgNWOVh0nvMbDCH7'
    x = YtbListPlayer(api_key)

    play_order = ''
    song_number = 0
    while play_order != 'q':
        if play_order != 's':
            download = input('1. Play Live Music\n2. Download Mp3 from Youtube.\n')

        if download == '1' or download == '':
            if play_order == 'a' or play_order == '':
                # 시작
                url = input("플레이리스트 URL: ").replace(" ", "")
            elif play_order == 'c':
                x.clear_playitems()
                url = input("플레이리스트 URL: ").replace(" ", "")

            if play_order != 's':
                x.set_playlist(url)
                x.set_utbplay_items()
                x.set_mediaplayer()
                x.get_playitems()

            song_number = int(input('상위루프 곡 선택: '))
            x.cmd_player(song_number)
            play_order = ""

            while True:
                # 곡을 실행, 일시멈춤, 다음곡, 이전곡, 처음으로, 리스트추가, 리스트삭제, 아이템삭제.
                if play_order != 's':
                    play_order = input("하위루프 명령어를 입력해주세요: ")

                if play_order == 's':
                    x.media_player.stop()
                    for i, audio in enumerate(x.play_list, 0):
                        print(f"({i}) {audio.title} - 좋아요수: {audio.likes}")
                    break
                elif play_order == 'p':
                    x.media_player.pause()
                elif play_order == '':
                    x.media_player.play()
                elif play_order == 'r':
                    print('Replaying: {0}'.format(x.play_list.get(int(song_number))))
                elif play_order == 'n':
                    x.media_player.next()
                    song_number += 1
                    print("다음곡: ")
                    print(x.get_title(song_number))
                elif play_order == 'b':
                    x.media_player.previous()
                    song_number -= 1
                    print(x.get_title(song_number))
                elif play_order == 'a':
                    x.media_player.stop()
                    break
                elif play_order == 'd':
                    x.media_player.stop()
                    break

        elif download == '2':
            url = input("플레이리스트 URL: ").replace(" ", "")
            x.set_playlist(url)
            x.set_utbplay_items()
            x.get_playitems()
            # song_number = int(input('상위루프 곡 선택: '))
            # x.download_media(song_number)
            x.bulk_download()

