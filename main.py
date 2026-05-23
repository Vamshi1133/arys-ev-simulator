import tkinter as tk
from tkinter import ttk
import time
import csv
import os
import random

# =====================================
# INITIAL VEHICLE PARAMETERS
# =====================================

speed = 0
soc = 100
temperature = 30
torque = 0
rpm = 0

drive_enabled = False
charging = False
regen_active = False

# =====================================
# CSV LOGGING SETUP
# =====================================

log_file = "logs/telemetry.csv"

if not os.path.exists(log_file):

    with open(log_file, mode="w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "Time",
            "Speed",
            "SOC",
            "Temperature",
            "Torque",
            "RPM",
            "Throttle",
            "DriveMode"
        ])

# =====================================
# MAIN WINDOW
# =====================================

root = tk.Tk()

root.title("EV Powertrain Dashboard")

root.geometry("1100x750")

root.configure(bg="#111111")

# =====================================
# TITLE
# =====================================

title_label = tk.Label(
    root,
    text="EV POWERTRAIN CONTROL DASHBOARD",
    font=("Segoe UI", 24, "bold"),
    fg="cyan",
    bg="#111111"
)

title_label.pack(pady=20)

# =====================================
# MAIN FRAME
# =====================================

main_frame = tk.Frame(root, bg="#111111")
main_frame.pack()

left_frame = tk.Frame(main_frame, bg="#111111")
left_frame.grid(row=0, column=0, padx=20)

right_frame = tk.Frame(main_frame, bg="#111111")
right_frame.grid(row=0, column=1, padx=20)

# =====================================
# SPEED DISPLAY
# =====================================

speed_label = tk.Label(
    left_frame,
    text="0 km/h",
    font=("Segoe UI", 40, "bold"),
    fg="cyan",
    bg="#111111"
)

speed_label.pack(pady=10)

# =====================================
# RPM DISPLAY
# =====================================

rpm_label = tk.Label(
    left_frame,
    text="Motor RPM: 0",
    font=("Segoe UI", 18),
    fg="orange",
    bg="#111111"
)

rpm_label.pack()

# =====================================
# TORQUE DISPLAY
# =====================================

torque_label = tk.Label(
    left_frame,
    text="Torque: 0 Nm",
    font=("Segoe UI", 18),
    fg="white",
    bg="#111111"
)

torque_label.pack()

# =====================================
# TEMPERATURE DISPLAY
# =====================================

temp_label = tk.Label(
    left_frame,
    text="Temperature: 30 °C",
    font=("Segoe UI", 18),
    fg="white",
    bg="#111111"
)

temp_label.pack()

# =====================================
# BATTERY DISPLAY
# =====================================

soc_label = tk.Label(
    left_frame,
    text="Battery SOC: 100%",
    font=("Segoe UI", 18),
    fg="lime",
    bg="#111111"
)

soc_label.pack(pady=10)

battery_bar = ttk.Progressbar(
    left_frame,
    orient="horizontal",
    length=300,
    mode="determinate"
)

battery_bar.pack(pady=5)

battery_bar["value"] = 100

# =====================================
# DRIVE MODE DISPLAY
# =====================================

mode_label = tk.Label(
    left_frame,
    text="Drive Mode: ECO",
    font=("Segoe UI", 18, "bold"),
    fg="skyblue",
    bg="#111111"
)

mode_label.pack(pady=10)

# =====================================
# STATUS LABEL
# =====================================

status_label = tk.Label(
    left_frame,
    text="IGNITION OFF",
    font=("Segoe UI", 18, "bold"),
    fg="red",
    bg="#111111"
)

status_label.pack(pady=10)

# =====================================
# THROTTLE CONTROL
# =====================================

throttle_title = tk.Label(
    left_frame,
    text="Throttle Control",
    font=("Segoe UI", 14),
    fg="white",
    bg="#111111"
)

throttle_title.pack()

throttle_slider = ttk.Scale(
    left_frame,
    from_=0,
    to=100,
    orient="horizontal",
    length=350
)

throttle_slider.pack(pady=10)

# =====================================
# CAN TERMINAL
# =====================================

terminal_title = tk.Label(
    right_frame,
    text="LIVE CAN TELEMETRY",
    font=("Segoe UI", 16, "bold"),
    fg="lime",
    bg="#111111"
)

terminal_title.pack()

can_box = tk.Text(
    right_frame,
    height=30,
    width=50,
    bg="black",
    fg="lime",
    font=("Consolas", 10)
)

can_box.pack()

# =====================================
# FAULT INDICATORS
# =====================================

fault_label = tk.Label(
    right_frame,
    text="SYSTEM STATUS: NORMAL",
    font=("Segoe UI", 16, "bold"),
    fg="lime",
    bg="#111111"
)

fault_label.pack(pady=10)

# =====================================
# LOGGING FUNCTION
# =====================================

def log_telemetry(throttle, mode):

    current_time = time.strftime("%H:%M:%S")

    with open(log_file, mode="a", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            current_time,
            int(speed),
            int(soc),
            int(temperature),
            torque,
            rpm,
            int(throttle),
            mode
        ])

# =====================================
# IGNITION SYSTEM
# =====================================

def start_vehicle():

    global drive_enabled

    drive_enabled = True

    status_label.config(
        text="VEHICLE ACTIVE",
        fg="lime"
    )

def stop_vehicle():

    global drive_enabled

    drive_enabled = False

    status_label.config(
        text="IGNITION OFF",
        fg="red"
    )

# =====================================
# CHARGING MODE
# =====================================

def toggle_charging():

    global charging

    charging = not charging

# =====================================
# FAULT INJECTION
# =====================================

def inject_fault():

    global temperature

    temperature = 75

# =====================================
# RESET SYSTEM
# =====================================

def reset_system():

    global speed
    global soc
    global temperature
    global torque
    global rpm
    

    speed = 0
    soc = 100
    temperature = 30
    torque = 0
    rpm = 0

    fault_label.config(
        text="SYSTEM STATUS: NORMAL",
        fg="lime"
    )

# =====================================
# BUTTONS
# =====================================

button_frame = tk.Frame(left_frame, bg="#111111")
button_frame.pack(pady=20)

start_button = tk.Button(
    button_frame,
    text="START",
    bg="green",
    fg="white",
    width=12,
    command=start_vehicle
)

start_button.grid(row=0, column=0, padx=5)

stop_button = tk.Button(
    button_frame,
    text="STOP",
    bg="red",
    fg="white",
    width=12,
    command=stop_vehicle
)

stop_button.grid(row=0, column=1, padx=5)

charge_button = tk.Button(
    button_frame,
    text="CHARGE",
    bg="blue",
    fg="white",
    width=12,
    command=toggle_charging
)

charge_button.grid(row=1, column=0, pady=10)

fault_button = tk.Button(
    button_frame,
    text="INJECT FAULT",
    bg="orange",
    fg="black",
    width=12,
    command=inject_fault
)

fault_button.grid(row=1, column=1)

reset_button = tk.Button(
    button_frame,
    text="RESET",
    bg="white",
    fg="black",
    width=12,
    command=reset_system
)

reset_button.grid(row=2, column=0, columnspan=2, pady=10)

# =====================================
# MAIN SIMULATION LOOP
# =====================================

def update_simulation():

    global speed
    global soc
    global temperature
    global torque
    global rpm
    global regen_active
    global drive_enabled
    global charging

    throttle = throttle_slider.get()

    mode = "ECO"

    if drive_enabled:

        if throttle < 30:

            mode = "ECO"

            mode_label.config(
                text="Drive Mode: ECO",
                fg="skyblue"
            )

        elif throttle < 70:

            mode = "NORMAL"

            mode_label.config(
                text="Drive Mode: NORMAL",
                fg="orange"
            )

        else:

            mode = "SPORT"

            mode_label.config(
                text="Drive Mode: SPORT",
                fg="red"
            )

        torque = int(throttle * 2)

        speed += throttle * 0.03

        if speed > 180:
            speed = 180

        rpm = int(speed * 85)

        soc -= throttle * 0.0007

        temperature += throttle * 0.003

        regen_active = False

    else:

        torque = 0

        speed *= 0.97

        rpm = int(speed * 85)

        regen_active = True

    # Charging Mode
    if charging:

        soc += 0.05

        if soc > 100:
            soc = 100

    # Fault Conditions
    if temperature > 60:

        drive_enabled = False

        fault_label.config(
            text="SYSTEM STATUS: OVERTEMPERATURE FAULT",
            fg="red"
        )

    # UI Updates
    speed_label.config(
        text=f"{int(speed)} km/h"
    )

    rpm_label.config(
        text=f"Motor RPM: {rpm}"
    )

    torque_label.config(
        text=f"Torque: {torque} Nm"
    )

    temp_label.config(
        text=f"Temperature: {int(temperature)} °C"
    )

    soc_label.config(
        text=f"Battery SOC: {int(soc)}%"
    )

    battery_bar["value"] = soc

    # CAN Message
    current_time = time.strftime("%H:%M:%S")

    can_message = f"""
TIME : {current_time}

CAN ID      : 0x120
THROTTLE    : {int(throttle)} %
TORQUE      : {torque} Nm
SPEED       : {int(speed)} km/h
RPM         : {rpm}
BATTERY SOC : {int(soc)} %
TEMP        : {int(temperature)} C
MODE        : {mode}
REGEN       : {regen_active}

-----------------------------------
"""

    can_box.insert(tk.END, can_message)

    can_box.see(tk.END)

    # Log Telemetry
    log_telemetry(throttle, mode)

    # Repeat Loop
    root.after(500, update_simulation)

# =====================================
# START LOOP
# =====================================

update_simulation()

root.mainloop()