import cv2
from collections import defaultdict
from ultralytics import YOLO
model = YOLO("yolov8n.pt")

# Track history: {track_id: [(x, y), (x, y), ...]}
track_history = defaultdict(list)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(frame, persist=True, verbose=False)

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xywh.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()
        classes = results[0].boxes.cls.int().cpu().tolist()

        annotated_frame = results[0].plot()

        for box, track_id, cls in zip(boxes, track_ids, classes):
            x, y, w, h = box
            center = (float(x), float(y))
            track_history[track_id].append(center)

            # Keep only last 30 points per track
            if len(track_history[track_id]) > 30:
                track_history[track_id].pop(0)

            # Draw trail
            points = track_history[track_id]
            for i in range(1, len(points)):
                pt1 = (int(points[i - 1][0]), int(points[i - 1][1]))
                pt2 = (int(points[i][0]), int(points[i][1]))
                cv2.line(annotated_frame, pt1, pt2, (0, 255, 255), 2)

            label = model.names[cls]
            print(f"Tracked: {label} | ID: {track_id} | Position: {center}")
    else:
        annotated_frame = frame

    cv2.imshow("VisionGuard Tracking with History - Press Q to quit", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()