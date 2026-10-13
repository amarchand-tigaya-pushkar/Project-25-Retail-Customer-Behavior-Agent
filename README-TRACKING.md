# Project 25 — Customer Tracking IDs Add-on

This add-on uses a separate `tracking_main.py`; the original `main.py` is not modified.

## Run on Windows CMD

```bat
.venv\Scripts\activate.bat
python tracking_main.py
```

Input video: `videos\store_video.mp4`
Output CSV: `output\customer_tracking_report.csv`

Press `q` while the video window is active to stop processing.

## How it works
- Ultralytics YOLO tracking with `persist=True` and ByteTrack.
- Detects COCO class `0` (person).
- Draws temporary tracking IDs on the video.
- Saves frame number, processing time, ID and bounding-box coordinates to CSV.

## Limitations
Tracking IDs can change after occlusion, long gaps, or tracking failures. They are not verified real-world identities and do not guarantee a true unique visitor count.
