"""
Face Recognition: Feature extraction and comparison
"""
import sys
import math
from pathlib import Path
from typing import Optional, List, Tuple
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

# Try importing face recognition libraries
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[Face Recognition] Warning: OpenCV not installed, camera features unavailable")

# Check Face++ API availability (only Face++ is supported)
try:
    from security.facepp_api import USE_FACEPP, FacePPError
    if USE_FACEPP:
        FACEPP_AVAILABLE = True
        FACE_RECOGNITION_AVAILABLE = True
        print("[Face Recognition] Using Face++ API (cloud service)")
    else:
        FACEPP_AVAILABLE = False
        FACE_RECOGNITION_AVAILABLE = False
        print("[Face Recognition] Face++ not configured, face recognition unavailable")
except (ImportError, Exception):
    FACEPP_AVAILABLE = False
    FACE_RECOGNITION_AVAILABLE = False
    print("[Face Recognition] Face++ API not available, face recognition unavailable")


class FaceRecognitionError(Exception):
    """Face recognition exception"""
    pass


def capture_face_image(show_preview: bool = True, preview_duration: int = 3) -> Optional[np.ndarray]:
    """
    Capture an image from default camera with optional preview window
    
    Args:
        show_preview: Show camera preview window
        preview_duration: Preview duration in seconds before auto-capture
    
    Returns:
        Image array in OpenCV format, or None if failed
        
    Raises:
        FaceRecognitionError: If camera is unavailable
    """
    if not CV2_AVAILABLE:
        raise FaceRecognitionError("OpenCV not installed, cannot use camera")
    
    print("[Face Recognition] Opening camera...")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        raise FaceRecognitionError("Cannot open camera")
    
    try:
        captured_frame = None
        
        if show_preview:
            window_name = "Face Capture - Please face the camera"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 640, 480)
            
            import time
            start_time = time.time()
            
            print(f"[Face Recognition] Preview window opened, auto-capture in {preview_duration} seconds...")
            print("[Face Recognition] Tip: Press SPACE to capture now, ESC to cancel")
            
            while True:
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    raise FaceRecognitionError("Cannot read image from camera")
                
                elapsed = time.time() - start_time
                remaining = max(0, preview_duration - int(elapsed))
                
                display_frame = frame.copy()
                
                overlay = display_frame.copy()
                cv2.rectangle(overlay, (10, 10), (630, 100), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.5, display_frame, 0.5, 0, display_frame)
                
                if remaining > 0:
                    text = f"Countdown: {remaining} sec"
                    cv2.putText(display_frame, text, (20, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
                else:
                    text = "Capturing..."
                    cv2.putText(display_frame, text, (20, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                
                hint = "SPACE=Capture | ESC=Cancel"
                cv2.putText(display_frame, hint, (20, 85), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                cv2.imshow(window_name, display_frame)
                
                key = cv2.waitKey(30) & 0xFF
                
                if key == 27:  # ESC
                    print("[Face Recognition] User cancelled")
                    cv2.destroyWindow(window_name)
                    raise FaceRecognitionError("User cancelled capture")
                elif key == 32:  # SPACE
                    print("[Face Recognition] Manual capture")
                    captured_frame = frame
                    break
                elif elapsed >= preview_duration:
                    print("[Face Recognition] Auto-capture")
                    captured_frame = frame
                    break
            
            success_frame = captured_frame.copy()
            overlay = success_frame.copy()
            cv2.rectangle(overlay, (0, 0), (640, 480), (0, 255, 0), -1)
            cv2.addWeighted(overlay, 0.3, success_frame, 0.7, 0, success_frame)
            cv2.putText(success_frame, "Success!", (180, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
            cv2.imshow(window_name, success_frame)
            cv2.waitKey(1000)
            
            cv2.destroyWindow(window_name)
            
        else:
            ret, frame = cap.read()
            
            if not ret or frame is None:
                raise FaceRecognitionError("Cannot read image from camera")
            
            captured_frame = frame
        
        print(f"[Face Recognition] Image captured {captured_frame.shape}")
        return captured_frame
        
    finally:
        cap.release()
        cv2.destroyAllWindows()


def extract_face_embedding(image: np.ndarray, show_detection: bool = False) -> List[float]:
    """
    Extract face feature vector from image using Face++ API

    Args:
        image: OpenCV format image array (BGR)
        show_detection: Show face detection result

    Returns:
        Face feature vector (list) - Face++ image data with special marker

    Raises:
        FaceRecognitionError: If no face detected or extraction failed
    """
    if not FACE_RECOGNITION_AVAILABLE:
        raise FaceRecognitionError("Face++ API not available, cannot extract features")

    if not FACEPP_AVAILABLE:
        raise FaceRecognitionError("Face++ not configured, cannot extract features")

    print("[Face Recognition] Detecting faces using Face++...")

    # Use Face++ API (cloud service)
    # Return image bytes as "embedding" for later comparison
    try:
        from security.facepp_api import detect_face_facepp, get_face_rectangle

        # Convert image to bytes
        import cv2
        _, image_bytes = cv2.imencode('.jpg', image)
        image_data = image_bytes.tobytes()

        # Verify face detection
        result = detect_face_facepp(image_data)

        if not result.get('faces'):
            raise FaceRecognitionError("No face detected by Face++")

        print(f"[Face Recognition] Face++ detected face successfully")

        # Show detection result if requested
        if show_detection and CV2_AVAILABLE:
            rect = get_face_rectangle(image_data)

            if rect:
                display_image = image.copy()
                x, y, w, h = rect['left'], rect['top'], rect['width'], rect['height']
                cv2.rectangle(display_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(display_image, "Face Detected (Face++)", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                window_name = "Face Detection Result"
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(window_name, 640, 480)
                cv2.imshow(window_name, display_image)
                cv2.waitKey(1500)
                cv2.destroyWindow(window_name)

        # Return image bytes as embedding (will be stored for comparison)
        # Use special marker to indicate this is Face++ image data
        return ["FACEPP_IMAGE", image_data.hex()]  # Convert bytes to hex string for JSON storage

    except Exception as e:
        from security.facepp_api import FacePPError
        if isinstance(e, FacePPError):
            raise FaceRecognitionError(f"Face++ API error: {str(e)}")
        raise FaceRecognitionError(f"Face++ extraction failed: {str(e)}")


def compute_distance(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate distance/similarity between two Face++ images using Face++ Compare API

    Args:
        vec1: First Face++ image marker
        vec2: Second Face++ image marker

    Returns:
        Distance metric (float), smaller means more similar, range [0, 1]

    Raises:
        ValueError: If data format is invalid or Face++ not available
    """
    # Check if these are Face++ image data (marker format: ["FACEPP_IMAGE", hex_string])
    if (len(vec1) == 2 and len(vec2) == 2 and
        isinstance(vec1[0], str) and isinstance(vec2[0], str) and
        vec1[0] == "FACEPP_IMAGE" and vec2[0] == "FACEPP_IMAGE"):

        # Face++ image comparison
        if FACEPP_AVAILABLE:
            try:
                from security.facepp_api import compare_faces_facepp

                print("[Face Recognition] Comparing faces using Face++ Compare API...")

                # Convert hex strings back to bytes
                image_data1 = bytes.fromhex(vec1[1])
                image_data2 = bytes.fromhex(vec2[1])

                # Call Face++ Compare API
                confidence, threshold = compare_faces_facepp(image_data1, image_data2)

                # Convert confidence (0-100) to distance (0-1)
                # Higher confidence = lower distance
                distance = (100 - confidence) / 100.0

                print(f"[Face Recognition] Face++ confidence: {confidence:.2f}%, distance: {distance:.4f}")
                print(f"[Face Recognition] Face++ suggests threshold: {threshold:.2f} (confidence)")

                return distance

            except Exception as e:
                print(f"[Face Recognition] Face++ comparison error: {e}")
                return 1.0  # Return max distance on error
        else:
            raise ValueError("Face++ image data provided but Face++ not available")

    else:
        raise ValueError("Invalid face data format: only Face++ image data is supported")


def generate_mock_face_embedding() -> List[float]:
    """
    Generate mock Face++ face data for testing

    Returns:
        Face++ format mock image data
    """
    import random
    print("[Face Recognition] Generating mock Face++ image data (test mode)")
    # Generate mock hex string data
    mock_hex = ''.join(random.choice('0123456789abcdef') for _ in range(1000))
    return ["FACEPP_IMAGE", mock_hex]


def capture_and_extract_face(show_preview: bool = True, show_detection: bool = True) -> List[float]:
    """
    Convenience method: Capture image and extract face features using Face++

    Args:
        show_preview: Show camera preview window (default True)
        show_detection: Show face detection result (default True)

    Returns:
        Face++ format face data

    Raises:
        FaceRecognitionError: If capture or extraction failed
    """
    image = capture_face_image(show_preview=show_preview)
    embedding = extract_face_embedding(image, show_detection=show_detection)
    return embedding


def is_face_recognition_available() -> Tuple[bool, str]:
    """
    Check if Face++ face recognition features are available

    Returns:
        (available, status message)
    """
    if not CV2_AVAILABLE:
        return False, "OpenCV not installed"

    if not FACEPP_AVAILABLE:
        return False, "Face++ API not configured or unavailable"

    return True, "Face++ face recognition features available"
