feedTimeSeconds = 2
frameRate = 20
videoWidth = 1280 * 0.5
videoHeight = 720 * 0.5
title = "Rabbit Feeder"

import secrets
from server import PetFeederServer 
import subprocess
import os

CONFIG = {
    "FEED_TIME_SECONDS": feedTimeSeconds,
    "TITLE": title,
    "EXPECTED_PASSWORD": os.getenv("feeder_password", "password"),
    "FRAME_WIDTH": videoWidth,
    "FRAME_HEIGHT": videoHeight,
    "FRAME_DELAY": 1/frameRate,
    "CAPTURE_DEVICE": 0,
    "SECRET_KEY": secrets.token_urlsafe(32),
    "LOGIN_HTML": open("code/html/login.html").read().replace("*title*", title),
    "DASHBOARD_HTML": open("code/html/dashboard.html").read().replace("*title*", title),
}

server = PetFeederServer(CONFIG)
server.run()
