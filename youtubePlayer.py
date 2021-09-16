from urllib.parse import parse_qs, urlparse
import pafy
import googleapiclient.discovery
import vlc
import configparser
import os
import asyncio


class YtbListPlayer:
    def __init__(self, api_key, *options):
        self.vlc_player = vlc.Instance(*options)
        self.play_list = []
        self.add_list = []
        self.media_list = ""
        self.media_player = ""
        self.events = None
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
        try:
            title = self.play_list[num].title
        except:
            title = None
        return title

    def clear_playitems(self):
        self.play_list = []
        self.add_list = []
        self.media_list = ""
        self.media_player = ""

    async def coroutine_pafy(self, url):
        '''
        코루틴 변환 함수
        :param url: 유튭플레이리스트
        :return:
        '''
        self.add_list = []
        try:
            loop = asyncio.get_event_loop()
            audio = await loop.run_in_executor(None, pafy.new, url)
            # await self.play_list.append(audio)
            await self.add_list.append(audio)
        except:
            pass

    async def set_utbplay_items(self):
        '''
        유튭 플레이리스트로부터 플레이정보를 비동기적으로 가져오기
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
        futures = [asyncio.ensure_future(self.coroutine_pafy(url)) for url in url_list]
        await asyncio.gather(*futures)

    def print_playitems(self):
        for index, audio in enumerate(self.play_list, 0):
            print(f"({index}) {audio.title} [{audio.duration}, {audio.length}] - 좋아요수: {audio.likes}")

    def set_mediaplayer(self):
        # creating a media list object for the first time
        if self.media_list == "":
            self.media_player = vlc.MediaListPlayer()
            self.media_list = vlc.MediaList()

        # for audio in self.play_list:
        for audio in self.add_list:
            if str(type(audio)) != "<class 'str'>":
                play_url = audio.getbestaudio(preftype="m4a").url
                media = self.vlc_player.media_new(play_url)
                media.get_mrl()
                self.media_list.add_media(media)
            else:
                media = self.vlc_player.media_new(audio)
                self.media_list.add_media(media)
        # add add_list to play_list
        self.play_list.extend(self.add_list)
        # set media_list to media_player
        self.media_player.set_media_list(self.media_list)

    def cmd_player(self, select_num):
        self.media_player.play_item_at_index(select_num)
        print(f">>> Play : {self.get_title(select_num)}")
        print("=" * 50)
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
    loop = asyncio.get_event_loop()
    config = configparser.ConfigParser()
    config.read('config.ini')

    print('Welcome to the Youtube-Mp3 player.')
    api_key = config['DEFAULT'].get("API_KEY")

    url = input("Plz enter the Youtube playlist URL : ").replace(" ", "")
    x = YtbListPlayer(api_key)

    play_order = ''
    song_number = 0
    while play_order != 'q':
        if play_order != 's':
            download = input('Choose one\n1. Play Live Music\n2. Download Mp3 from Youtube.\n')

        if download == '1' or download == '':
            if play_order == 'a':
                # 시작
                url = input("Plz enter the Youtube playlist URL : ").replace(" ", "")
            elif play_order == 'c':
                x.clear_playitems()
                url = input("Plz enter the Youtube playlist URL : ").replace(" ", "")

            if play_order != 's':
                x.set_playlist(url)
                loop.run_until_complete(x.set_utbplay_items())
                loop.close()
                x.set_mediaplayer()
                x.print_playitems()

            song_number = int(input('Choose the song to play: '))
            x.cmd_player(song_number)
            play_order = ""

            while True:
                # 곡을 실행, 일시멈춤, 다음곡, 이전곡, 처음으로, 리스트추가, 리스트삭제, 아이템삭제.
                if play_order != 's':
                    play_order = input(
                        "Order (Play:p, Stop:s, Pause Song:ps, Next Song:n, Before Song:b, Add Song:a) : ")

                if play_order == 's':
                    x.media_player.stop()
                    for i, audio in enumerate(x.play_list, 0):
                        print(f"({i}) {audio.title} - 좋아요수: {audio.likes}")
                    break
                    print("=" * 50)
                elif play_order == 'p':
                    x.media_player.pause()
                    print(f">>> Pause Song: {x.get_title(song_number)}")
                    print("=" * 50)
                elif play_order == '':
                    x.media_player.play()
                elif play_order == 'r':
                    print('Replaying: {0}'.format(x.play_list.get(int(song_number))))
                elif play_order == 'n':
                    x.media_player.next()
                    song_number += 1
                    print("Next Song: ")
                    print(">>>",x.get_title(song_number))
                    print("="*50)
                elif play_order == 'b':
                    x.media_player.previous()
                    song_number -= 1
                    print("Previous Song: ")
                    print(">>>", x.get_title(song_number))
                    print("=" * 50)
                elif play_order == 'a':
                    x.media_player.stop()
                    print("Add Playlist")
                    break

        elif download == '2':
            url = input("플레이리스트 URL: ").replace(" ", "")
            x.set_playlist(url)
            x.set_utbplay_items()
            x.print_playitems()
            x.bulk_download()

