# PiCamGuard
Raspberry Pi security camera with:
* Live MJPEG stream
* Motion detection (bucketed series for charts)
* Snapshots (auto + manual) with gallery (view/download/delete)
* Optional Telegram alerts with image
* Optional Tailscale HTTPS exposure

## Setup
### Install system packages
```sudo apt update
sudo apt install -y \
  libcamera-apps python3-libcamera python3-picamera2 \
  python3-opencv python3-numpy python3-simplejpeg \
  python3-venv python3-pip
  ```

### Create the venv (with system packages)
You need the venv to “see” the OS packages above:
```cd ~/Coding/PiCamGuard
python3 -m venv --system-site-packages venv
source venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt
```
### Confige secretes
Create a .env file in the project root:
```TELEGRAM_BOT_TOKEN=1234567890:AA....   # full token (id:hash), optional
TELEGRAM_CHAT_ID=123456789             # numeric id or -100... for groups, optional
SAVE_TO_TELEGRAM=false                 # set true to enable alerts
MAX_NUM_SNAPSHOTS=200
NOTIFY_INTERVAL=60
MOTION_THRESHOLD=500000
FRAME_INTERVAL=0.05
```
### Run it
``` python run.py```

### Optional (Tailscale)

```curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
sudo tailscale serve https / http://127.0.0.1:5000
tailscale serve status
```
Open on any device in your tailnet
```
https://<your-pi-hostname>.<tailnet>.ts.net/
```
