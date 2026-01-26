import secrets
from server import PetFeederServer 

CONFIG = {
    "CAPTURE_DEVICE": 0,
    "FRAME_WIDTH": 1280,
    "FRAME_HEIGHT": 720,
    "FRAME_DELAY": 1/30,  # 30 FPS
    "EXPECTED_PASSWORD": "password",
    "SECRET_KEY": secrets.token_urlsafe(32),
    "LOGIN_HTML": """
        <form method="post" action="/login">
            <input type="password" name="pw" placeholder="Password"/>
            <button type="submit">Login</button>
        </form>
    """,
    "DASHBOARD_HTML": """
        <html><body><h1>Welcome to the Pet Feeder Dashboard!</h1></body></html>
    """,
}

server = PetFeederServer(CONFIG)
server.run()
