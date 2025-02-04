import cv2
import numpy as np
import face_recognition
from djitellopy import tello
from datetime import datetime
import time
import os
import threading

me = tello.Tello()
me.connect()
print(me.get_battery())

me.streamon()
me.set_video_fps(me.FPS_30)
me.takeoff()
me.send_rc_control(0, 0, 27, 0)
time.sleep(2)

path = 'FaceFile'
images = []
classNames = []
myList = os.listdir(path)

for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])

hansung_img = cv2.imread('FaceFile/hansung.jpg')
hansung_encoding = face_recognition.face_encodings(hansung_img)[0]

def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)
        if encode:
            encodeList.append(encode[0])
    return encodeList

encodeListKnown = findEncodings(images)
print('인코딩 완료')

drone_control_stop = False

def drone_control():
    global drone_control_stop
    while not drone_control_stop:
        me.move_forward(100)
        time.sleep(2)
        me.rotate_clockwise(90)
        time.sleep(2)

def face_detection():
    global drone_control_stop
    w, h = 320, 240
    pid = [0.8, 0.5, 0]
    fbRange = [6200, 6800]
    pError = 0

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    storage_path = os.path.join(desktop_path, "storage")

    if not os.path.exists(storage_path):
        os.makedirs(storage_path)
        print(f"디렉토리 생성됨: {storage_path}")
    else:
        print(f"디렉토리 이미 존재함: {storage_path}")

    def findFace(img):
        faceCascade = cv2.CascadeClassifier("haarcascades/haarcascade_frontalface_default.xml")
        imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(imgGray, 1.1, 4)
        myFaceListC = []
        myFaceListArea = []

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cx = x + w // 2
            cy = y + h // 2
            area = w * h
            cv2.circle(img, (cx, cy), 5, (0, 255, 0), cv2.FILLED)
            myFaceListC.append([cx, cy])
            myFaceListArea.append(area)
        if len(myFaceListArea) != 0:
            i = myFaceListArea.index(max(myFaceListArea))
            return img, [myFaceListC[i], myFaceListArea[i]]
        else:
            return img, [[0, 0], 0]

    def trackFace(info, w, pid, pError):
        area = info[1]
        x, y = info[0]
        fb = 0

        error = x - w // 2
        speed = pid[0] * error + pid[1] * (error - pError)
        speed = int(np.clip(speed, -100, 100))

        if area > fbRange[0] and area < fbRange[1]:
            fb = 0
        elif area > fbRange[1]:
            fb = -20
        elif area < fbRange[0] and area != 0:
            fb = 20

        if x == 0:
            speed = 0
            error = 0

        me.send_rc_control(0, fb, 0, speed)
        return error

    while True:
        img = me.get_frame_read().frame
        img = cv2.resize(img, (w, h))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(img)
        encodesCurFrame = face_recognition.face_encodings(img, faceCurFrame)

        for encodeFace, faceLoc in zip(encodesCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                name = classNames[matchIndex].upper()
                y1, x2, y2, x1 = faceLoc
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                if "HANSUNG" in name:
                    pass
                else:
                    drone_control_stop = True

                    while True:
                        img = me.get_frame_read().frame
                        img = cv2.resize(img, (w, h))

                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                        img, info = findFace(img)
                        pError = trackFace(info, w, pid, pError)

                        if info[1] > 0:
                            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            filename = os.path.join(storage_path, f"detected_face_{current_time}.jpg")
                            cv2.imwrite(filename, img)

                            if cv2.imwrite(filename, img):
                                print(f"이미지 저장됨: {filename}")
                            else:
                                print(f"이미지 저장 실패: {filename}")

                        cv2.imshow('drone streaming', img)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            me.land()
                            break

        cv2.imshow('drone streaming', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            me.land()
            break


face_detection_thread = threading.Thread(target=face_detection)
drone_control_thread = threading.Thread(target=drone_control)

face_detection_thread.start()
drone_control_thread.start()

face_detection_thread.join()
drone_control_thread.join()

cv2.destroyAllWindows()
