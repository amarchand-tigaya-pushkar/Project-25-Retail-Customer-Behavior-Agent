
import cv2
import pandas as pd
from ultralytics import YOLO
from datetime import datetime
import os

# Create output folder if not exists
os.makedirs("output", exist_ok=True)

# Load YOLO model
# yolov8n.pt is a small beginner-friendly model
model = YOLO("yolov8n.pt")

# Video path
video_path = "videos/store_video.mp4"

# Open video
cap = cv2.VideoCapture(video_path)

# List to store report data
report_data = []

# Frame counter
frame_number = 0

print("Retail Store Customer Behavior Agent Started...")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    # Run YOLO detection
    results = model(frame)

    customer_count = 0

    # Read detection results
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])

            # In COCO dataset, class 0 means person
            if class_id == 0:
                customer_count += 1

                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                # Draw rectangle around customer
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                # Show label
                cv2.putText(
                    frame,
                    "Customer",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

    # Show customer count on screen
    cv2.putText(
        frame,
        f"Customers: {customer_count}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2
    )

    # Save data for report
    report_data.append({
        "Frame Number": frame_number,
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Customer Count": customer_count
    })

    # Show video
    cv2.imshow("Retail Store Customer Behavior Agent", frame)

    # Press q to stop
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release video
cap.release()
cv2.destroyAllWindows()

# Save report to CSV
df = pd.DataFrame(report_data)
df.to_csv("output/customer_report.csv", index=False)

print("Analysis Completed!")
print("Report saved in output/customer_report.csv")
