import json
import logging
import os
import sys
import time
from urllib.parse import urljoin

import requests
import schedule
from requests.exceptions import RequestException


def spawn_notebook(api_url, token, user, timeout=600, delete=True):
    start = time.time()
    user_url = urljoin(api_url, "users/%s" % user)
    server_url = urljoin(api_url, "users/%s/server" % user)
    # is the user there already?
    headers = {"Authorization": "token %s" % token}
    r = requests.get(user_url, headers=headers)
    if r.status_code != 200:
        # create the user
        r = requests.post(user_url, headers=headers)
        if r.status_code != 201:
            return "CRITICAL", "Unable to create user: %s" % r.text
    else:
        # first clean up any previously existing server
        if r.json()["servers"].get("", {}):
            r = requests.delete(server_url, headers=headers)
            # wait a bit for it to stop
            time.sleep(60)
    # start a new server
    r = requests.post(server_url, headers=headers)
    if r.status_code not in [202, 201]:
        return "CRITICAL", "Unable to spawn new server: %s" % r.text
    #  wait for server to be fully started
    server_ready = False
    for i in range(int(timeout / 5)):
        r = requests.get(user_url, headers=headers)
        if r.status_code != 200:
            return "CRITICAL", "Unable to query user: %s" % r.text
        if r.json()["servers"].get("", {}):
            server_ready = r.json()["servers"][""].get("ready", False)
            if server_ready:
                break
        time.sleep(5)
    #  delete the server, don't care much about the result?
    if delete:
        requests.delete(server_url, headers=headers)
    elapsed = time.time() - start
    if server_ready:
        return "OK", "Spawned server in %.2f seconds" % elapsed
    return "CRITICAL", "Server did not start in %.2f seconds" % elapsed


def check_notebook(api_url, token, user, status_file, timeout, delete=True):
    logging.info("Checking notebooks spawning!")
    status = {
        "time": time.time(),
    }
    try:
        code, msg = spawn_notebook(api_url, token, user, timeout, delete)
        status["code"] = code
        status["msg"] = msg
    except RequestException as e:
        status["code"] = "CRITICAL"
        status["msg"] = "Error in checking notebooks: %s" % e
    logging.debug("Updating status: %s" % status)
    with open(status_file, "w") as f:
        f.write(json.dumps(status))


if __name__ == "__main__":
    if os.environ.get("DEBUG", "").upper() == "TRUE":
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level)
    api_url = os.environ.get("JUPYTERHUB_API_URL", "http://localhost/")
    if not api_url.endswith("/"):
        api_url = api_url + "/"
    token = os.environ.get("JUPYTERHUB_API_TOKEN", "")
    user = os.environ.get("JUPYTERHUB_USER", "monitor")
    status_file = os.environ.get("STATUS_FILE", "status.json")

    # timeout in seconds
    timeout = int(os.environ.get("SPAWN_TIMEOUT", 600))

    # first execution
    check_notebook(api_url, token, user, status_file, timeout, delete=True)

    if os.environ.get("SINGLE_EXECUTION", "").upper() == "TRUE":
        sys.exit()

    schedule.every(1).hour.do(
        check_notebook, api_url, token, user, status_file, timeout
    )
    while True:
        schedule.run_pending()
        time.sleep(10)
