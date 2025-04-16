import cv2
from ultralytics import YOLO

# Load YOLOv8 model (Replace 'best.pt' with your trained model file)
model = YOLO("best.pt")

# Open system camera (0 for default webcam, change to 1 or 2 for external cameras)
cap = cv2.VideoCapture(0)

# Check if the webcam opened successfully
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

frame_count = 0  # Counter for saving detected frames

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame from webcam.")
        break

    # Run YOLO model on the frame
    results = model(frame, conf=0.3)  # Adjust confidence threshold as needed

    # Process detections
    for r in results:
        if len(r.boxes) > 0:  # If an ambulance is detected
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Get bounding box coordinates
                conf = box.conf[0].item()  # Confidence score
                cls = int(box.cls[0])  # Class index
                label = model.names[cls]  # Get class label (ambulance)

                # Draw bounding box and label on the frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label}: {conf:.2f}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Save detected frame
            filename = f"detected_frame_{frame_count}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename}")

    # Show frame with detections
    cv2.imshow("Ambulance Detection (Webcam)", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frame_count += 1  # Increment frame count

# Release webcam and close all windows
cap.release()
cv2.destroyAllWindows()
