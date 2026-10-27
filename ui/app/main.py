import json
import os
import time
from datetime import timedelta

from babel.dates import format_timedelta
from flask import Flask, render_template, request
from flask.json import jsonify

app = Flask(__name__)


class PrefixMiddleware:
    def __init__(self, app, prefix=""):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ["PATH_INFO"].startswith(self.prefix):
            new_path = environ["PATH_INFO"][len(self.prefix) :]  # noqa: E203
            environ["PATH_INFO"] = new_path
            environ["SCRIPT_NAME"] = self.prefix
            return self.app(environ, start_response)
        start_response("404", [("Content-Type", "text/plain")])
        return ["This url does not belong to the app.".encode()]


prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "/")
app = Flask(__name__)
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=prefix)

status_file = os.environ.get("STATUS_FILE", "status.json")


def read_status():
    try:
        with open(status_file) as f:
            return json.loads(f.read())
    except Exception as e:
        return {"time": time.time(), "code": "WARNING", "msg": str(e)}


@app.template_filter("timedelta")
def timedelta_filter(s):
    return format_timedelta(s, locale="en_US")


@app.route("/")
def get_status():
    status = read_status()
    if any(m == "application/json" for m in request.accept_mimetypes.values()):
        return jsonify(status)
    # add a timedelta to status
    status["delta"] = timedelta(seconds=time.time() - status["time"])
    return render_template("status.html", status=status)


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host="0.0.0.0", debug=True)
