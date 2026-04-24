# Bicep Curl Counter — OpenCV & MediaPipe

A real-time bicep curl counter using computer vision.

## What it does
- Detects body pose using MediaPipe
- Tracks elbow angle on both arms simultaneously
- Counts reps accurately using angle smoothing and a state machine
- Saves workout sessions and sets to a MySQL database

## Tech used
- Python
- OpenCV
- MediaPipe
- NumPy
- MySQL

## Problems solved
- Fixed false rep counts using a rolling average buffer to smooth noisy angles
- Implemented a lock mechanism to prevent counting during angle wobble at peak
- Tracks left and right arms independently with separate state

## How to run
1. Install dependencies: `pip install opencv-python mediapipe numpy mysql-connector-python`
2. Start MySQL via XAMPP
3. Create database `curl_counter` with `sessions` and `sets` tables
4. Run `AwesomePoseProject.py`
5. Press `S` to save a set, `Q` to quit
