import pafy
import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse
import vlc
import configparser
import re

config = configparser.ConfigParser()
config.read('config.ini')


class YtbListPlayer:
    def __init__(self, api_key):
        self.playlist = []
        self.item_names = {}
        self.media_player = ""
        self.player = vlc.Instance()
        self.url = config['DEFAULT'].get("MY_PLAY_URL", None)
        self.youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    # https://stackoverflow.com/questions/45019711/how-to-make-vlc-repeat-the-whole-playlist-instead-of-only-current-item-using-lib
    def set_url(self, ytb_playlist_url):
        '''
        유튜브 playlist 주소만 받아 설정
        :param ytb_playlist_url: 유튜브 플레이리스트 url 주소
        :return: 
        '''
        url_p = re.compile("^http.?:\/\/.*")
        if url_p.match(ytb_playlist_url):
            self.url = ytb_playlist_url

    def get_ytblist(self):
        '''
        변환된 리스트를 전달.
        :return:
        '''
        if self.item_names != {}:
            return self.item_names
        else:
            return False

    def get_title(self, num):
        '''
        리스트에서 특정 플레이 명칭을 전달.
        :param num:
        :return:
        '''

        if self.item_names[num][0] is not None:
            return self.item_names[num][0]
        else:
            return False

    def get_play_items(self):
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
            maxResults=50
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

        if self.item_names == {}:
            i = 1
            for url in url_list:
                try:
                    info = pafy.new(url)
                    self.item_names[i] = [info.title, info.getbestaudio(preftype="m4a")]
                    print(f"({i}) {info.title}")
                    i += 1
                except ValueError:
                    raise ValueError("에러 발생")
        else:
            print("=" * 100)
            for index, value in self.item_names.items():
                print(f"({index}) {value}")

    def set_mediaplayer(self):
        player = vlc.Instance()
        # 플레이어의 미디어 리스트 객체 생성.
        media_list = player.media_list_new()
        # 미디어리스트 플레이어 생성.

        self.media_player = player.media_list_player_new()

        for i, v in self.item_names.items():
            audio = v[1]
            play_url = audio.url
            # 미디어리스트 생성
            media = player.media_new(play_url)
            media.get_mrl()
            media_list.add_media(media)

        self.media_player.set_media_list(media_list)

    def cmd_player(self, select_num):
        num = int(select_num) - 1
        self.media_player.play_item_at_index(num)
        print(self.get_title(num+1))

        # https://www.programcreek.com/python/example/93375/vlc.Instance
        status = str(self.media_player.get_state())
        # https://www.geeksforgeeks.org/python-vlc-medialistplayer-currently-playing/?ref=rp
        while True:
            play_typ = input('Type "s" to stop; "p" to pause; "" to play; : ')
            if play_typ == 's':
                self.media_player.stop()
                for i, v in self.item_names.items():
                    print(f"({i}) {v[0]}")
                break
            elif play_typ == 'p':
                self.media_player.pause()
            elif play_typ == '':
                self.media_player.play()
            elif play_typ == 'r':
                print('Replaying: {0}'.format(self.item_names[int(num)]))
            elif play_typ == 'n':
                self.media_player.next()
                num += 1
                print(self.get_title(num+1))
            elif play_typ == 'b':
                self.media_player.previous()
                num -= 1
                print(self.get_title(num+1))

        return play_typ

    def download_media(self, num):
        url = self.item_names[int(num)]
        info = pafy.new(url)
        audio = info.getbestaudio(preftype="m4a")
        song_name = self.item_names[int(num)]
        print("Downloading: {0}.".format(self.item_names[int(num)]))
        print(song_name)
        song_name = input("Filename (Enter if as it is): ")
        #       file_name = song_name[:11] + '.m4a'
        file_name = song_name + '.m4a'
        if song_name == '':
            audio.download(remux_audio=True)
        else:
            audio.download(filepath=filename, remux_audio=True)

    def bulk_download(self, url):
        info = pafy.new(url)
        audio = info.getbestaudio(preftype="m4a")
        song_name = self.item_names[int(num)]
        print("Downloading: {0}.".format(self.item_names[int(num)]))
        print(song_name)
        song_name = input("Filename (Enter if as it is): ")
        #       file_name = song_name[:11] + '.m4a'
        file_name = song_name + '.m4a'
        if song_name == '':
            audio.download(remux_audio=True)
        else:
            audio.download(filepath=filename, remux_audio=True)


if __name__ == '__main__':

    print('Welcome to the Youtube-Mp3 player.')
    api_key = config['DEFAULT'].get("API_KEY")

    url = 'https://www.youtube.com/playlist?list=PL7283475-4coSLe9BEWrHpQUJLPZZtI9B'
    x = YtbListPlayer(api_key)
    x.set_url(url)
    search = ''
    x.get_play_items()
    while search != 'q':
        max_search = 5
        download = input('1. Play Live Music\n2. Download Mp3 from Youtube.\n')
        if search != 'q' and (download == '1' or download == ''):
            song_number = input('Input song number: ')
            if search != 's':
                print("search: ", search)
                x.set_mediaplayer()
            search = x.cmd_player(song_number)
        elif download == '2':
            print('\nDownloading {0} (conveniently) from youtube servers.'.format(search.title()))
            x.get_play_items(search, max_search)
            x.get_search_items(max_search)
            song_number = input('Input song number: ')
            x.download_media(song_number)