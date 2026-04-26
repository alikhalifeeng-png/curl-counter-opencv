import time
import cv2
import numpy as np
from collections import deque
import mysql.connector
import PoseModule as pm

# ── Database Connection ──
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="curl_counter"
)
cursor = db.cursor()


def create_session():
    try:
        cursor.execute("INSERT INTO sessions (duration, total_reps) VALUES (0, 0)")
        db.commit()
        print(f"Session created: {cursor.lastrowid}")
        return cursor.lastrowid
    except Exception as e:
        print(f"Session creation failed: {e}")
        return None


def save_set(session_id, arm, reps):
    try:
        cursor.execute(
            "INSERT INTO sets (session_id, arm, reps) VALUES (%s, %s, %s)",
            (session_id, arm, reps)
        )
        db.commit()
        print(f"Set saved — {arm} arm: {reps} reps")
    except Exception as e:
        print(f"Save set failed: {e}")


def close_session(session_id, duration, total_reps):
    try:
        cursor.execute(
            "UPDATE sessions SET duration=%s, total_reps=%s WHERE id=%s",
            (duration, total_reps, session_id)
        )
        db.commit()
        print(f"Session closed — Duration: {duration}s | Total reps: {total_reps}")
    except Exception as e:
        print(f"Close session failed: {e}")


def smooth_angle(buffer, new_angle):
    buffer.append(new_angle)
    return np.mean(buffer)


def count_rep(per, count, direction, locked):
    if per >= 90 and not locked:
        if direction == 0:
            count += 0.5
            direction = 1
            locked = True
    if per <= 15:
        if direction == 1:
            count += 0.5
            direction = 0
        locked = False
    return count, direction, locked


def draw_curl_bar(img, per, bar_x, label, count):
    bar_top = 100
    bar_bot = 650
    color = (0, 255, 0) if per > 50 else (255, 100, 0)
    bar_fill = int(np.interp(per, [0, 100], [bar_bot, bar_top]))

    cv2.rectangle(img, (bar_x, bar_top), (bar_x + 30, bar_bot), (200, 200, 200), 2)
    cv2.rectangle(img, (bar_x, bar_fill), (bar_x + 30, bar_bot), color, cv2.FILLED)
    cv2.putText(img, f'{int(per)}%', (bar_x - 5, bar_top - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.putText(img, label, (bar_x + 5, bar_bot + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.rectangle(img, (bar_x - 5, bar_bot + 45), (bar_x + 55, bar_bot + 100),
                  (0, 0, 0), cv2.FILLED)
    cv2.putText(img, str(int(count)), (bar_x, bar_bot + 95),
                cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 255, 255), 3)


# ── Init ──
cap = cv2.VideoCapture(0)
detector = pm.PoseDetector()

pTime = 0
startTime = time.time()
session_id = create_session()

# ── Smoothing buffers ──
bufferR = deque(maxlen=5)
bufferL = deque(maxlen=5)

# ── Rep state ──
countR, countL = 0, 0
dirR, dirL = 0, 0
lockedR, lockedL = False, False

# ── Total reps accumulator ──
totalRepsAllTime = 0

# ── Feedback message ──
message = ""
messageTime = 0

# ── Set counter ──
setCount = 0

while True:
    success, img = cap.read()
    if not success:
        break

    img = detector.findPose(img)
    lmList = detector.findPosition(img, draw=False)

    if lmList:
        # ── Right Arm ──
        rawR = detector.findAngle(img, 12, 14, 16)
        smoothR = smooth_angle(bufferR, rawR)
        perR = np.interp(smoothR, [40, 160], [100, 0])
        countR, dirR, lockedR = count_rep(perR, countR, dirR, lockedR)

        # ── Left Arm ──
        rawL = detector.findAngle(img, 11, 13, 15)
        smoothL = smooth_angle(bufferL, rawL)
        perL = np.interp(smoothL, [40, 160], [100, 0])
        countL, dirL, lockedL = count_rep(perL, countL, dirL, lockedL)

        draw_curl_bar(img, perL, 20, 'L', countL)
        draw_curl_bar(img, perR, img.shape[1] - 70, 'R', countR)

    # ── Keybinds ──
    key = cv2.waitKey(1) & 0xFF

    # S — save current set and reset counts
    if key == ord('s'):
        setCount += 1
        totalRepsAllTime += int(countR + countL)  # accumulate before reset
        save_set(session_id, 'right', int(countR))
        save_set(session_id, 'left', int(countL))
        countR, countL = 0, 0                     # reset after saving
        dirR, dirL = 0, 0
        lockedR, lockedL = False, False
        bufferR.clear()
        bufferL.clear()
        message = f"Set {setCount} saved!"
        messageTime = time.time()
        print(f"Set {setCount} saved")

    # Q — quit and close session
    if key == ord('q'):
        totalRepsAllTime += int(countR + countL)  # add any unsaved reps
        duration = int(time.time() - startTime)
        close_session(session_id, duration, totalRepsAllTime)
        break

    # ── Feedback message on screen ──
    if message and time.time() - messageTime < 2:
        cv2.rectangle(img, (150, 320), (650, 380), (0, 0, 0), cv2.FILLED)
        cv2.putText(img, message, (160, 365),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

    # ── Controls hint ──
    cv2.putText(img, "S = Save Set | Q = Quit", (150, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

    # ── Set counter on screen ──
    cv2.putText(img, f'Sets: {setCount}', (img.shape[1] // 2 - 50, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    # ── FPS ──
    cTime = time.time()
    fps = 1 / (cTime - pTime) if pTime != 0 else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (img.shape[1] // 2 - 50, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow('Curl Counter', img)

# ── Session Summary ──
print(f"\n--- Session Summary ---")
print(f"Sets completed:  {setCount}")
print(f"Total reps:      {totalRepsAllTime}")
print(f"Duration:        {int(time.time() - startTime)}s")

cursor.close()
db.close()
cap.release()
cv2.destroyAllWindows()