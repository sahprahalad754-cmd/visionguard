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

FALL_RATIO_THRESHOLD = 0.7   # height/width is se kam = leta hua
STANDING_RATIO = 1.2         # height/width is se zyada = khada hua
STANDING_MEMORY = 6          # girne se pehle itne sec ke andar khada dikha hona chahiye
GLOBAL_COOLDOWN = 15         # seconds, kisi bhi ID ke liye

last_standing_time = defaultdict(float)
fall_active = set()          # jin IDs ka fall alert ho chuka hai
last_global_alert = 0

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

            # Khada hua dikha toh time yaad rakho
            if ratio >= STANDING_RATIO:
                last_standing_time[track_id] = now

            # Utha toh dobara alert allow
            if ratio >= FALL_RATIO_THRESHOLD:
                fall_active.discard(track_id)

            ratio_history[track_id].append((now, ratio))

            # Sirf last 2 seconds ka data rakho
            ratio_history[track_id] = [
                (t, r) for (t, r) in ratio_history[track_id] if now - t <= 2
            ]

            history = ratio_history[track_id]
            enough_data = len(history) > 5 and (now - history[0][0]) >= 1.5
            all_low = enough_data and all(r < FALL_RATIO_THRESHOLD for (_, r) in history)
            was_standing = (now - last_standing_time[track_id]) <= STANDING_MEMORY
            is_fallen = all_low and was_standing

            if is_fallen:
                label = f"ID:{track_id} FALL DETECTED"
                x1, y1 = int(x - w / 2), int(y - h / 2)
                cv2.putText(annotated_frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if (
                is_fallen
                and track_id not in fall_active
                and (now - last_global_alert) > GLOBAL_COOLDOWN
            ):
                print(f"[FALL ALERT] Person ID {track_id} may have fallen! (ratio={ratio:.2f})")
                fall_active.add(track_id)
                last_global_alert = now

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