import cv2
import time
from collections import defaultdict
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture(0)

# Track aspect ratio history per person: {track_id: [(timestamp, ratio), ...]}
ratio_history = defaultdict(list)

# If height/width ratio drops below this, person is likely lying down
FALL_RATIO_THRESHOLD = 1.0
FALL_ALERT_COOLDOWN = 5  # seconds, avoid repeated alerts
last_alert_time = defaultdict(float)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(frame, persist=True, verbose=False, classes=[0])  # class 0 = person
    annotated_frame = results[0].plot()

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xywh.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()

        for box, track_id in zip(boxes, track_ids):
            x, y, w, h = box
            ratio = float(h) / float(w) if w > 0 else 0  # height/width

            now = time.time()
            ratio_history[track_id].append((now, ratio))

            # Keep only last 2 seconds of history
            ratio_history[track_id] = [
                (t, r) for (t, r) in ratio_history[track_id] if now - t <= 2
            ]

            is_fallen = ratio < FALL_RATIO_THRESHOLD

            if is_fallen and (now - last_alert_time[track_id]) > FALL_ALERT_COOLDOWN:
                print(f"[FALL ALERT] Person ID {track_id} may have fallen! (ratio={ratio:.2f})")
                last_alert_time[track_id] = now

            if is_fallen:
                label = f"ID:{track_id} FALL DETECTED"
                x1, y1 = int(x - w / 2), int(y - h / 2)
                cv2.putText(annotated_frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("VisionGuard - Fall Detection (experimental) - Press Q to quit", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()