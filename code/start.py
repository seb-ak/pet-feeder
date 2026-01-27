import secrets
from server import PetFeederServer 
import subprocess
import os

CONFIG = {
    "CAPTURE_DEVICE": 0,
    "FRAME_WIDTH": 1280,
    "FRAME_HEIGHT": 720,
    "FRAME_DELAY": 1/30,
    "EXPECTED_PASSWORD": os.getenv("feeder_password", "password"),

    "SECRET_KEY": secrets.token_urlsafe(32),
    "LOGIN_HTML": open("code/html/login.html").read(),
    "DASHBOARD_HTML": open("code/html/dashboard.html").read(),
}

subprocess.Popen(["cloudflared", "tunnel", "run", "rabbits"])

server = PetFeederServer(CONFIG)
server.run()