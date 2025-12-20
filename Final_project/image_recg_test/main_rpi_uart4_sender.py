import cv2
import mediapipe as mp
import time
import os
import sys
import serial
import numpy as np
from picamera2 import Picamera2

# ===================================================
# 0. 環境和初始化設置
# ===================================================

# 圖形化環境設定
os.environ['QT_QPA_PLATFORM'] = 'xcb' 
WIDTH, HEIGHT = 640, 480
FPS = 30 
TARGET_SIZE = 64  # STM32 模型輸入大小

# ---------------------------------------------------
# MediaPipe 初始化
# ---------------------------------------------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# ---------------------------------------------------
# UART 初始化
# ---------------------------------------------------
try:
    # 🌟 保持使用 /dev/serial0 (RPi 的硬體 UART), 鮑率 115200 bps
    # 此埠將連接到 STM32 的 UART4 (PA0/PA1 或 Arduino D1/D0)
    ser = serial.Serial('/dev/serial0', 115200, timeout=1)
    print("✅ UART 連接成功: /dev/serial0 @ 115200 bps (目標: STM32 UART4)")
except serial.SerialException as e:
    print(f"❌ UART 連接失敗: {e}")
    ser = None

# ---------------------------------------------------
# Picamera2 相機初始化
# ---------------------------------------------------
try:
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(
        main={"size": (WIDTH, HEIGHT)}, raw=None, controls={"FrameRate": FPS}
    ))
    picam2.start()
    time.sleep(1)
    print("✅ Picamera2 攝影機服務啟動成功。")
except Exception as e:
    print(f"❌ Picamera2 啟動失敗：{e}")
    sys.exit(1)

# ---------------------------------------------------
# OpenCV 視窗初始化
# ---------------------------------------------------
WINDOW_NAME = 'RPi Hand Tracking & Sender'
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)

# ===================================================
# 1. 影像處理輔助函式 (不變)
# ===================================================

def resize_and_pad_gray(img, target_size):
    """轉灰階並保持比例縮放至 target_size，補黑邊"""
    if len(img.shape) > 2:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
    h, w = img.shape[:2]
    scale = target_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((target_size, target_size), dtype=np.uint8)
    
    x_offset = (target_size - new_w) // 2
    y_offset = (target_size - new_h) // 2
    
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    return canvas

def send_image_via_uart(processed_img):
    """將 64x64 影像轉為 Float32 並透過 UART 發送 (16384 bytes)"""
    if ser:
        try:
            float_data = processed_img.astype(np.float32)
            bytes_to_send = float_data.tobytes()
            
            print(f"🚀 [傳送中] 發送影像資料: {len(bytes_to_send)} bytes (Float32)...")
            ser.write(bytes_to_send)
            print("✅ [傳送完成]")
        except Exception as e:
            print(f"❌ UART 發送錯誤: {e}")
    else:
        print("⚠️ UART 未連接，無法發送影像。")

# ===================================================
# 2. 主迴圈
# ===================================================

print("--- 程式運行中：全程預覽骨架，每 10 秒傳送一次資料 ---")
next_capture_time = time.time() + 10.0 
last_sent_preview = None 

try:
    while True:
        # A. 每一幀都執行：抓圖 + MediaPipe 偵測
        frame_array = picam2.capture_array()
        frame = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = hands.process(rgb_frame)
        
        bbox = None
        current_hand_crop = None
        
        # 繪製骨架
        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
            
            # 計算 Bounding Box
            h_img, w_img, _ = frame.shape
            xs = [lm.x for lm in hand.landmark]
            ys = [lm.y for lm in hand.landmark]
            
            x_vals = [int(x * w_img) for x in xs]
            y_vals = [int(y * h_img) for y in ys]
            
            box_w = max(x_vals) - min(x_vals)
            box_h = max(y_vals) - min(y_vals)
            
            mx, my = int(box_w * 0.2), int(box_h * 0.2)
            xmin, xmax = max(0, min(x_vals)-mx), min(w_img, max(x_vals)+mx)
            ymin, ymax = max(0, min(y_vals)-my), min(h_img, max(y_vals)+my)
            
            if xmax > xmin and ymax > ymin:
                bbox = (xmin, ymin, xmax, ymax)
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                current_hand_crop = frame[ymin:ymax, xmin:xmax]

        # B. 檢查時間：是否到達傳送時刻 (每 10 秒)
        current_time = time.time()
        
        if current_time >= next_capture_time:
            print(f"\n⏰ 時間到 ({time.strftime('%H:%M:%S')}) - 準備傳送...")
            
            if current_hand_crop is not None:
                # 執行前處理
                processed_img = resize_and_pad_gray(current_hand_crop, TARGET_SIZE)
                
                # 更新左上角的預覽縮圖
                last_sent_preview = cv2.cvtColor(processed_img, cv2.COLOR_GRAY2BGR)
                
                # 執行 UART 傳送
                send_image_via_uart(processed_img)
            else:
                print("⚠️ 時間到但未偵測到手部，本次跳過。")
            
            # 設定下一次傳送時間
            next_capture_time = current_time + 10.0

        # C. 顯示資訊與畫面
        remaining = max(0, next_capture_time - current_time)
        cv2.putText(frame, f"Next Send: {remaining:.1f}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # 顯示最後一次傳送的縮圖
        if last_sent_preview is not None:
            frame[0:64, 0:64] = last_sent_preview
            cv2.rectangle(frame, (0,0), (64,64), (0,0,255), 2)
            cv2.putText(frame, "Sent", (0, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

        cv2.imshow(WINDOW_NAME, frame)
        
        key = cv2.waitKey(1) 
        if key & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    pass
except Exception as e:
    print(f"主迴圈發生嚴重錯誤: {e}")

finally:
    print("\n--- 程式退出中，釋放資源 ---")
    picam2.stop()
    cv2.destroyAllWindows()
    if ser:
        ser.close()
    print("✅ 程式已安全退出。")