from flask import Flask, Response, request, abort, jsonify, send_file, render_template_string, stream_with_context, session, redirect, url_for
from flask_cors import CORS
import atexit
import cv2
import threading
import time
import datetime
import logging
import subprocess
import secrets

class Camera:
    def __init__(self, config):
        self.config = config
        self.device = config["CAPTURE_DEVICE"]
        self.width = config["FRAME_WIDTH"]
        self.height = config["FRAME_HEIGHT"]
        self.cap = None
        self.clients = 0
        self.clients_lock = threading.Lock()

    def open(self):
        if self.cap is None or not self.cap.isOpened():
            logging.info("Opening camera")
            self.cap = cv2.VideoCapture(self.device)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def close(self):
        if self.cap is not None and self.cap.isOpened():
            logging.info("Closing camera")
            self.cap.release()
        self.cap = None

    def generate_mjpeg(self):
        with self.clients_lock:
            self.clients += 1
            if self.clients == 1:
                self.open()
        try:
            last = time.time()
            while True:
                if self.cap is None or not self.cap.isOpened():
                    break
                now = time.time()
                if now - last < self.config["FRAME_DELAY"]:
                    time.sleep(self.config["FRAME_DELAY"] - (now - last))
                success, frame = self.cap.read()
                if not success:
                    continue
                ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                cv2.putText(frame, ts, (10, 20),
                            cv2.FONT_HERSHEY_PLAIN, 1,
                            (255, 255, 255), 1, cv2.LINE_AA)
                ok, buf = cv2.imencode(".jpg", frame)
                if not ok:
                    continue
                yield (b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" +
                    buf.tobytes() +
                    b"\r\n")
                last = time.time()
        finally:
            with self.clients_lock:
                self.clients -= 1
                if self.clients == 0:
                    self.close()

class PetFeederServer:
    def __init__(self, config):
        self.camera = Camera(config)
        self.config = config
        self.tempCodes = []

        self.app = Flask(__name__)
        self.app.secret_key = config["SECRET_KEY"]
        CORS(self.app, resources={r"/*": {"origins": "*"}})

        self._register_routes()

        atexit.register(self.shutdown)

    def _register_routes(self):
        app = self.app
        config = self.config

        @app.after_request
        def allow_all(response):
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

        def is_logged_in():
            return session.get("logged_in", False)
        
        def is_temp():
            return session.get("temp", False)

        @app.route("/login", methods=["GET", "POST"])
        def login():
            if request.method == "POST":
                pw = request.form.get("pw")
                if pw == config["EXPECTED_PASSWORD"]:
                    session["logged_in"] = True
                    return redirect(url_for("dashboard"))
                else:
                    return render_template_string(
                        config["LOGIN_HTML"]
                        .replace("<p>Enter the password to access.</p>", "<p>Incorrect password. Please try again.</p>")
                    )
            return render_template_string(config["LOGIN_HTML"])

        @app.route("/logout")
        def logout():
            session.clear()
            return redirect(url_for("login"))

        @app.route("/")
        def dashboard():
            c = request.args.get("c")
            if c in self.tempCodes:
                session["temp"] = True
                index = self.tempCodes.index(c)
                self.tempCodes.pop(index)

            if not is_logged_in():
                if is_temp():
                    return render_template_string(config["DASHBOARD_HTML"].replace("#bottom {","#bottom { visibility: hidden;"))
                
                return redirect(url_for("login"))
            
            return render_template_string(config["DASHBOARD_HTML"])

        @app.route("/video_feed")
        def video_feed():
            if not is_logged_in() and not is_temp():
                abort(403)
            return Response(
                stream_with_context(self.camera.generate_mjpeg()),
                mimetype="multipart/x-mixed-replace; boundary=frame"
            )
        
        @app.route("/cmd")
        def cmd():
            if not is_logged_in():
                return redirect(url_for("login"))
            if is_temp():
                return redirect(url_for("dashboard"))

            c = request.args.get("c")

            if c == "feed":
                feed(config["FEED_TIME_SECONDS"])
                return redirect(url_for("dashboard"))
            
            elif c == "reboot":
                reboot()
                return redirect(url_for("dashboard"))
            
            elif c == "logout":
                return redirect(url_for("logout"))
            
            elif c == "link":
                code = secrets.token_urlsafe(5),
                self.tempCodes.append(code)
                link = "https://rabbits.sebak.me.uk/?c=" + code
                return redirect(
                    url_for("dashboard").replace("show1","hide1").replace("hide2","show2").replace("*link*",link)
                )
            
            else:
                abort(400, description="Unknown command")

    def shutdown(self):
        self.camera.close()

    def run(self, host="0.0.0.0", port=8080):
        self.app.run(host=host, port=port, threaded=True)

import RPi.GPIO as GPIO
def feed(time_seconds):
    def feed_thread(time_seconds):
        IN1 = 23

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(IN1, GPIO.OUT)
        time.sleep(0.5)

        try:
            GPIO.output(IN1, GPIO.HIGH)
            time.sleep(time_seconds)
            GPIO.output(IN1, GPIO.LOW)

        finally:
            time.sleep(0.5)
            GPIO.cleanup()

    threading.Thread(target=feed_thread, args=(time_seconds,)).start()

def reboot(): subprocess.run(["sudo", "reboot"])