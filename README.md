# EV CAN Simulator

## Overview

This project is a simulated Electric Vehicle (EV) Controller Area Network (CAN) communication system developed as part of an Embedded Systems internship assignment.

The simulator demonstrates interaction between:

- Vehicle Control Unit (VCU)
- Battery Management System (BMS)
- Motor Control Unit (MCU)

using simulated CAN telemetry messages.

---

# Features

## Real-Time EV Simulation

- Vehicle speed simulation
- Torque calculation
- Battery SOC monitoring
- Temperature monitoring

---

## CAN Communication Simulation

Simulated CAN telemetry includes:

- CAN ID
- Throttle %
- Torque
- Vehicle speed
- Battery SOC
- Temperature

---

## Drive Modes

The simulator dynamically changes between:

- ECO Mode
- NORMAL Mode
- SPORT Mode

based on throttle input.

---

## Fault Handling

The system supports fault injection:

- Overtemperature fault
- Drive disable protection

The simulator disables drive operation automatically when unsafe conditions occur.

---

## Reset System

The reset function restores:

- Speed
- Temperature
- SOC
- Torque
- Drive state

---

## Telemetry Logging

All vehicle telemetry data is logged into:

```text
logs/telemetry.csv
```

This simulates real automotive telemetry storage systems.

---

# Technologies Used

- Python
- Tkinter
- CSV Logging
- GitHub

---

# System Architecture

```text
Throttle Input
       ↓
Vehicle Control Logic
       ↓
Simulated CAN Messaging
       ↓
BMS / MCU Monitoring
       ↓
Telemetry Dashboard
       ↓
CSV Data Logging
```

---

# Screenshot

![Dashboard](dashboard.png)

---

# How to Run

## Install dependencies

```bash
pip install matplotlib pandas
```

## Run simulator

```bash
python main.py
```

---

# Project Structure

```text
Arys_EV_Simulator
│
├── logs
│   └── telemetry.csv
│
├── modules
│   ├── bms.py
│   ├── vcu.py
│   ├── mcu.py
│   ├── dashboard.py
│   └── logger.py
│
├── main.py
├── README.md
└── requirements.txt
```

---

# AI Usage Declaration

AI tools used during development:

- ChatGPT

How AI helped:

- System architecture planning
- CAN simulation logic
- GUI development assistance
- Debugging support
- Documentation guidance

All implementation, testing, and integration were performed manually.

---

# Future Improvements

- Real CAN hardware integration
- STM32 communication
- Live plotting graphs
- Battery charging simulation
- Motor efficiency calculations
- Advanced fault diagnostics

---

# Author

Vamshi N