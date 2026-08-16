import cv2
import sys
import time

def test_camera_hardware():
    print("=" * 60)
    print("GESTUREDRIVE STANDALONE CAMERA HARDWARE DIAGNOSTIC")
    print("=" * 60)

    indices_to_test = [0, 1, 2, 3]
    backends = []
    if sys.platform == "win32":
        backends = [
            ("DSHOW", cv2.CAP_DSHOW),
            ("MSMF", cv2.CAP_MSMF),
            ("DEFAULT", cv2.CAP_ANY)
        ]
    else:
        backends = [("DEFAULT", cv2.CAP_ANY)]

    working_camera = None

    for idx in indices_to_test:
        for b_name, b_id in backends:
            print(f"\n[DIAGNOSTIC] Testing Camera Index {idx} with Backend {b_name}...")
            try:
                cap = cv2.VideoCapture(idx, b_id)
                opened = cap.isOpened()
                print(f"[DIAGNOSTIC] -> isOpened(): {opened}")

                if opened:
                    # Request resolution 640x480
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

                    # Read test frames
                    success_count = 0
                    test_shape = None

                    for f_idx in range(5):
                        ret, frame = cap.read()
                        if ret and frame is not None and frame.size > 0:
                            success_count += 1
                            test_shape = frame.shape
                        time.sleep(0.03)

                    print(f"[DIAGNOSTIC] -> 5-Frame Read Success Count: {success_count}/5")

                    if success_count > 0:
                        print(f"[DIAGNOSTIC] -> SUCCESS! Valid frame received. Shape: {test_shape}")
                        working_camera = (idx, b_name, cap, test_shape)
                        break
                    else:
                        print(f"[DIAGNOSTIC] -> WARNING: Camera opened but ret=False for all test frames.")
                    cap.release()
            except Exception as e:
                print(f"[DIAGNOSTIC] -> Exception: {e}")

        if working_camera:
            break

    if not working_camera:
        print("\n[DIAGNOSTIC] ERROR: No working camera device found on indices 0-3!")
        return

    idx, b_name, cap, shape = working_camera
    print("\n" + "=" * 60)
    print(f"CAMERA DIAGNOSTIC SUCCESS: Index {idx} ({b_name}) | Frame Shape: {shape}")
    print("Opening live OpenCV test window... Press 'q' or 'ESC' on the window to close.")
    print("=" * 60)

    window_name = f"GestureDrive Camera Test - Index {idx} ({b_name})"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    frame_num = 0
    start_t = time.time()

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Warning: Frame drop during live test.")
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1)
        frame_num += 1
        elapsed = time.time() - start_t
        fps = frame_num / max(0.001, elapsed)

        # Draw diagnostic text directly on frame
        cv2.rectangle(frame, (10, 10), (550, 70), (0, 0, 0), -1)
        cv2.putText(frame, "GESTUREDRIVE LIVE CAMERA DIAGNOSTIC", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"Cam Index: {idx} | Backend: {b_name} | FPS: {fps:.1f} | Shape: {frame.shape}", (20, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        cv2.imshow(window_name, frame)

        key = cv2.waitKey(15) & 0xFF
        if key == 27 or key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Camera diagnostic complete. Closed successfully.")

if __name__ == "__main__":
    test_camera_hardware()
