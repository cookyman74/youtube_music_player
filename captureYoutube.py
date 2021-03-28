import pafy
import cv2

url = "https://www.youtube.com/watch?v=gdZLi9oWNZg"
video = pafy.new(url)

print("video title : {}".format(video.title))  # 제목
print("video rating : {}".format(video.rating))  # 평점
print("video viewcount : {}".format(video.viewcount))  # 조회수
print("video author : {}".format(video.author))  # 저작권자
print("video length : {}".format(video.length))  # 길이
print("video duration : {}".format(video.duration))  # 길이
print("video likes : {}".format(video.likes))  # 좋아요
print("video dislikes : {}".format(video.dislikes))  # 싫어요

best = video.getbest(preftype="mp4")
print("best resolution : {}".format(best.resolution))

cap = cv2.VideoCapture(best.url)

# 동영상 크기(frame정보)를 읽어옴
frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 동영상 프레임을 캡쳐
frameRate = int(cap.get(cv2.CAP_PROP_FPS))

frame_size = (frameWidth, frameHeight)
print('frame_size={}'.format(frame_size))
print('fps={}'.format(frameRate))

# cv2.VideoWriter_fourcc(*'코덱')
# codec 및 녹화 관련 설정
# 인코딩 방식을 설정
fourcc = cv2.VideoWriter_fourcc(*'XVID')
# fourcc = cv2.VideoWriter_fourcc(*'DIVX')
# fourcc = cv2.VideoWriter_fourcc(*'MPEG')
# fourcc = cv2.VideoWriter_fourcc(*'X264')

out1Path = 'data/recode1.mp4'
out2Path = 'data/recode2.mp4'

# 영상 저장하기
# out1Path : 저장할 파일명
# fourcc : frame 압축 관련 설정(인코딩, 코덱 등)
# frameRate : 초당 저장할 frame
# frame_size : frame 사이즈(가로, 세로)
# isColor : 컬러 저장 여부
out1 = cv2.VideoWriter(out1Path, fourcc, frameRate, frame_size)
out2 = cv2.VideoWriter(out2Path, fourcc, frameRate, frame_size)

while True:
    # 한 장의 이미지를 가져오기
    # 이미지 -> frame
    # 정상적으로 읽어왔는지 -> retval
    retval, frame = cap.read()
    if not (retval):
        break  # 프레임정보를 정상적으로 읽지 못하면 while문을 빠져나가기

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 회색으로 컬러 변환
    edges = cv2.Canny(gray, 100, 200)  # Canny함수로 엣지 따기

    # 동영상 파일에 쓰기
    out1.write(frame)
    out2.write(edges)

    # 모니터에 출력
    cv2.imshow('frame', frame)
    cv2.imshow('edges', edges)

    key = cv2.waitKey(frameRate)  # frameRate msec동안 한 프레임을 보여준다

    # 키 입력을 받으면 키값을 key로 저장 -> esc == 27
    if key == 27:
        break

if cap.isOpened():
    cap.release()
    out1.release()
    out2.release()

cv2.destroyAllWindows()