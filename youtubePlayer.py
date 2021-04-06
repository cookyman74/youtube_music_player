from urllib.parse import parse_qs, urlparse
import pafy
import googleapiclient.discovery
import vlc
import configparser
import re


class YtbListPlayer:
    def __init__(self, api_key):
        self.play_list = {}
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
        if self.play_list != {}:
            return self.play_list
        else:
            return False

    def get_title(self, num):
        '''
        리스트에서 특정 플레이 명칭을 전달.
        :param num:
        :return:
        '''

        if self.play_list[num][0] is not None:
            return self.play_list[num][0]
        else:
            return False

    def clear_playitems(self):
        self.play_list = {}

    def set_playitems(self):
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

        if self.play_list == {}:
            i = 1
        else:
            i = len(self.play_list) + 1
            
        for url in url_list:
            try:
                info = pafy.new(url)
                self.play_list[i] = [info.title, info.getbestaudio(preftype="m4a")]
                print(f"({i}) {info.title}")
                i += 1
            except ValueError:
                raise ValueError("에러 발생")

    def get_playitems(self):
        for index, value in self.play_list.items():
            print(f"({index}) {value}")

    def set_mediaplayer(self):
        player = vlc.Instance()
        # 플레이어의 미디어 리스트 객체 생성.
        media_list = player.media_list_new()
        # 미디어리스트 플레이어 생성.

        self.media_player = player.media_list_player_new()
        for _, v in self.play_list.items():
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


    def download_media(self, num):
        url = self.play_list[int(num)]
        info = pafy.new(url)
        audio = info.getbestaudio(preftype="m4a")
        song_name = self.play_list[int(num)]
        print("Downloading: {0}.".format(self.play_list[int(num)]))
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
        song_name = self.play_list[int(num)]
        print("Downloading: {0}.".format(self.play_list[int(num)]))
        print(song_name)
        song_name = input("Filename (Enter if as it is): ")
        #       file_name = song_name[:11] + '.m4a'
        file_name = song_name + '.m4a'
        if song_name == '':
            audio.download(remux_audio=True)
        else:
            audio.download(filepath=filename, remux_audio=True)


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
        download = input('1. Play Live Music\n2. Download Mp3 from Youtube.\n')
        if play_order != 'q' and (download == '1' or download == ''):

            if play_order == 'c':
                x.clear_playitems()
                url = input("플레이리스트 URL: ").replace(" ", "")
                x.set_playlist(url)
                x.set_playitems()
                x.set_mediaplayer()
               
            if play_order == 'a':
                # 시작
                url = input("플레이리스트 URL: ").replace(" ", "")
                x.set_playlist(url)
                x.set_playitems()
                x.set_mediaplayer()
            
            song_number = int(input('곡 선택: '))
            x.cmd_player(song_number)
                
            while True:
                # 곡을 실행, 일시멈춤, 다음곡, 이전곡, 처음으로, 리스트추가, 리스트삭제, 아이템삭제.
                if song_number == 0 or play_order == "":
                    play_order = input('명령어를 입력: ')

                if play_order == 's':
                    x.media_player.stop()
                    for i, v in x.play_list.items():
                        print(f"({i}) {v[0]}")
                    song_number = int(input('곡 선택: '))
                    break
                elif play_order == 'p':
                    x.media_player.pause()
                elif play_order == '':
                    x.media_player.play()
                elif play_order == 'r':
                    print('Replaying: {0}'.format(x.play_list[int(song_number)]))
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
            print('\nDownloading {0} (conveniently) from youtube servers.'.format(play_order.title()))
            song_number = input('Input song number: ')
            x.download_media(song_number)

