﻿import pafy
import pyglet
import urllib.request
from urllib.parse import *
from bs4 import BeautifulSoup
import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse
import vlc
import configparser
import re
import asyncio


config = configparser.ConfigParser()
config.read('config.ini')


class Youtube_mp3():
    def __init__(self, api_key):
        self.playlist = []
        self.item_names = {}
        self.youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        self.player = vlc.Instance()

    # https://stackoverflow.com/questions/45019711/how-to-make-vlc-repeat-the-whole-playlist-instead-of-only-current-item-using-lib


    def nextPlay(self):
        self.listPlayer.next()

    def playPlaylist(self):
        self.listPlayer.play()
        
    def set_url(self, my_urlist):
        url_p = re.compile("^http.?:\/\/.*")
        if url_p.match(my_urlist):
            self.url = my_urlist
        else:
            self.url = config['DEFAULT'].get("MY_PLAY_URL", None)

    def get_play_items(self):
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
                    self.item_names[i] = [info.title, url]
                    print(f"({i}) {info.title}")
                    i += 1
                except ValueError:
                    raise ValueError("에러 발생")
        else:
            print("="*100)
            for index, value in self.item_names.items():
                print(f"({index}) {value}")

    def get_list(self):
        return self.item_names

    async def check_status(self, player):
        while True:
            status = str(player.get_state())
            if status == "State.Ended":
                print("멈춰")
                break

    def play_media(self, num):
        player = vlc.Instance()
        # 플레이리스트 생성
        media_list = player.media_list_new()
        # 미디어리스트 재생기 생성.
        media_player = player.media_list_player_new()

        for i, v in self.item_names.items():
            url = v[1]
            info = pafy.new(url)
            audio = info.getbestaudio(preftype="m4a")
            play_url = audio.url
            # 미디어리스트 생성
            media = player.media_new(play_url)
            media.get_mrl()
            media_list.add_media(media)

        # 미디어리스트를 재생기에 부여
        media_player.set_media_list(media_list)
        media_player.play()
        status = str(media_player.get_state())
        good_states = ["State.Playing", "State.NothingSpecial", "State.Opening"]

        stop = ''
        while True:
            stop = input('Type "s" to stop; "p" to pause; "" to play; : ')
            if stop == 's':
                media_player.stop()
                for i, v in self.item_names.items():
                    print(f"({i}) {v[0]}")
                break
            elif stop == 'p':
                media_player.pause()
            elif stop == '':
                media_player.play()
            elif stop == 'r':
                print('Replaying: {0}'.format(self.item_names[int(num)]))
            elif stop == 'n':
                media_player.next()

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

    def add_playlist(self, search_query):
        url = self.get_play_items(search_query, max_search=1)
        self.playlist.append(url)


if __name__ == '__main__':
    print('Welcome to the Youtube-Mp3 player.')
    api_key = config['DEFAULT'].get("API_KEY")
    url = 'https://www.youtube.com/playlist?list=PL7283475-4coSLe9BEWrHpQUJLPZZtI9B'

    x = Youtube_mp3(api_key)
    x.set_url(url)
    search = ''
    x.get_play_items()
    while search != 'q':
        max_search = 5
        download = input('1. Play Live Music\n2. Download Mp3 from Youtube.\n')
        if search != 'q' and (download == '1' or download == ''):
            song_number = input('Input song number: ')
            x.play_media(song_number)
        elif download == '2':
            print('\nDownloading {0} (conveniently) from youtube servers.'.format(search.title()))
            x.get_play_items(search, max_search)
            x.get_search_items(max_search)
            song_number = input('Input song number: ')
            x.download_media(song_number)