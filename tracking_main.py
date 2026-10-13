import os
from datetime import datetime

import cv2
import pandas as pd
from ultralytics import YOLO

# Separate tracking add-on. Original main.py is not modified.
os.makedirs("output", exist_ok=True)

MODEL_PATH = "yolov8n.pt"
VIDEO_PATH = "videos/store_video.mp4"
CSV_PATH = "output/customer_tracking_report.csv"

model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    raise FileNotFoundError(
        f"Could not open video: {VIDEO_PATH}. "
        "Check that videos/store_video.mp4 exists."
    )

report_data = []
frame_number = 0

print("Project 25 Customer Tracking Started...")
print("Press q in the video window to stop.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_number += 1
        results = model.track(
            frame,
            persist=True,
            classes=[0],  # COCO class 0 = person
            tracker="bytetrack.yaml",
            verbose=False,
        )

        active_ids = set()
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                track_id = int(box.id[0].item()) if box.id is not None else None
                if track_id is not None:
                    active_ids.add(track_id)

                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                label = f"Customer ID: {track_id}" if track_id is not None else "Customer"
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame, label, (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                )
                report_data.append({
                    "Frame Number": frame_number,
                    "Processing Time": datetime.now().strftime("%H:%M:%S"),
                    "Tracking ID": track_id,
                    "X1": x1, "Y1": y1, "X2": x2, "Y2": y2,
                })

        cv2.putText(
            frame, f"People detected: {len(active_ids)}", (25, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
        )
        cv2.imshow("Project 25 - Customer Tracking IDs", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()

columns = ["Frame Number", "Processing Time", "Tracking ID", "X1", "Y1", "X2", "Y2"]
df = pd.DataFrame(report_data, columns=columns)
df.to_csv(CSV_PATH, index=False)
unique_ids = df["Tracking ID"].dropna().nunique() if not df.empty else 0
print("Tracking analysis completed.")
print(f"Tracking report saved to: {CSV_PATH}")
print(f"Distinct tracking IDs observed: {unique_ids}")
print("Note: IDs are temporary tracker identities, not verified real-world identities.")
