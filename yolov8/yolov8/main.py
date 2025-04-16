import cv2
import torch
from ultralytics import YOLO
from plyer import notification  # For desktop notifications
import requests  # If you want to trigger a real-world system

# Load YOLOv8 model (Replace 'best.pt' with your trained model file)
model = YOLO("best.pt")

# Video file path (Change to 0 for webcam)
video_path = "ambu (online-video-cutter.com).mp4"  # Replace with your video file
cap = cv2.VideoCapture(video_path)

# Check if video opened successfully
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

frame_count = 0  # Counter for tracking total frames
save_interval = 30  # Save every 30 frames (~1 second for 30 FPS)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Video ended or failed to read frame.")
        break

    # Run YOLO model on the frame
    results = model(frame, conf=0.3)  # Adjust confidence threshold as needed
    ambulance_detected = False  # Flag to check ambulance detection

    # Process detections
    for r in results:
        if len(r.boxes) > 0:  # If any object is detected
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Get bounding box coordinates
                conf = box.conf[0].item()  # Confidence score
                cls = int(box.cls[0])  # Class index
                label = model.names[cls]  # Get class label

                if label.lower() == "ambulance":  # Check if detected object is an ambulance
                    ambulance_detected = True

                    # Draw bounding box and label on the frame
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{label}: {conf:.2f}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # Save frame only every 'save_interval' frames
                    if frame_count % save_interval == 0:
                        filename = "latest_detection.jpg"  # Overwrites the same file
                        cv2.imwrite(filename, frame)
                        print(f"Saved: {filename}")

    if ambulance_detected:
        # Terminal alert with color formatting
        print("\033[91mALERT: Ambulance detected! Change signal to GREEN!\033[0m")  # Red alert in the terminal

        # Show a desktop notification
        notification.notify(
            title="Ambulance Detected",
            message="Change traffic signal to GREEN!",
            timeout=5
        )

        # Send API request (If applicable)
        try:
            response = requests.post("http://traffic-system.local/api/change_signal", json={"signal": "green"})
            if response.status_code == 200:
                print("\033[92mTraffic signal changed to GREEN.\033[0m")  # Green confirmation message
            else:
                print("\033[93mFailed to change traffic signal.\033[0m")  # Yellow warning message
        except Exception as e:
            print("\033[91mError sending API request:\033[0m", e)

    # Show frame with detections
    cv2.imshow("Ambulance Detection", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frame_count += 1  # Increment frame count

# Release resources
cap.release()
cv2.destroyAllWindows()
