import mss
import cv2
import numpy as np


def capture_screen() -> np.ndarray:
    with mss.mss() as sct:
        shot = sct.grab(sct.monitors[0])
        img = np.array(shot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


def _decode(detector, img) -> set[str]:
    try:
        retval, decoded_info, *_ = detector.detectAndDecodeMulti(img)
        if retval and decoded_info:
            return {s for s in decoded_info if s.strip()}
    except Exception:
        pass
    return set()


def detect_qr(img: np.ndarray) -> list[str]:
    detector = cv2.QRCodeDetector()
    results: set[str] = set()

    # 1. 原图
    results |= _decode(detector, img)
    if results:
        return list(results)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. 灰度图
    results |= _decode(detector, gray)
    if results:
        return list(results)

    # 3. 自适应阈值（处理光线不均匀）
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    results |= _decode(detector, thresh)
    if results:
        return list(results)

    # 4. 缩小到 1080p 再检测（高分辨率屏幕二维码可能太小）
    h, w = img.shape[:2]
    if w > 1920:
        scale = 1920 / w
        small = cv2.resize(gray, (int(w * scale), int(h * scale)))
        results |= _decode(detector, small)
        if results:
            return list(results)

    # 5. 放大 1.5x（二维码太小时）
    big = cv2.resize(gray, (int(w * 1.5), int(h * 1.5)))
    results |= _decode(detector, big)

    # 6. zxing-cpp 兜底（识别率更高）
    if not results:
        try:
            import zxingcpp
            found = zxingcpp.read_barcodes(img)
            results |= {b.text for b in found if b.text.strip()}
        except Exception:
            pass

    return list(results)
