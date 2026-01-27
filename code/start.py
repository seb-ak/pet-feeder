import secrets
from server import PetFeederServer 
import subprocess

CONFIG = {
    "CAPTURE_DEVICE": 0,
    "FRAME_WIDTH": 1280,
    "FRAME_HEIGHT": 720,
    "FRAME_DELAY": 1/30,
    "EXPECTED_PASSWORD": "password",

    "SECRET_KEY": secrets.token_urlsafe(32),
    "LOGIN_HTML": open("code/html/login.html").read(),
    "DASHBOARD_HTML": open("code/html/dashboard.html").read(),
}

server = PetFeederServer(CONFIG)
server.run()

subprocess.Popen(["cloudflared", "tunnel", "run", "rabbits"])