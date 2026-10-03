import os
import time
from collections import defaultdict

import cv2
from ultralytics import YOLO

from .incident import IncidentManager, Severity
from .crud import save_incident

manager = IncidentManager(cooldown_seconds=10)

model = YOLO("yolov8n.pt")

# Evidence photos yahan save hongi (backend/evidence)
EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

cap = cv2.VideoCapture(0)

# Track aspect ratio history per person: {track_id: [(timestamp, ratio), ...]}
ratio_history = defaultdict(list)

# Agar height/width ratio is se kam ho, toh person lete hue ho sakta hai
FALL_RATIO_THRESHOLD = 0.8
FALL_ALERT_COOLDOWN = 5  # seconds
last_alert_time = defaultdict(float)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(frame, persist=True, verbose=False, classes=[0])
    annotated_frame = results[0].plot()

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xywh.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()
        confs = results[0].boxes.conf.cpu().tolist()

        for box, track_id, conf in zip(boxes, track_ids, confs):
            x, y, w, h = box
            ratio = float(h) / float(w) if w > 0 else 0  # height/width

            now = time.time()
            ratio_history[track_id].append((now, ratio))

            # Sirf last 2 seconds ka data rakho
            ratio_history[track_id] = [
                (t, r) for (t, r) in ratio_history[track_id] if now - t <= 2
            ]

            # Fall tab maano jab ~2 sec ke saare readings ratio < threshold ho
            history = ratio_history[track_id]
            enough_data = len(history) > 5 and (now - history[0][0]) >= 1.5
            is_fallen = enough_data and all(r < FALL_RATIO_THRESHOLD for (_, r) in history)

            if is_fallen:
                label = f"ID:{track_id} FALL DETECTED"
                x1, y1 = int(x - w / 2), int(y - h / 2)
                cv2.putText(annotated_frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if is_fallen and (now - last_alert_time[track_id]) > FALL_ALERT_COOLDOWN:
                print(f"[FALL ALERT] Person ID {track_id} may have fallen! (ratio={ratio:.2f})")
                last_alert_time[track_id] = now

                incident = manager.create_incident(
                    "cam_01", "fall_detected", Severity.CRITICAL, float(conf), track_id
                )
                if incident:
                    # Photo save karo (incident id ke naam se)
                    filename = f"{incident.id}.jpg"
                    cv2.imwrite(os.path.join(EVIDENCE_DIR, filename), annotated_frame)
                    incident.evidence_path = filename
                    save_incident(incident)

    cv2.imshow("VisionGuard - Fall Detection (experimental) - Press Q to quit", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()