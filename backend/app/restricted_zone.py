import cv2
import numpy as np
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

# Define restricted zone as a polygon (x, y points)
# These are example coordinates - adjust based on your camera resolution
RESTRICTED_ZONE = np.array([
    [200, 200],
    [500, 200],
    [500, 450],
    [200, 450]
], np.int32)

def point_in_polygon(point, polygon):
    result = cv2.pointPolygonTest(polygon, point, False)
    return result >= 0

cap = cv2.VideoCapture(0)

# Track which IDs are currently inside the zone (avoid duplicate alerts)
ids_in_zone = set()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(frame, persist=True, verbose=False, classes=[0])  # class 0 = person

    annotated_frame = frame.copy()

    # Draw restricted zone
    cv2.polylines(annotated_frame, [RESTRICTED_ZONE], isClosed=True, color=(0, 0, 255), thickness=2)
    overlay = annotated_frame.copy()
    cv2.fillPoly(overlay, [RESTRICTED_ZONE], color=(0, 0, 255))
    annotated_frame = cv2.addWeighted(overlay, 0.2, annotated_frame, 0.8, 0)

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xywh.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()

        for box, track_id in zip(boxes, track_ids):
            x, y, w, h = box
            foot_point = (float(x), float(y + h / 2))

            inside = point_in_polygon(foot_point, RESTRICTED_ZONE)

            color = (0, 0, 255) if inside else (0, 255, 0)
            x1, y1 = int(x - w / 2), int(y - h / 2)
            x2, y2 = int(x + w / 2), int(y + h / 2)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)

            label = f"ID:{track_id} {'INTRUSION!' if inside else 'safe'}"
            cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            if inside and track_id not in ids_in_zone:
                print(f"[ALERT] Person ID {track_id} entered restricted zone!")
                ids_in_zone.add(track_id)
            elif not inside and track_id in ids_in_zone:
                ids_in_zone.discard(track_id)

    cv2.imshow("VisionGuard - Restricted Zone - Press Q to quit", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()