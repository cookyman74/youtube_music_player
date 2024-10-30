# youtube_music_player

`youtube_music_player`는 YouTube 및 로컬 음악 파일을 재생할 수 있는 간단한 음악 플레이어입니다. 이 앱을 통해 사용자는 YouTube 플레이리스트와 로컬 디렉토리의 음악을 추가하고, 직관적인 GUI를 통해 쉽게 음악을 재생하고 관리할 수 있습니다.

---

## 주요 기능

- **유튜브 플레이리스트 추가**: 유튜브의 플레이리스트 URL을 입력하여 음악을 스트리밍할 수 있습니다.
- **로컬 파일 추가**: MP3, WAV, OGG 등 다양한 로컬 음악 파일을 추가하여 재생할 수 있습니다.
- **앨범 이미지 표시**: 현재 재생 중인 곡의 앨범 아트를 표시하여 시각적인 즐거움도 제공합니다.
- **재생 시간 표시**: 전체 음악 재생 시간과 현재 재생 위치를 실시간으로 확인할 수 있습니다.
- **볼륨 조절**: 간편한 볼륨 슬라이더로 볼륨을 조절할 수 있습니다.
- **기본 재생 제어**: 이전 곡, 재생/일시 정지, 정지, 다음 곡 버튼을 통해 음악을 쉽게 제어할 수 있습니다.

---

## 설치 방법

1. **파이썬 설치**: Python 3.8 이상이 설치되어 있어야 합니다. [Python 다운로드](https://www.python.org/downloads/)

2. **필수 패키지 설치**: 다음 명령어를 실행하여 프로젝트에 필요한 패키지를 설치하세요.
   ```bash
   pip install -r requirements.txt
   ```
   
3. FFmpeg 설치: FFmpeg는 음악 파일을 처리하는 데 필요합니다. OS에 맞게 설치하세요.
   - Windows: FFmpeg 설치 가이드
   - macOS (Homebrew 사용):

       ```bash
         brew install ffmpeg
       ```

   - Linux (APT 사용):

        ```bash
          sudo apt update
          sudo apt install ffmpeg
        ```

## 실행 방법
1. 애플리케이션 실행
2. YouTube 플레이리스트 추가
3. 로컬 파일 추가
4. 재생 제어

## 파일구조

```plaintext
youtube_music_player/
├── main.py                # 메인 GUI 실행 파일
├── youtubePlayer.py       # YouTube 플레이어 로직
├── images/                # UI에 사용할 이미지 파일 폴더
│   ├── play.png
│   ├── pause.png
│   └── ...
├── downloaded_audios/     # 다운로드된 오디오 파일 저장 폴더
├── requirements.txt       # 필요한 패키지 리스트
└── config.ini             # YouTube API 키 설정 파일
```


## 기여
이 프로젝트에 기여하고 싶다면 언제든지 Pull Request를 제출해 주세요! 코드 개선, 버그 수정, 기능 추가를 환영합니다.

"💖 이 앱이 당신의 일상에 작은 행복을 더해줬다면, 저희의 노력에 따뜻한 커피 한 잔으로 응원해주세요. 🌱

#한잔의행복"

<a href="https://www.buymeacoffee.com/cookymanm" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
