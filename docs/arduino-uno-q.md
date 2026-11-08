# Wire-Pod on Arduino UNO Q (ABX00173)

This guide documents how to run **Wire-Pod** as an official **Arduino App** inside the **Arduino App Lab (`arduino-app-cli`)** ecosystem on the **Arduino UNO Q 4GB**.

---

## 1. Architecture Overview

```
                      +------------------------------------------+
                      |         Arduino UNO Q (ABX00173)         |
                      |                                          |
                      |   [Linux MPU: Debian 13 aarch64]         |
                      |   +------------------------------------+ |
                      |   | Arduino App Lab (arduino-app-cli)  | |
                      |   | +--------------------------------+ | |
[Anki Vector 2.0] <=======> | app.yaml (ID: user:wire-pod)   | | |
  (mDNS: escapepod.local) | | python/main.py (Supervisor)    | | |
  (gRPC: Port 443/8084)  | | chipper (Golang binary)        | | |
  (WebUI: Port 8080)     | | libvosk.so (Offline STT)       | | |
                      |   | +--------------------------------+ | |
                      |   +------------------------------------+ |
                      +------------------------------------------+
```

* **Zero Core Modifications:** Wire-Pod's Go source code (`chipper/**`) remains 100% vanilla and unmodified.
* **Stand-Alone 24/7:** Runs continuously on the board without requiring a PC or paid cloud VPS.
* **App Lab Integrated:** Managed via `arduino-app-cli` and accessible through the Arduino Web App Lab interface on port 7000 (which redirects to port 8080).

---

## 2. Network Ports

| Port | Protocol | Purpose |
| :--- | :--- | :--- |
| **80** | HTTP | Vector internet connectivity check (`connCheck`). |
| **443** | TLS / gRPC | Escape Pod TLS voice streaming and session handler. |
| **7000** | HTTP | Arduino App Lab Web UI redirect router. |
| **8080** | HTTP | Wire-Pod Web configuration and bot setup dashboard. |
| **8084** | TLS / gRPC | Vector 2.0.1 jdocs compatibility port. |
| **5353** | UDP (mDNS) | Resolves `escapepod.local` across the local Wi-Fi network via Avahi. |

---

## 3. Installation & Setup

### Step 1: Install Build Dependencies on Arduino UNO Q (Debian 13)
```bash
sudo apt update
sudo apt install -y -t trixie-backports libasound2-dev
sudo apt install -y wget curl git gcc make libsox-dev libopus-dev libsodium-dev cmake lld avahi-daemon
```

### Step 2: Compile Chipper Binary & Install Vosk Library
```bash
# Clone the repository into ArduinoApps
git clone https://github.com/ovurrsl/wire-pod /home/arduino/ArduinoApps/wire-pod
cd /home/arduino/ArduinoApps/wire-pod

# Download Vosk aarch64 shared library
mkdir -p lib /home/arduino/.vosk/libvosk
wget https://github.com/alphacep/vosk-api/releases/download/v0.3.45/vosk-linux-aarch64-0.3.45.zip
unzip vosk-linux-aarch64-0.3.45.zip
cp vosk-linux-aarch64-0.3.45/libvosk.so lib/
cp vosk-linux-aarch64-0.3.45/libvosk.so /home/arduino/.vosk/libvosk/
sudo cp vosk-linux-aarch64-0.3.45/libvosk.so /usr/local/lib/
sudo ldconfig

# Build chipper binary
cd chipper
go build -tags nolibopusfile -o chipper cmd/vosk/main.go
sudo setcap 'cap_net_bind_service=+ep' chipper
```

### Step 3: Run via Arduino App CLI
```bash
# Start Wire-Pod application
arduino-app-cli app start /home/arduino/ArduinoApps/wire-pod

# Verify running status
arduino-app-cli app ps

# View live application logs
arduino-app-cli app logs /home/arduino/ArduinoApps/wire-pod --tail 50
```

### Step 4: Configure Autostart on Boot
To ensure Wire-Pod boots automatically whenever the board is powered on:
```bash
arduino-app-cli properties set default /home/arduino/ArduinoApps/wire-pod
```

---

## 4. Bot Pairing

1. Open **`http://escapepod.local:8080/`** (or `http://<board-ip>:8080/`) in Chrome or Edge.
2. Place Vector on his charger and double-click his back button to enter pairing mode.
3. In the Wire-Pod web dashboard, go to **Bot Setup**, pair via Web Bluetooth, and click **Activate Escape Pod**.
