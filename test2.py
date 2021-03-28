import pafy
import cv2


url = "https://www.youtube.com/watch?v=aKX8uaoy9c8"
videoPafy = pafy.new(url)
best = videoPafy.getbest(preftype="webm")

video=cv2.VideoCapture(best.url)