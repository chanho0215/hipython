from __future__ import annotations

import argparse
import time

import cv2
from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use a webcam for real-time object detection with YOLO."
    )
    parser.add_argument(
        "--model",
        default="yolo11n.pt",
        help="YOLO model path or model name. Downloads automatically if needed.",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Webcam index. Use 0 for the default camera.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.45,
        help="Minimum confidence threshold.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Inference image size.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help='Inference device. Example: "cpu", "0", "0,1".',
    )
    return parser.parse_args()


def draw_status(frame, fps: float) -> None:
    cv2.rectangle(frame, (10, 10), (180, 48), (20, 20, 20), -1)
    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (20, 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError(
            f"Cannot open webcam {args.camera}. Check camera access or index."
        )

    previous_time = time.time()

    print("Webcam object detection started.")
    print("Press 'q' or ESC to quit.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read a frame from the webcam.")
                break

            results = model.predict(
                source=frame,
                conf=args.conf,
                imgsz=args.imgsz,
                device=args.device,
                verbose=False,
            )
            annotated = results[0].plot()

            current_time = time.time()
            fps = 1.0 / max(current_time - previous_time, 1e-6)
            previous_time = current_time
            draw_status(annotated, fps)

            cv2.imshow("YOLO Webcam Detection", annotated)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
