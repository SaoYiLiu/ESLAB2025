import serial
import matplotlib.pyplot as plt

# ===== UART 設定 =====
PORT = "COM6"        # ⚠️ 改成你的 STM32 COM port
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)

# ===== 手勢定義 =====
labels = ["K", "L", "O"]
values = [0.0, 0.0, 0.0]

# ===== Matplotlib 初始化 =====
plt.ion()
fig, ax = plt.subplots()
bars = ax.bar(labels, values)
ax.set_ylim(0, 1)
ax.set_ylabel("Probability")
ax.set_title("Gesture Recognition")

print("Listening...")

while True:
    line = ser.readline().decode(errors="ignore").strip()
    if not line:
        continue

    try:
        # 期望格式: 0.1,0.8,0.1
        values = list(map(float, line.split(",")))
        if len(values) != 3:
            continue

        # 更新 bar
        for bar, v in zip(bars, values):
            bar.set_height(v)

        # 找最大機率
        pred_idx = values.index(max(values))
        pred_label = labels[pred_idx]

        ax.set_title(
            f"Predict: {pred_label} | "
            f"K={values[0]*100:.1f}%  "
            f"L={values[1]*100:.1f}%  "
            f"O={values[2]*100:.1f}%"
        )

        plt.pause(0.05)

    except ValueError:
        # 避免亂碼行
        continue
