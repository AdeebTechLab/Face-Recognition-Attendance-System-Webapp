import os
import base64
import pickle
from datetime import datetime
import cv2
import numpy as np
import face_recognition

STORAGE_ROOT = os.getenv("BIOMETRIC_STORAGE_DIR", "storage")
DATASET_DIR = os.path.join(STORAGE_ROOT, "dataset")
MODELS_DIR = os.path.join(STORAGE_ROOT, "models")
ACTIVE_MODEL_PATH = os.path.join(MODELS_DIR, "active_encodings.pkl")

os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

def decode_base64_image(image_base64: str) -> np.ndarray:
    """Converts data:image/jpeg;base64,... into an OpenCV BGR numpy array."""
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]
    img_bytes = base64.b64decode(image_base64)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Corrupted or unreadable image frame.")
    return frame

def validate_and_save_capture(roll_number: str, image_base64: str) -> dict:
    """Detects a single face in the captured frame, crops with margin, and saves locally."""
    frame = decode_base64_image(image_base64)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Detect face locations
    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    if len(face_locations) == 0:
        return {"saved": False, "reason": "No face detected. Ensure proper lighting and look at the camera."}
    if len(face_locations) > 1:
        return {"saved": False, "reason": "Multiple faces detected. Only one person may be in frame during registration."}

    top, right, bottom, left = face_locations[0]
    h, w, _ = frame.shape
    pad = 30
    crop = frame[max(0, top - pad):min(h, bottom + pad), max(0, left - pad):min(w, right + pad)]

    safe_roll = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in roll_number)
    person_dir = os.path.join(DATASET_DIR, safe_roll)
    os.makedirs(person_dir, exist_ok=True)

    existing = [f for f in os.listdir(person_dir) if f.endswith(".jpg")]
    filename = f"sample_{len(existing) + 1:03d}_{int(datetime.utcnow().timestamp())}.jpg"
    filepath = os.path.join(person_dir, filename)
    cv2.imwrite(filepath, crop)

    return {
        "saved": True,
        "photo_count": len(existing) + 1,
        "filename": filename
    }

def train_encodings_model(active_students: list, tolerance: float = 0.50) -> dict:
    """
    Extracts 128-d embeddings for all active students with >=10 photos.
    Computes genuine Leave-One-Out Cross-Validation accuracy (never fabricated).
    """
    known_encodings = []
    known_rolls = []
    known_names = []
    known_depts = []
    valid_students = 0

    for student in active_students:
        safe_roll = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in student.roll_number)
        person_dir = os.path.join(DATASET_DIR, safe_roll)
        if not os.path.exists(person_dir):
            continue

        images = [f for f in os.listdir(person_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        if len(images) < 10:
            continue

        student_enc_count = 0
        for img_name in images:
            img_path = os.path.join(person_dir, img_name)
            bgr = cv2.imread(img_path)
            if bgr is None:
                continue
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model="hog")
            encs = face_recognition.face_encodings(rgb, boxes)
            if encs:
                known_encodings.append(encs[0])
                known_rolls.append(student.roll_number)
                known_names.append(student.name)
                known_depts.append(student.department)
                student_enc_count += 1

        if student_enc_count > 0:
            valid_students += 1

    total_samples = len(known_encodings)
    if total_samples == 0 or valid_students == 0:
        raise ValueError("Dataset validation failed: Ensure active students have at least 10 valid face photos.")

    # Genuine Leave-One-Out Cross-Validation (LOOCV)
    correct = 0
    enc_matrix = np.array(known_encodings)
    for i in range(total_samples):
        if total_samples == 1:
            break
        target = enc_matrix[i]
        gallery = np.delete(enc_matrix, i, axis=0)
        gallery_rolls = known_rolls[:i] + known_rolls[i + 1:]

        distances = face_recognition.face_distance(gallery, target)
        best_idx = int(np.argmin(distances))
        if distances[best_idx] <= tolerance and gallery_rolls[best_idx] == known_rolls[i]:
            correct += 1

    accuracy = round((correct / total_samples) * 100.0, 2) if total_samples > 1 else 0.0
    version_tag = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    version_path = os.path.join(MODELS_DIR, f"model_{version_tag}.pkl")

    payload = {
        "version_tag": version_tag,
        "encodings": known_encodings,
        "roll_numbers": known_rolls,
        "names": known_names,
        "departments": known_depts,
        "tolerance": tolerance
    }

    with open(version_path, "wb") as f:
        pickle.dump(payload, f)
    with open(ACTIVE_MODEL_PATH, "wb") as f:
        pickle.dump(payload, f)

    return {
        "version_tag": version_tag,
        "students_count": valid_students,
        "encodings_count": total_samples,
        "validation_accuracy": accuracy,
        "tolerance_used": tolerance,
        "artifact_path": version_path
    }

def recognize_faces_in_frame(image_base64: str, tolerance: float = 0.50) -> list:
    """Detects all faces in frame, matches against active encodings, and returns bounding boxes + metadata."""
    if not os.path.exists(ACTIVE_MODEL_PATH):
        raise FileNotFoundError("No trained model available. Please train the model first.")

    with open(ACTIVE_MODEL_PATH, "rb") as f:
        model_data = pickle.load(f)

    frame = decode_base64_image(image_base64)
    orig_h, orig_w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(rgb_frame, model="hog")
    encodings = face_recognition.face_encodings(rgb_frame, locations)

    results = []
    for (top, right, bottom, left), encoding in zip(locations, encodings):
        distances = face_recognition.face_distance(model_data["encodings"], encoding)
        best_idx = int(np.argmin(distances))
        min_dist = float(distances[best_idx])

        is_known = min_dist <= tolerance
        results.append({
            "box": {
                "top": top,
                "right": right,
                "bottom": bottom,
                "left": left,
                "frame_width": orig_w,
                "frame_height": orig_h
            },
            "status": "KNOWN" if is_known else "UNKNOWN",
            "roll_number": model_data["roll_numbers"][best_idx] if is_known else None,
            "name": model_data["names"][best_idx] if is_known else "Unknown",
            "department": model_data["departments"][best_idx] if is_known else None,
            "distance": round(min_dist, 4),
            "confidence": round(max(0.0, (1.0 - min_dist) * 100.0), 1)
        })

    return results