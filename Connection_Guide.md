# Reachy 2 Setup and Run Guide

This guide explains how to turn on Reachy, connect Reachy and the laptop to the same network, open the project in Visual Studio Code, activate the Python virtual environment on Windows, and run the Reachy ball grasp program.

---

## 1. Turn on Reachy

1. Power on Reachy.
2. Wait until Reachy fully boots.
3. Make sure the emergency stop is nearby and released.
4. Make sure the laptop and Reachy are connected to the same network.

For the first setup, it is recommended to connect the laptop and Reachy using Ethernet first, then configure Wi-Fi from the Reachy dashboard.

---

## 2. Connect Reachy and laptop through the same network

Reachy and the laptop must be on the same local network so the Python SDK can connect to the robot.

You can connect them in one of these ways:

```txt
Option 1:
Reachy and laptop are connected to the same Wi-Fi.

Option 2:
Reachy and laptop are connected through the same Ethernet network.

Option 3:
Use Ethernet first to access the Reachy dashboard, then set Reachy's Wi-Fi from the dashboard.
```

If Reachy has already been set up and is already connected to the same Wi-Fi as the laptop, you can skip the network setup steps.

---

## 3. Open the Reachy dashboard

Open a browser on the laptop and go to the Reachy dashboard.

Try:

```txt
http://10.116.19.109:8000
```

or:

```txt
http://reachy2-pvt01.local:8000
```

If the dashboard opens, the laptop can see Reachy on the network.

If the dashboard does not open, check:

```txt
- Reachy is powered on.
- Reachy and laptop are on the same Wi-Fi or local network.
- Ethernet cable is connected if using Ethernet.
- Reachy's IP address has not changed.
- VPN is disabled if it blocks local network traffic.
```

Important:

```txt
Do not use Docker internal IP addresses like 172.17.x.x.
Use the real Reachy network IP address.
```

---

## 4. Set Reachy Wi-Fi from the dashboard

On the Reachy dashboard:

```txt
1. Go to Network.
2. Choose the Wi-Fi network.
3. Connect Reachy to the same Wi-Fi used by the laptop.
4. Wait until Reachy confirms the connection.
5. Check that the dashboard still works after Wi-Fi connection.
```

Reachy and the laptop must stay on the same network. If the Wi-Fi changes, Reachy's IP address may also change, so you may need to update the `ROBOT_HOST` value in the Python code.

---

## 5. Open the project in Visual Studio Code

On the laptop, open Visual Studio Code.

Open the project folder:

```txt
reachy2-robot-controller
```

Example Windows path:

```txt
C:\Users\<your-name>\reachy2-robot-controller
```

---

## 6. Open the terminal in Visual Studio Code

In Visual Studio Code:

```txt
Terminal → New Terminal
```

Make sure the terminal is opened inside the project root folder.

You should be inside:

```txt
reachy2-robot-controller
```

If not, move into the project folder:

```powershell
cd C:\Users\<your-name>\reachy2-robot-controller
```

---

## 7. Create and activate the Python virtual environment on Windows

PowerShell usually blocks virtual environment activation. Therefore, before activating `.venv`, always run this command first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This command is required for this setup. It only applies to the current PowerShell session and does not permanently change the computer policy.

If the `.venv` folder does not exist yet, create it with Python 3.10:

```powershell
py -3.10 -m venv .venv
```

Then activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, the terminal should show something like:

```powershell
(.venv) PS C:\Users\<your-name>\reachy2-robot-controller>
```

Install the required Python packages:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

The normal Windows setup flow should be:

```powershell
cd C:\Users\<your-name>\reachy2-robot-controller
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

---

## 8. Check Reachy connection

Before running the main demo, test whether the laptop can connect to Reachy.

Run:

```powershell
python check_reachy_access.py
```

If you do not have that file, create a simple connection test:

```python
from reachy2_sdk import ReachySDK

ROBOT_HOST = "10.116.19.109"

reachy = ReachySDK(host=ROBOT_HOST)

print("Connected:", reachy.is_connected())

if reachy.is_connected():
    print("Head:", reachy.head)
    print("Right arm:", reachy.r_arm)
    print("Left arm:", reachy.l_arm)
    print("Cameras:", reachy.cameras)
```

Expected result:

```txt
Connected: True
```

If it says `Connected: False`, check:

```txt
- Reachy IP address is correct.
- Laptop and Reachy are on the same Wi-Fi or local network.
- Reachy dashboard is accessible.
- Reachy core is running.
- VPN is disabled if it blocks local network traffic.