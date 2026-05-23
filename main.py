"""
EV CAN Simulation Dashboard
Q5 - Arys Garage Assignment
CAN Network: Throttle → VCU → BMS → MCU
"""

import tkinter as tk
from tkinter import ttk, font
import math, time, csv, os, random, threading

# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
BG_DARK   = "#0A0E17"
BG_PANEL  = "#111827"
BG_CARD   = "#1A2235"
BG_CARD2  = "#1E2940"
ACCENT    = "#00D4FF"       # cyan
ACCENT2   = "#39FF14"       # neon-green  (SOC)
WARN      = "#FF6B35"       # orange
DANGER    = "#FF2D55"       # red
GOLD      = "#FFD700"
BORDER    = "#2A3A55"
TEXT_PRI  = "#E8F0FE"
TEXT_SEC  = "#7A8FAF"
PURPLE    = "#A855F7"       # regen
TEAL      = "#14B8A6"

# ─────────────────────────────────────────────
#  SIMULATION STATE
# ─────────────────────────────────────────────
class SimState:
    def __init__(self):
        self.speed       = 0.0
        self.soc         = 100.0
        self.temperature = 30.0
        self.torque      = 0.0
        self.rpm         = 0.0
        self.accel       = 0.0
        self.g_force     = 0.0
        self.distance    = 0.0   # km
        self.drive_on    = False
        self.charging    = False
        self.regen_active= False
        self.fault       = False
        self.fault_msg   = ""
        self.mode        = "ECO"
        self.throttle    = 0.0
        self.brake       = 0.0
        self.prev_speed  = 0.0
        self.lap_time    = 0.0
        self.lap_start   = None
        self.best_lap    = None
        self.lap_count   = 0
        self.bms_ok      = True
        self.mcu_ok      = True
        self.vcu_ok      = True
        self.can_id      = "0x120"
        # time-series (last N points)
        self.N = 60
        self.t_arr   = []
        self.spd_arr = []
        self.soc_arr = []
        self.tmp_arr = []
        self.regen_arr = []
        self.tick    = 0

sim = SimState()

# ─────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
LOG_FILE = "logs/ev_telemetry.csv"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        csv.writer(f).writerow([
            "Time","Speed_kmh","SOC_%","Temp_C",
            "Torque_Nm","RPM","Throttle_%","Brake_%",
            "Mode","G_Force","Distance_km","CAN_ID"
        ])

def log_data():
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([
            time.strftime("%H:%M:%S"),
            round(sim.speed,2), round(sim.soc,2),
            round(sim.temperature,2), round(sim.torque,2),
            int(sim.rpm), round(sim.throttle,1), round(sim.brake,1),
            sim.mode, round(sim.g_force,3),
            round(sim.distance,3), sim.can_id
        ])

# ─────────────────────────────────────────────
#  ROOT WINDOW
# ─────────────────────────────────────────────
root = tk.Tk()
root.title("EV CAN Simulation  |  Arys Garage")
root.configure(bg=BG_DARK)
root.state("zoomed")
root.resizable(True, True)

try:
    root.tk.call("tk", "scaling", 1.2)
except Exception:
    pass

# ─────────────────────────────────────────────
#  FONTS
# ─────────────────────────────────────────────
F_TITLE   = ("Courier New", 13, "bold")
F_HUGE    = ("Courier New", 52, "bold")
F_BIG     = ("Courier New", 22, "bold")
F_MED     = ("Courier New", 13, "bold")
F_SMALL   = ("Courier New", 10)
F_TINY    = ("Courier New", 9)
F_MONO    = ("Consolas",    10)
F_MONO_S  = ("Consolas",    9)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def soc_color(v):
    if v > 60: return ACCENT2
    if v > 25: return GOLD
    return DANGER

def temp_color(v):
    if v < 45: return ACCENT2
    if v < 60: return WARN
    return DANGER

def speed_color(v):
    if v < 80: return ACCENT
    if v < 140: return GOLD
    return DANGER

def draw_arc_gauge(canvas, cx, cy, r, value, vmin, vmax,
                   color, bg_color, width=14, start_angle=220, extent=280):
    """Draw a smooth arc gauge on a Canvas widget."""
    canvas.delete("all")
    # background arc
    canvas.create_arc(
        cx-r, cy-r, cx+r, cy+r,
        start=start_angle, extent=-extent,
        style="arc", outline=BG_CARD2, width=width
    )
    # foreground arc
    pct   = max(0, min(1, (value - vmin) / (vmax - vmin)))
    sweep = pct * extent
    if sweep > 0:
        canvas.create_arc(
            cx-r, cy-r, cx+r, cy+r,
            start=start_angle, extent=-sweep,
            style="arc", outline=color, width=width
        )
    # tick marks
    for i in range(11):
        angle = math.radians(start_angle - (i / 10) * extent)
        ri = r - width//2 - 4
        ro = r + width//2 + 4
        x1 = cx + ri * math.cos(angle)
        y1 = cy - ri * math.sin(angle)
        x2 = cx + ro * math.cos(angle)
        y2 = cy - ro * math.sin(angle)
        canvas.create_line(x1, y1, x2, y2, fill=BORDER, width=1)

def draw_sparkline(canvas, data, color, w, h, fill=False):
    canvas.delete("all")
    canvas.create_rectangle(0, 0, w, h, fill=BG_CARD, outline="")
    if len(data) < 2:
        return
    mn, mx = min(data), max(data)
    span = mx - mn if mx != mn else 1
    pts = []
    for i, v in enumerate(data):
        x = i / (len(data)-1) * (w-4) + 2
        y = h - 4 - (v - mn) / span * (h-8)
        pts.append((x, y))
    if fill and len(pts) >= 2:
        poly = [(2, h-2)] + pts + [(w-2, h-2)]
        flat = [c for p in poly for c in p]
        canvas.create_polygon(flat, fill=color, stipple="gray25", outline="")
    for i in range(len(pts)-1):
        canvas.create_line(pts[i][0], pts[i][1],
                           pts[i+1][0], pts[i+1][1],
                           fill=color, width=2, smooth=True)

# ─────────────────────────────────────────────
#  LAYOUT FRAMES
# ─────────────────────────────────────────────
# Header
hdr = tk.Frame(root, bg=BG_DARK, height=52)
hdr.pack(fill="x", padx=0, pady=0)
hdr.pack_propagate(False)

# Body
body = tk.Frame(root, bg=BG_DARK)
body.pack(fill="both", expand=True, padx=8, pady=(0,8))

# Three columns
col_left   = tk.Frame(body, bg=BG_DARK, width=300)
col_center = tk.Frame(body, bg=BG_DARK)
col_right  = tk.Frame(body, bg=BG_DARK, width=340)

col_left.pack(side="left",  fill="y",    padx=(0,6))
col_center.pack(side="left", fill="both", expand=True, padx=3)
col_right.pack(side="left",  fill="y",   padx=(6,0))

col_left.pack_propagate(False)
col_right.pack_propagate(False)

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
tk.Label(hdr, text="⚡ EV CAN SIMULATION DASHBOARD",
         font=("Courier New",15,"bold"),
         fg=ACCENT, bg=BG_DARK).pack(side="left", padx=20, pady=10)

tk.Label(hdr, text="Throttle → VCU → BMS → MCU",
         font=F_SMALL, fg=TEXT_SEC, bg=BG_DARK).pack(side="left", padx=6)

# Status dots (right side of header)
hdr_right = tk.Frame(hdr, bg=BG_DARK)
hdr_right.pack(side="right", padx=20)

node_dots = {}
for node in ["BMS", "VCU", "MCU"]:
    fr = tk.Frame(hdr_right, bg=BG_DARK)
    fr.pack(side="left", padx=8)
    dot = tk.Label(fr, text="●", font=("Courier New",14), fg=ACCENT2, bg=BG_DARK)
    dot.pack(side="left")
    tk.Label(fr, text=node, font=F_TINY, fg=TEXT_SEC, bg=BG_DARK).pack(side="left", padx=2)
    node_dots[node] = dot

clock_lbl = tk.Label(hdr, font=F_SMALL, fg=TEXT_SEC, bg=BG_DARK)
clock_lbl.pack(side="right", padx=10)

# ─────────────────────────────────────────────
#  LEFT COLUMN — GAUGES + CONTROLS
# ─────────────────────────────────────────────
def make_card(parent, title, pady_inner=8):
    outer = tk.Frame(parent, bg=BG_CARD, bd=0,
                     highlightbackground=BORDER, highlightthickness=1)
    outer.pack(fill="x", pady=4, padx=2)
    tk.Label(outer, text=title, font=F_TINY, fg=TEXT_SEC, bg=BG_CARD).pack(anchor="w", padx=10, pady=(6,0))
    inner = tk.Frame(outer, bg=BG_CARD)
    inner.pack(fill="x", padx=8, pady=pady_inner)
    return inner

# ── Speed gauge ──
spd_card = tk.Frame(col_left, bg=BG_CARD,
                    highlightbackground=BORDER, highlightthickness=1)
spd_card.pack(fill="x", pady=4, padx=2)
tk.Label(spd_card, text="VEHICLE SPEED", font=F_TINY, fg=TEXT_SEC, bg=BG_CARD).pack(pady=(6,0))
spd_canvas = tk.Canvas(spd_card, width=280, height=160, bg=BG_CARD,
                        highlightthickness=0)
spd_canvas.pack()
spd_val_lbl = tk.Label(spd_card, text="0", font=F_HUGE, fg=ACCENT, bg=BG_CARD)
spd_val_lbl.pack()
tk.Label(spd_card, text="km/h", font=F_SMALL, fg=TEXT_SEC, bg=BG_CARD).pack(pady=(0,8))

# ── RPM gauge ──
rpm_card = tk.Frame(col_left, bg=BG_CARD,
                    highlightbackground=BORDER, highlightthickness=1)
rpm_card.pack(fill="x", pady=4, padx=2)
tk.Label(rpm_card, text="MOTOR RPM", font=F_TINY, fg=TEXT_SEC, bg=BG_CARD).pack(pady=(6,0))
rpm_canvas = tk.Canvas(rpm_card, width=280, height=100, bg=BG_CARD,
                        highlightthickness=0)
rpm_canvas.pack()
rpm_val_lbl = tk.Label(rpm_card, text="0 RPM", font=F_BIG, fg=WARN, bg=BG_CARD)
rpm_val_lbl.pack(pady=(0,6))

# ── Torque ──
trq_inner = make_card(col_left, "TORQUE  (Nm)")
trq_bar   = ttk.Progressbar(trq_inner, orient="horizontal", length=260,
                             mode="determinate", maximum=400)
trq_bar.pack(pady=2)
trq_lbl   = tk.Label(trq_inner, text="0 Nm", font=F_MED, fg=TEXT_PRI, bg=BG_CARD)
trq_lbl.pack()

# ── Drive mode ──
mode_inner = make_card(col_left, "DRIVE MODE")
mode_lbl = tk.Label(mode_inner, text="ECO", font=("Courier New",26,"bold"),
                    fg=ACCENT, bg=BG_CARD)
mode_lbl.pack()

# ── G-Force ──
gf_inner = make_card(col_left, "G-FORCE  /  ACCELERATION")
gf_row   = tk.Frame(gf_inner, bg=BG_CARD)
gf_row.pack()
gf_lbl   = tk.Label(gf_row, text="0.00 g", font=F_MED, fg=GOLD, bg=BG_CARD)
gf_lbl.pack(side="left", padx=10)
acc_lbl  = tk.Label(gf_row, text="0.00 m/s²", font=F_MED, fg=TEAL, bg=BG_CARD)
acc_lbl.pack(side="left", padx=10)

# ── Distance ──
dist_inner = make_card(col_left, "DISTANCE  /  LAP")
dist_row   = tk.Frame(dist_inner, bg=BG_CARD)
dist_row.pack()
dist_lbl = tk.Label(dist_row, text="0.000 km", font=F_MED, fg=TEXT_PRI, bg=BG_CARD)
dist_lbl.pack(side="left", padx=8)
lap_lbl  = tk.Label(dist_row, text="Lap —", font=F_MED, fg=PURPLE, bg=BG_CARD)
lap_lbl.pack(side="left", padx=8)

# ─────────────────────────────────────────────
#  CENTER COLUMN — SOC, TEMP, SPARKLINES, CAN
# ─────────────────────────────────────────────

# ── SOC ──
soc_card = tk.Frame(col_center, bg=BG_CARD,
                    highlightbackground=BORDER, highlightthickness=1)
soc_card.pack(fill="x", pady=4, padx=2)
soc_top  = tk.Frame(soc_card, bg=BG_CARD)
soc_top.pack(fill="x", padx=10, pady=(6,2))
tk.Label(soc_top, text="BATTERY SOC", font=F_TINY, fg=TEXT_SEC, bg=BG_CARD).pack(side="left")
soc_pct_lbl = tk.Label(soc_top, text="100%", font=F_BIG, fg=ACCENT2, bg=BG_CARD)
soc_pct_lbl.pack(side="right")

style = ttk.Style()
style.theme_use("clam")
style.configure("soc.Horizontal.TProgressbar",
                troughcolor=BG_CARD2, background=ACCENT2,
                bordercolor=BG_CARD, lightcolor=ACCENT2, darkcolor=ACCENT2)
style.configure("temp.Horizontal.TProgressbar",
                troughcolor=BG_CARD2, background=WARN,
                bordercolor=BG_CARD, lightcolor=WARN, darkcolor=WARN)
style.configure("brake.Horizontal.TProgressbar",
                troughcolor=BG_CARD2, background=DANGER,
                bordercolor=BG_CARD, lightcolor=DANGER, darkcolor=DANGER)

soc_bar = ttk.Progressbar(soc_card, orient="horizontal", length=500,
                           mode="determinate", maximum=100,
                           style="soc.Horizontal.TProgressbar")
soc_bar.pack(padx=10, pady=(0,6))
soc_bar["value"] = 100

soc_spark_canvas = tk.Canvas(soc_card, width=500, height=40,
                              bg=BG_CARD, highlightthickness=0)
soc_spark_canvas.pack(padx=10, pady=(0,6))

# ── Temperature ──
temp_card = tk.Frame(col_center, bg=BG_CARD,
                     highlightbackground=BORDER, highlightthickness=1)
temp_card.pack(fill="x", pady=4, padx=2)
temp_top = tk.Frame(temp_card, bg=BG_CARD)
temp_top.pack(fill="x", padx=10, pady=(6,2))
tk.Label(temp_top, text="MOTOR TEMPERATURE", font=F_TINY, fg=TEXT_SEC, bg=BG_CARD).pack(side="left")
temp_val_lbl = tk.Label(temp_top, text="30 °C", font=F_BIG, fg=ACCENT2, bg=BG_CARD)
temp_val_lbl.pack(side="right")
temp_bar = ttk.Progressbar(temp_card, orient="horizontal", length=500,
                            mode="determinate", maximum=100,
                            style="temp.Horizontal.TProgressbar")
temp_bar.pack(padx=10, pady=(0,4))
temp_spark_canvas = tk.Canvas(temp_card, width=500, height=40,
                               bg=BG_CARD, highlightthickness=0)
temp_spark_canvas.pack(padx=10, pady=(0,6))

# ── Speed sparkline ──
spd_spark_card = tk.Frame(col_center, bg=BG_CARD,
                           highlightbackground=BORDER, highlightthickness=1)
spd_spark_card.pack(fill="x", pady=4, padx=2)
tk.Label(spd_spark_card, text="SPEED TELEMETRY", font=F_TINY, fg=TEXT_SEC, bg=BG_CARD).pack(anchor="w", padx=10, pady=(6,2))
spd_spark_canvas = tk.Canvas(spd_spark_card, width=500, height=60,
                              bg=BG_CARD, highlightthickness=0)
spd_spark_canvas.pack(padx=10, pady=(0,6))

# ── Throttle / Brake sliders ──
ctrl_card = make_card(col_center, "DRIVER INPUTS", pady_inner=10)

th_row = tk.Frame(ctrl_card, bg=BG_CARD)
th_row.pack(fill="x", pady=3)
tk.Label(th_row, text="THROTTLE", font=F_TINY, fg=TEXT_SEC, bg=BG_CARD, width=10, anchor="w").pack(side="left")
throttle_var = tk.DoubleVar(value=0)
throttle_slider = ttk.Scale(th_row, from_=0, to=100, orient="horizontal",
                             variable=throttle_var, length=340)
throttle_slider.pack(side="left", padx=6)
th_pct_lbl = tk.Label(th_row, text="0%", font=F_TINY, fg=ACCENT, bg=BG_CARD, width=6)
th_pct_lbl.pack(side="left")

br_row = tk.Frame(ctrl_card, bg=BG_CARD)
br_row.pack(fill="x", pady=3)
tk.Label(br_row, text="BRAKE", font=F_TINY, fg=TEXT_SEC, bg=BG_CARD, width=10, anchor="w").pack(side="left")
brake_var = tk.DoubleVar(value=0)
brake_slider = ttk.Scale(br_row, from_=0, to=100, orient="horizontal",
                          variable=brake_var, length=340)
brake_slider.pack(side="left", padx=6)
br_pct_lbl = tk.Label(br_row, text="0%", font=F_TINY, fg=DANGER, bg=BG_CARD, width=6)
br_pct_lbl.pack(side="left")

# Brake progress bar
br_bar_row = tk.Frame(ctrl_card, bg=BG_CARD)
br_bar_row.pack(fill="x", pady=2)
tk.Label(br_bar_row, text="BRAKE FORCE", font=F_TINY, fg=TEXT_SEC, bg=BG_CARD, width=12, anchor="w").pack(side="left")
brake_bar = ttk.Progressbar(br_bar_row, orient="horizontal", length=350,
                             mode="determinate", maximum=100,
                             style="brake.Horizontal.TProgressbar")
brake_bar.pack(side="left")

# ── CAN Terminal ──
can_card = tk.Frame(col_center, bg=BG_CARD,
                    highlightbackground=BORDER, highlightthickness=1)
can_card.pack(fill="both", expand=True, pady=4, padx=2)
can_hdr_row = tk.Frame(can_card, bg=BG_CARD)
can_hdr_row.pack(fill="x", padx=10, pady=(6,2))
tk.Label(can_hdr_row, text="◉ LIVE CAN BUS TERMINAL", font=F_TINY,
         fg=ACCENT2, bg=BG_CARD).pack(side="left")
can_hz_lbl = tk.Label(can_hdr_row, text="2 Hz", font=F_TINY, fg=TEXT_SEC, bg=BG_CARD)
can_hz_lbl.pack(side="right")
can_box = tk.Text(can_card, height=10, bg="#050A10", fg=ACCENT2,
                  font=F_MONO, insertbackground=ACCENT2,
                  selectbackground=BORDER, relief="flat",
                  padx=6, pady=4, state="disabled")
can_box.pack(fill="both", expand=True, padx=6, pady=(0,6))

# tag colours inside terminal
can_box.config(state="normal")
can_box.tag_config("id",    foreground=GOLD)
can_box.tag_config("warn",  foreground=WARN)
can_box.tag_config("err",   foreground=DANGER)
can_box.tag_config("ok",    foreground=ACCENT2)
can_box.tag_config("label", foreground=TEXT_SEC)
can_box.config(state="disabled")

# ─────────────────────────────────────────────
#  RIGHT COLUMN — LED PANEL, BUTTONS, FAULT, STATUS
# ─────────────────────────────────────────────

# ── LED Panel ──
led_card = make_card(col_right, "SYSTEM STATUS INDICATORS")
led_grid = tk.Frame(led_card, bg=BG_CARD)
led_grid.pack()

def make_led(parent, text, row, col):
    fr = tk.Frame(parent, bg=BG_CARD2, bd=0,
                  highlightbackground=BORDER, highlightthickness=1,
                  padx=8, pady=6)
    fr.grid(row=row, column=col, padx=4, pady=4, ipadx=4)
    dot = tk.Label(fr, text="●", font=("Courier New", 18), fg="gray30", bg=BG_CARD2)
    dot.pack()
    lbl = tk.Label(fr, text=text, font=F_TINY, fg=TEXT_SEC, bg=BG_CARD2)
    lbl.pack()
    return dot

led_drive  = make_led(led_grid, "DRIVE",   0, 0)
led_charge = make_led(led_grid, "CHARGE",  0, 1)
led_regen  = make_led(led_grid, "REGEN",   0, 2)
led_fault  = make_led(led_grid, "FAULT",   0, 3)
led_bms    = make_led(led_grid, "BMS",     1, 0)
led_vcu    = make_led(led_grid, "VCU",     1, 1)
led_mcu    = make_led(led_grid, "MCU",     1, 2)
led_ovt    = make_led(led_grid, "OV-TEMP", 1, 3)

# ── Fault banner ──
fault_banner = tk.Label(col_right, text="● SYSTEM NOMINAL",
                        font=("Courier New", 11, "bold"),
                        fg=ACCENT2, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1,
                        pady=8)
fault_banner.pack(fill="x", padx=2, pady=4)

# ── Status box ──
status_card = make_card(col_right, "IGNITION / CHARGE STATUS")
status_lbl = tk.Label(status_card, text="IGNITION OFF",
                      font=("Courier New", 20, "bold"), fg=DANGER, bg=BG_CARD)
status_lbl.pack()

# ── Control buttons ──
btn_card = make_card(col_right, "CONTROLS")

def btn(parent, text, color, cmd, col, row=0, colspan=1):
    b = tk.Button(parent, text=text, font=F_TINY,
                  bg=color, fg="white" if color != "#FFFFFF" else "black",
                  activebackground=color, relief="flat",
                  cursor="hand2", command=cmd,
                  padx=8, pady=7, bd=0,
                  highlightthickness=0)
    b.grid(row=row, column=col, columnspan=colspan,
           padx=4, pady=4, sticky="ew")
    return b

btn_grid = tk.Frame(btn_card, bg=BG_CARD)
btn_grid.pack()
for c in range(3): btn_grid.columnconfigure(c, weight=1)

def start_vehicle():
    if sim.fault:
        return
    sim.drive_on = True
    sim.charging = False
    status_lbl.config(text="VEHICLE ACTIVE", fg=ACCENT2)
    if sim.lap_start is None:
        sim.lap_start = time.time()

def stop_vehicle():
    sim.drive_on = False
    status_lbl.config(text="IGNITION OFF", fg=DANGER)

def toggle_charge():
    if sim.drive_on: return
    sim.charging = not sim.charging
    status_lbl.config(
        text="CHARGING…" if sim.charging else "IGNITION OFF",
        fg=TEAL if sim.charging else DANGER
    )

def inject_fault():
    sim.temperature = 72
    sim.fault = True
    sim.fault_msg = "OVERTEMPERATURE FAULT"

def reset_system():
    sim.speed = 0; sim.soc = 100; sim.temperature = 30
    sim.torque = 0; sim.rpm = 0; sim.accel = 0; sim.g_force = 0
    sim.drive_on = False; sim.charging = False
    sim.fault = False; sim.fault_msg = ""
    sim.distance = 0; sim.lap_time = 0; sim.lap_start = None
    sim.bms_ok = True; sim.mcu_ok = True; sim.vcu_ok = True
    status_lbl.config(text="IGNITION OFF", fg=DANGER)
    fault_banner.config(text="● SYSTEM NOMINAL", fg=ACCENT2)
    throttle_var.set(0); brake_var.set(0)
    sim.t_arr.clear(); sim.spd_arr.clear()
    sim.soc_arr.clear(); sim.tmp_arr.clear()
    sim.regen_arr.clear()

def lap_reset():
    if sim.lap_start is not None:
        elapsed = time.time() - sim.lap_start
        sim.lap_count += 1
        if sim.best_lap is None or elapsed < sim.best_lap:
            sim.best_lap = elapsed
        sim.lap_start = time.time()

btn(btn_grid, "START",  "#145A32", start_vehicle, 0)
btn(btn_grid, "STOP",   "#7B241C", stop_vehicle,  1)
btn(btn_grid, "CHARGE", "#1A5276", toggle_charge, 2)

def btn2(parent, text, color, cmd, col):
    b = tk.Button(parent, text=text, font=F_TINY,
                  bg=color, fg="white",
                  activebackground=color, relief="flat",
                  cursor="hand2", command=cmd,
                  padx=8, pady=7, bd=0,
                  highlightthickness=0)
    b.grid(row=1, column=col, padx=4, pady=4, sticky="ew")
    return b

btn2(btn_grid, "INJECT FAULT", "#784212", inject_fault,  0)
btn2(btn_grid, "LAP RESET",    "#1A3A4A", lap_reset,     1)
btn2(btn_grid, "SYSTEM RESET", "#3D3D3D", reset_system,  2)

# ── CAN node details ──
node_card = make_card(col_right, "CAN NODE DETAILS")
node_txt  = tk.Text(node_card, height=9, bg="#050A10", fg=ACCENT,
                    font=F_MONO_S, relief="flat",
                    padx=6, pady=4, state="disabled")
node_txt.pack(fill="x")
node_txt.tag_config("h",    foreground=GOLD,    font=("Consolas",9,"bold"))
node_txt.tag_config("val",  foreground=TEXT_PRI)
node_txt.tag_config("dim",  foreground=TEXT_SEC)

# ── Mini stats ──
stats_card = make_card(col_right, "SESSION STATS")
stats_grid = tk.Frame(stats_card, bg=BG_CARD)
stats_grid.pack(fill="x")

def stat_row(parent, label, row):
    tk.Label(parent, text=label+":", font=F_TINY, fg=TEXT_SEC,
             bg=BG_CARD, anchor="w", width=16).grid(row=row, column=0, sticky="w", pady=2)
    v = tk.Label(parent, text="—", font=F_TINY, fg=TEXT_PRI,
                 bg=BG_CARD, anchor="e", width=14)
    v.grid(row=row, column=1, sticky="e")
    return v

sv_max_spd  = stat_row(stats_grid, "Max Speed",      0)
sv_min_soc  = stat_row(stats_grid, "Min SOC",        1)
sv_max_temp = stat_row(stats_grid, "Peak Temp",      2)
sv_lap_cnt  = stat_row(stats_grid, "Laps",           3)
sv_best_lap = stat_row(stats_grid, "Best Lap",       4)
sv_distance = stat_row(stats_grid, "Total Distance", 5)

session = {"max_spd": 0, "min_soc": 100, "max_temp": 30}

# ─────────────────────────────────────────────
#  SIMULATION LOOP
# ─────────────────────────────────────────────
DT = 0.5   # seconds per tick

def update():
    t0 = time.time()
    sim.prev_speed = sim.speed
    throttle = throttle_var.get()
    brake    = brake_var.get()
    sim.throttle = throttle
    sim.brake    = brake

    # ── BMS logic (0x110, 0x111) ──
    if sim.soc < 5:
        sim.bms_ok = False
        sim.drive_on = False

    # ── VCU: throttle → torque command (0x120) ──
    if sim.drive_on and sim.bms_ok:
        if throttle < 30:
            sim.mode = "ECO";   torque_mult = 1.2
        elif throttle < 70:
            sim.mode = "NORMAL"; torque_mult = 1.8
        else:
            sim.mode = "SPORT";  torque_mult = 2.5
        sim.torque = round(throttle * torque_mult, 1)
    else:
        sim.torque = 0

    # ── MCU: torque → speed (0x130) ──
    if sim.drive_on and sim.bms_ok and not sim.fault:
        brake_decel = brake * 0.6
        sim.speed  += throttle * 0.035 - brake_decel * 0.1
        sim.speed   = max(0, min(220, sim.speed))
        sim.rpm     = sim.speed * 90
        sim.soc    -= throttle * 0.0008 + 0.0002
        sim.temperature += throttle * 0.003 + 0.005
        sim.regen_active = False
        sim.distance += (sim.speed / 3600) * DT   # km
    else:
        # regen braking when off
        regen_force = brake * 0.04
        sim.speed = max(0, sim.speed * 0.96 - regen_force)
        sim.rpm   = sim.speed * 90
        if sim.speed > 0:
            sim.regen_active = True
            sim.soc += min(0.03, sim.speed * 0.0001)
        else:
            sim.regen_active = False
        sim.temperature = max(30, sim.temperature - 0.05)

    # ── Charging ──
    if sim.charging:
        sim.soc = min(100, sim.soc + 0.08)
        sim.temperature = max(30, sim.temperature + 0.01)

    # ── SOC / Temp clamp ──
    sim.soc = max(0, min(100, sim.soc))

    # ── Accel / G ──
    delta_v = (sim.speed - sim.prev_speed) / 3.6   # m/s
    sim.accel   = delta_v / DT
    sim.g_force = abs(sim.accel) / 9.81 + (brake * 0.008)

    # ── Fault detection ──
    if sim.temperature > 65:
        sim.drive_on  = False
        sim.fault     = True
        sim.fault_msg = "OVERTEMPERATURE FAULT — MCU SHUTDOWN"
    if sim.soc < 3:
        sim.fault     = True
        sim.fault_msg = "CRITICAL LOW SOC — BMS CUT-OFF"

    # ── Session stats ──
    session["max_spd"] = max(session["max_spd"], sim.speed)
    session["min_soc"] = min(session["min_soc"], sim.soc)
    session["max_temp"]= max(session["max_temp"], sim.temperature)

    # ── Time series ──
    sim.tick += 1
    sim.t_arr.append(sim.tick)
    sim.spd_arr.append(sim.speed)
    sim.soc_arr.append(sim.soc)
    sim.tmp_arr.append(sim.temperature)
    sim.regen_arr.append(1 if sim.regen_active else 0)
    for arr in [sim.t_arr, sim.spd_arr, sim.soc_arr, sim.tmp_arr, sim.regen_arr]:
        if len(arr) > sim.N:
            arr.pop(0)

    # ── Logging ──
    if sim.tick % 2 == 0:
        log_data()

    render()
    elapsed = time.time() - t0
    delay   = max(10, int(DT*1000 - elapsed*1000))
    root.after(delay, update)


# ─────────────────────────────────────────────
#  RENDER
# ─────────────────────────────────────────────
def render():
    s   = sim
    spd = int(s.speed)
    soc = s.soc
    tmp = s.temperature

    # ── Speed gauge ──
    sc = speed_color(spd)
    draw_arc_gauge(spd_canvas, 140, 100, 80, spd, 0, 220, sc, BG_CARD, width=16)
    spd_val_lbl.config(text=str(spd), fg=sc)

    # ── RPM gauge ──
    draw_arc_gauge(rpm_canvas, 140, 70, 52, int(s.rpm), 0, 20000,
                   WARN, BG_CARD, width=10, extent=200)
    rpm_val_lbl.config(text=f"{int(s.rpm):,} RPM")

    # ── Torque bar ──
    trq_bar["value"] = min(400, s.torque)
    trq_lbl.config(text=f"{s.torque:.1f} Nm")

    # ── Mode ──
    mc = {"ECO": ACCENT, "NORMAL": GOLD, "SPORT": DANGER}.get(s.mode, ACCENT)
    mode_lbl.config(text=s.mode, fg=mc)

    # ── G / Accel ──
    gf_lbl.config(text=f"{s.g_force:.2f} g")
    acc_lbl.config(text=f"{s.accel:+.2f} m/s²",
                   fg=ACCENT2 if s.accel >= 0 else WARN)

    # ── Distance / Lap ──
    dist_lbl.config(text=f"{s.distance:.3f} km")
    if s.lap_start:
        lap_t = time.time() - s.lap_start
        lap_lbl.config(text=f"Lap {s.lap_count+1}  {lap_t:.1f}s")
    else:
        lap_lbl.config(text="Lap —")

    # ── SOC bar + sparkline ──
    sc2 = soc_color(soc)
    soc_bar["value"] = soc
    style.configure("soc.Horizontal.TProgressbar", background=sc2,
                    lightcolor=sc2, darkcolor=sc2)
    soc_pct_lbl.config(text=f"{soc:.1f}%", fg=sc2)
    w = soc_spark_canvas.winfo_width() or 500
    draw_sparkline(soc_spark_canvas, s.soc_arr, sc2, w, 40, fill=True)

    # ── Temp bar + sparkline ──
    tc = temp_color(tmp)
    temp_bar["value"] = min(100, tmp)
    style.configure("temp.Horizontal.TProgressbar", background=tc,
                    lightcolor=tc, darkcolor=tc)
    temp_val_lbl.config(text=f"{int(tmp)} °C", fg=tc)
    w2 = temp_spark_canvas.winfo_width() or 500
    draw_sparkline(temp_spark_canvas, s.tmp_arr, tc, w2, 40, fill=True)

    # ── Speed sparkline ──
    w3 = spd_spark_canvas.winfo_width() or 500
    draw_sparkline(spd_spark_canvas, s.spd_arr, speed_color(spd), w3, 60, fill=True)

    # ── Throttle / Brake labels ──
    th_pct_lbl.config(text=f"{int(s.throttle)}%")
    br_pct_lbl.config(text=f"{int(s.brake)}%")
    brake_bar["value"] = s.brake

    # ── LEDs ──
    led_drive.config(fg=ACCENT2 if s.drive_on else "gray30")
    led_charge.config(fg=TEAL    if s.charging else "gray30")
    led_regen.config( fg=PURPLE  if s.regen_active else "gray30")
    led_fault.config( fg=DANGER  if s.fault else "gray30")
    led_bms.config(   fg=ACCENT2 if s.bms_ok else DANGER)
    led_vcu.config(   fg=ACCENT2 if s.vcu_ok else DANGER)
    led_mcu.config(   fg=ACCENT2 if s.mcu_ok else DANGER)
    led_ovt.config(   fg=DANGER  if tmp > 60 else "gray30")

    # ── Header node dots ──
    node_dots["BMS"].config(fg=ACCENT2 if s.bms_ok else DANGER)
    node_dots["VCU"].config(fg=ACCENT2 if s.vcu_ok else DANGER)
    node_dots["MCU"].config(fg=ACCENT2 if s.mcu_ok else DANGER)

    # ── Fault banner ──
    if s.fault:
        fault_banner.config(text=f"⚠  {s.fault_msg}", fg=DANGER)
    elif tmp > 50:
        fault_banner.config(text="⚠  HIGH TEMPERATURE WARNING", fg=WARN)
    elif soc < 20:
        fault_banner.config(text="⚠  LOW BATTERY", fg=WARN)
    else:
        fault_banner.config(text="● SYSTEM NOMINAL", fg=ACCENT2)

    # ── CAN Terminal ──
    ts = time.strftime("%H:%M:%S")
    can_box.config(state="normal")
    if can_box.index("end-1c") != "1.0":
        lines = int(float(can_box.index("end-1c").split(".")[0]))
        if lines > 200:
            can_box.delete("1.0", "40.0")

    # BMS_STATUS 0x110
    can_box.insert("end", f"[{ts}] ", "dim")
    can_box.insert("end", "BMS_STATUS ", "h")
    can_box.insert("end", "ID:0x110  ", "id")
    can_box.insert("end",
        f"SOC={soc:.1f}%  V={36+soc*0.04:.2f}V  T={tmp:.1f}°C  "
        f"{'OK' if s.bms_ok else 'FAULT'}\n",
        "ok" if s.bms_ok else "err")

    # BMS_LIMITS 0x111
    can_box.insert("end", f"[{ts}] ", "dim")
    can_box.insert("end", "BMS_LIMITS ", "h")
    can_box.insert("end", "ID:0x111  ", "id")
    can_box.insert("end",
        f"MaxDischg=150A  MaxChg=50A  DriveOK={'Y' if s.bms_ok else 'N'}\n",
        "ok" if s.bms_ok else "err")

    # VCU_COMMAND 0x120
    can_box.insert("end", f"[{ts}] ", "dim")
    can_box.insert("end", "VCU_CMD    ", "h")
    can_box.insert("end", "ID:0x120  ", "id")
    can_box.insert("end",
        f"Throttle={int(s.throttle)}%  TorqueCmd={s.torque:.1f}Nm  Mode={s.mode}\n",
        "ok")

    # MCU_STATUS 0x130
    can_box.insert("end", f"[{ts}] ", "dim")
    can_box.insert("end", "MCU_STATUS ", "h")
    can_box.insert("end", "ID:0x130  ", "id")
    can_box.insert("end",
        f"Spd={spd}km/h  RPM={int(s.rpm)}  Regen={'ON' if s.regen_active else 'OFF'}"
        f"  Brake={int(s.brake)}%\n",
        "ok" if s.mcu_ok else "err")

    can_box.insert("end", "─" * 72 + "\n", "dim")
    can_box.see("end")
    can_box.config(state="disabled")

    # ── CAN Node Details ──
    node_txt.config(state="normal")
    node_txt.delete("1.0", "end")
    v = 36 + soc * 0.04
    node_txt.insert("end", "BMS   (0x110/0x111)\n", "h")
    node_txt.insert("end", f"  SOC        : {soc:.1f}%\n", "val")
    node_txt.insert("end", f"  Pack Volt  : {v:.2f} V\n", "val")
    node_txt.insert("end", f"  Temperature: {tmp:.1f} °C\n", "val")
    node_txt.insert("end", f"  Drive Perm : {'YES' if s.bms_ok else 'NO'}\n", "val")
    node_txt.insert("end", "\nVCU   (0x120)\n", "h")
    node_txt.insert("end", f"  Throttle   : {int(s.throttle)} %\n", "val")
    node_txt.insert("end", f"  Torque Cmd : {s.torque:.1f} Nm\n", "val")
    node_txt.insert("end", f"  Drive Mode : {s.mode}\n", "val")
    node_txt.insert("end", "\nMCU   (0x130)\n", "h")
    node_txt.insert("end", f"  Speed      : {spd} km/h\n", "val")
    node_txt.insert("end", f"  RPM        : {int(s.rpm):,}\n", "val")
    node_txt.insert("end", f"  Regen      : {'ACTIVE' if s.regen_active else 'OFF'}\n", "val")
    node_txt.config(state="disabled")

    # ── Session stats ──
    sv_max_spd.config(text=f"{session['max_spd']:.1f} km/h")
    sv_min_soc.config(text=f"{session['min_soc']:.1f} %")
    sv_max_temp.config(text=f"{session['max_temp']:.1f} °C")
    sv_lap_cnt.config(text=str(s.lap_count))
    sv_best_lap.config(text=f"{s.best_lap:.1f}s" if s.best_lap else "—")
    sv_distance.config(text=f"{s.distance:.3f} km")

    # ── Clock ──
    clock_lbl.config(text=time.strftime("  %H:%M:%S  %d %b %Y"))


# ─────────────────────────────────────────────
#  KEYBOARD SHORTCUTS
# ─────────────────────────────────────────────
def on_key(event):
    k = event.keysym.lower()
    if k == "s": start_vehicle()
    elif k == "x": stop_vehicle()
    elif k == "c": toggle_charge()
    elif k == "r": reset_system()
    elif k == "f": inject_fault()
    elif k == "l": lap_reset()
    elif k == "up":
        throttle_var.set(min(100, throttle_var.get() + 5))
    elif k == "down":
        throttle_var.set(max(0, throttle_var.get() - 5))
    elif k == "right":
        brake_var.set(min(100, brake_var.get() + 5))
    elif k == "left":
        brake_var.set(max(0, brake_var.get() - 5))

root.bind("<KeyPress>", on_key)

# ── Keyboard shortcut hint ──
hint = tk.Label(col_right,
    text="Shortcuts: S=Start  X=Stop  C=Charge  F=Fault  R=Reset  L=Lap\n"
         "↑↓=Throttle  ←→=Brake",
    font=("Courier New", 8), fg="#3A5070", bg=BG_DARK,
    justify="left")
hint.pack(fill="x", padx=6, pady=(4,0))

# ─────────────────────────────────────────────
#  START
# ─────────────────────────────────────────────
root.after(200, update)
root.mainloop()