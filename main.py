import tkinter as tk
from tkinter import ttk
import time

# -----------------------------
# Initial Vehicle Parameters
# -----------------------------
speed = 0
soc = 100
temperature = 30
torque = 0
drive_enabled = True

# -----------------------------
# Main Window
# -----------------------------
root = tk.Tk()
root.title("EV CAN Simulator")
root.geometry("500x600")

# -----------------------------
# Labels
# -----------------------------
title_label = tk.Label(
    root,
    text="EV CAN Simulator",
    font=("Arial", 20, "bold")
)
title_label.pack(pady=10)

speed_label = tk.Label(
    root,
    text="Speed: 0 km/h",
    font=("Arial", 14)
)
speed_label.pack()

soc_label = tk.Label(
    root,
    text="Battery SOC: 100 %",
    font=("Arial", 14)
)
soc_label.pack()

temp_label = tk.Label(
    root,
    text="Temperature: 30 °C",
    font=("Arial", 14)
)
temp_label.pack()

torque_label = tk.Label(
    root,
    text="Torque: 0 Nm",
    font=("Arial", 14)
)
torque_label.pack()

status_label = tk.Label(
    root,
    text="Status: DRIVE ENABLED",
    fg="green",
    font=("Arial", 14, "bold")
)
status_label.pack(pady=10)

mode_label = tk.Label(
    root,
    text="Drive Mode: ECO",
    fg="blue",
    font=("Arial", 12, "bold")
)
mode_label.pack()

# -----------------------------
# CAN Message Box
# -----------------------------
can_box = tk.Text(root, height=12, width=50)
can_box.pack(pady=10)

# -----------------------------
# Throttle Slider
# -----------------------------
throttle_label = tk.Label(root, text="Throttle")
throttle_label.pack()

throttle_slider = ttk.Scale(
    root,
    from_=0,
    to=100,
    orient="horizontal",
    length=300
)
throttle_slider.pack()

# -----------------------------
# Update Simulation
# -----------------------------
def update_simulation():

    global speed
    global soc
    global temperature
    global torque
    global drive_enabled

    throttle = throttle_slider.get()

    if drive_enabled:

        # Drive Modes
        if throttle < 30:
            mode_label.config(
                text="Drive Mode: ECO",
                fg="blue"
            )

        elif throttle < 70:
            mode_label.config(
                text="Drive Mode: NORMAL",
                fg="orange"
            )

        else:
            mode_label.config(
                text="Drive Mode: SPORT",
                fg="red"
            )

        # Vehicle Logic
        torque = int(throttle * 2)

        speed += throttle * 0.02

        if speed > 120:
            speed = 120

        soc -= throttle * 0.0005

        temperature += throttle * 0.002

    else:
        torque = 0
        speed *= 0.95

    # Fault Conditions
    if temperature > 60 or soc < 20:
        drive_enabled = False

        status_label.config(
            text="Status: DRIVE DISABLED",
            fg="red"
        )

    # Update Labels
    speed_label.config(
        text=f"Speed: {int(speed)} km/h"
    )

    soc_label.config(
        text=f"Battery SOC: {int(soc)} %"
    )

    temp_label.config(
        text=f"Temperature: {int(temperature)} °C"
    )

    torque_label.config(
        text=f"Torque: {torque} Nm"
    )

    # CAN Message
    current_time = time.strftime("%H:%M:%S")

    can_message = f"""
Time: {current_time}

CAN ID: 0x120
Throttle: {int(throttle)} %
Torque: {torque} Nm
Speed: {int(speed)} km/h
SOC: {int(soc)} %
Temp: {int(temperature)} C

-------------------------
"""

    can_box.insert(tk.END, can_message)
    can_box.see(tk.END)

    # Repeat Loop
    root.after(500, update_simulation)

# -----------------------------
# Fault Injection
# -----------------------------
def inject_fault():
    global temperature

    temperature = 70

# -----------------------------
# Reset System
# -----------------------------
def reset_system():

    global speed
    global soc
    global temperature
    global torque
    global drive_enabled

    speed = 0
    soc = 100
    temperature = 30
    torque = 0
    drive_enabled = True

    status_label.config(
        text="Status: DRIVE ENABLED",
        fg="green"
    )

# -----------------------------
# Buttons
# -----------------------------
fault_button = tk.Button(
    root,
    text="Inject Overtemperature Fault",
    bg="red",
    fg="white",
    command=inject_fault
)
fault_button.pack(pady=10)

reset_button = tk.Button(
    root,
    text="Reset System",
    bg="green",
    fg="white",
    command=reset_system
)
reset_button.pack(pady=5)

# -----------------------------
# Start Simulation
# -----------------------------
update_simulation()

root.mainloop()