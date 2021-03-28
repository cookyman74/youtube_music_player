import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse

#extract playlist id from url
url = 'https://www.youtube.com/playlist?list=PL7283475-4coSLe9BEWrHpQUJLPZZtI9B'
query = parse_qs(urlparse(url).query, keep_blank_values=True)
playlist_id = query["list"][0]

print(f'get all playlist items links from {playlist_id}')
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = "AIzaSyCk0ie0Dd75ry5t1srGz6OnaXZM5e1wMdg")

request = youtube.playlistItems().list(
    part = "snippet",
    playlistId = playlist_id,
    maxResults = 50
)
response = request.execute()

playlist_items = []
while request is not None:
    response = request.execute()
    print(response)
    playlist_items += response["items"]
    request = youtube.playlistItems().list_next(request, response)

print(f"total: {len(playlist_items)}")
print([
    f'https://www.youtube.com/watch?v={t["snippet"]["resourceId"]["videoId"]}&list={playlist_id}&t=0s'
    for t in playlist_items
])