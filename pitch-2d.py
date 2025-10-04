import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# ----- CONFIG -----
PORT = 'COM17'
BAUD = 115200
WINDOW = 200

ser = serial.Serial(PORT, BAUD, timeout=1)

pitch_buf = deque(maxlen=WINDOW)
x_idx     = deque(maxlen=WINDOW)

# --- Figure setup ---
fig, ax = plt.subplots(figsize=(10,5))
(line_pitch,) = ax.plot([], [], label="Pitch (°)", color='blue')
ax.set_xlim(0, WINDOW)
ax.set_ylim(-90, 90)
ax.set_xlabel("Samples")
ax.set_ylabel("Pitch Angle (°)")
ax.set_title("2) A Python script that reads the serial data and visualizes pitch only in 2D")
ax.legend(loc="upper right")

# --- Parse incoming serial line ---
def parse_line(line):
    try:
        parts = line.strip().split(',')
        if len(parts) < 1:
            return None
        return float(parts[0])   # Only pitch is used
    except:
        return None

# --- Init function for animation ---
def init():
    line_pitch.set_data([], [])
    return line_pitch,

# --- Update function ---
def update(frame):
    for _ in range(5):  # read a few samples per frame
        raw = ser.readline().decode(errors='ignore')
        if not raw:
            break
        pitch = parse_line(raw)
        if pitch is None:
            continue
        pitch_buf.append(pitch)
        x_idx.append(len(x_idx)+1 if x_idx else 1)

    xs = list(range(len(x_idx)))
    line_pitch.set_data(xs, list(pitch_buf))
    ax.set_xlim(max(0, len(xs)-WINDOW), max(WINDOW, len(xs)))
    return line_pitch,

ani = animation.FuncAnimation(fig, update, init_func=init, interval=30, blit=False)
plt.tight_layout()
plt.show()
