import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection

# ----- CONFIG -----
PORT = 'COM17'
BAUD = 115200
WINDOW = 200

ser = serial.Serial(PORT, BAUD, timeout=1)

pitch_buf = deque(maxlen=WINDOW)
roll_buf  = deque(maxlen=WINDOW)
x_idx     = deque(maxlen=WINDOW)

# Bigger figure
fig = plt.figure(figsize=(12,8))

# --- Top: time series ---
ax1 = fig.add_subplot(2,1,1)
(line_pitch,) = ax1.plot([], [], label="Pitch (°)", color='blue')
(line_roll,)  = ax1.plot([], [], label="Roll (°)", color='red')
ax1.set_xlim(0, WINDOW)
ax1.set_ylim(-90, 90)
ax1.set_xlabel("Samples")
ax1.set_ylabel("Angle (°)")
ax1.set_title("MPU6050 Pitch & Roll")
ax1.legend(loc="upper right")

# --- Bottom: 3D chair ---
ax2 = fig.add_subplot(2,1,2, projection='3d')
ax2.set_xlim([-2,2])
ax2.set_ylim([-2,2])
ax2.set_zlim([0,2])
ax2.set_title("3D Chair Orientation")
ax2.view_init(elev=20, azim=30)
ax2.set_box_aspect([1,1,1])  # Equal aspect

# --- Chair components ---
# Seat (centered)
seat = np.array([
    [-1.0, -0.5, 1.0],  # back-left
    [ 1.0, -0.5, 1.0],  # back-right
    [ 1.0,  0.5, 1.0],  # front-right
    [-1.0,  0.5, 1.0]   # front-left
])
seat_faces = [[seat[j] for j in [0,1,2,3]]]
seat_patch = Poly3DCollection(seat_faces, facecolor='green', alpha=0.7, edgecolor='black')
ax2.add_collection3d(seat_patch)

# Backrest
backrest = np.array([
    [-1.0, -0.5, 1.0],  # bottom-left
    [ 1.0, -0.5, 1.0],  # bottom-right
    [ 1.0, -0.5, 2.0],  # top-right
    [-1.0, -0.5, 2.0]   # top-left
])
backrest_faces = [[backrest[j] for j in [0,1,2,3]]]
backrest_patch = Poly3DCollection(backrest_faces, facecolor='blue', alpha=0.7, edgecolor='black')
ax2.add_collection3d(backrest_patch)

# Chair legs (lines)
leg_coords = [
    [[-1.0, -0.5, 0], [-1.0, -0.5, 1.0]],
    [[ 1.0, -0.5, 0], [ 1.0, -0.5, 1.0]],
    [[ 1.0,  0.5, 0], [ 1.0,  0.5, 1.0]],
    [[-1.0,  0.5, 0], [-1.0,  0.5, 1.0]]
]
legs = Line3DCollection(leg_coords, colors='brown', linewidths=3)
ax2.add_collection3d(legs)

# Front marker
marker = ax2.scatter([0], [0.5], [1.05], color='red', s=80, label="Front")

# Floor grid
floor_x = [-2,2]
floor_y = [-2,2]
ax2.plot([floor_x[0], floor_x[1]], [0,0], [0,0], color='gray', linestyle='--')
ax2.plot([0,0], [floor_y[0], floor_y[1]], [0,0], color='gray', linestyle='--')

# --- Rotation ---
def rotation_matrix(pitch, roll):
    pitch_rad = np.radians(pitch)
    roll_rad  = np.radians(roll)
    Rx = np.array([[1,0,0],
                   [0,np.cos(pitch_rad), -np.sin(pitch_rad)],
                   [0,np.sin(pitch_rad),  np.cos(pitch_rad)]])
    Ry = np.array([[np.cos(roll_rad),0,np.sin(roll_rad)],
                   [0,1,0],
                   [-np.sin(roll_rad),0,np.cos(roll_rad)]])
    return Ry @ Rx

def parse_line(line):
    try:
        parts = line.strip().split(',')
        if len(parts)!=2:
            return None, None
        return float(parts[0]), float(parts[1])
    except:
        return None, None

def init():
    line_pitch.set_data([], [])
    line_roll.set_data([], [])
    return line_pitch, line_roll, seat_patch, backrest_patch, marker

def update(frame):
    for _ in range(5):
        raw = ser.readline().decode(errors='ignore')
        if not raw: break
        pitch, roll = parse_line(raw)
        if pitch is None: continue
        pitch_buf.append(pitch)
        roll_buf.append(roll)
        x_idx.append(len(x_idx)+1 if x_idx else 1)

    xs = list(range(len(x_idx)))
    line_pitch.set_data(xs, list(pitch_buf))
    line_roll.set_data(xs, list(roll_buf))
    ax1.set_xlim(max(0,len(xs)-WINDOW), max(WINDOW,len(xs)))

    if pitch_buf and roll_buf:
        R = rotation_matrix(pitch_buf[-1], roll_buf[-1])
        # Rotate seat
        rotated_seat = seat @ R.T
        seat_patch.set_verts([[rotated_seat[j] for j in [0,1,2,3]]])
        # Rotate backrest
        rotated_back = backrest @ R.T
        backrest_patch.set_verts([[rotated_back[j] for j in [0,1,2,3]]])
        # Rotate marker
        front_marker = np.array([0,0.5,1.05]) @ R.T
        marker._offsets3d = ([front_marker[0]], [front_marker[1]], [front_marker[2]])
        # Rotate legs
        rotated_legs = [np.array([coord[0], coord[1]]) @ R.T for coord in leg_coords]
        legs.set_segments(rotated_legs)

    return line_pitch, line_roll, seat_patch, backrest_patch, marker, legs

ani = animation.FuncAnimation(fig, update, init_func=init, interval=30, blit=False)
plt.tight_layout()
plt.show()
