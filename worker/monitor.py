import json
import logging
import os
import sys
import time
from functools import partial
from urllib.parse import urljoin

import schedule
from httpx import Client, RequestError


def spawn_notebook(api_url, token, user, timeout=600, delete=True):
    start = time.time()
    client = Client(headers={"Authorization": f"token {token}"})

    user_url = urljoin(api_url, f"users/{user}")
    server_url = urljoin(api_url, f"users/{user}/server")
    # is the user there already?
    r = client.get(user_url)
    if r.status_code != 200:
        # create the user
        r = client.post(user_url)
        if r.status_code != 201:
            return "CRITICAL", f"Unable to create user: {r.text}"
    else:
        # first clean up any previously existing server
        if r.json()["servers"].get("", {}):
            r = client.delete(server_url)
            # wait a bit for it to stop
            time.sleep(60)
    # start a new server
    r = client.post(server_url)
    if r.status_code not in [202, 201]:
        return "CRITICAL", f"Unable to spawn new server: {r.text}"
    #  wait for server to be fully started
    server_ready = False
    for _ in range(int(timeout / 5)):
        r = client.get(user_url)
        if r.status_code != 200:
            return "CRITICAL", f"Unable to query user: {r.text}"
        if r.json()["servers"].get("", {}):
            server_ready = r.json()["servers"][""].get("ready", False)
            if server_ready:
                break
        time.sleep(5)
    #  delete the server, don't care much about the result?
    if delete:
        client.delete(server_url)
    elapsed = time.time() - start
    if server_ready:
        return "OK", f"Spawned server in {elapsed:.2f} seconds"
    return "CRITICAL", f"Server did not start in {elapsed:.2f} seconds"


def check_notebook(api_url, token, user, status_file, timeout, delete=True):
    logging.info("Checking notebooks spawning!")
    status = {}
    try:
        code, msg = spawn_notebook(api_url, token, user, timeout, delete)
        status["code"] = code
        status["msg"] = msg
    except RequestError as e:
        status["code"] = "CRITICAL"
        status["msg"] = f"Error in checking notebooks: {e}"
    return status


def check_binder(binder_url):
    logging.info("Checking binder health!")
    status = {}
    client = Client()
    try:
        r = client.get(urljoin(binder_url, "health"))
        ok = r.json().get("ok", "")
        if ok:
            status["code"] = "OK"
            status["msg"] = "All components ok"
        else:
            status["code"] = "CRITICAL"
            not_ok = [svc["service"] for svc in r.json()["checks"] if not svc["ok"]]
            status["msg"] = f"{' '.join(not_ok)} not ok"
    except RequestError as e:
        status["code"] = "CRITICAL"
        status["msg"] = f"Error in checking notebooks: {e}"
    return status


def check_and_write_status(f, status_file):
    status = f()
    status.update(
        {
            "time": time.time(),
        }
    )
    logging.debug("Updating status: %s" % status)
    with open(status_file, "w") as f:
        f.write(json.dumps(status))
    return status["code"] == "OK"


def fake_check(service_type):
    return {
        "code": "CRITICAL",
        "msg": f"Unknown service {service_type}",
    }


if __name__ == "__main__":
    if os.environ.get("DEBUG", "").upper() == "TRUE":
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level)

    status_file = os.environ.get("STATUS_FILE", "status.json")
    service_type = os.environ.get("SERVICE_TYPE", "jupyterhub").lower()
    url = os.environ.get("MONITORED_URL", "http://localhost/")
    if not url.endswith("/"):
        url = url + "/"
    token = os.environ.get("JUPYTERHUB_API_TOKEN", "")
    user = os.environ.get("JUPYTERHUB_USER", "monitor")
    timeout = int(os.environ.get("SPAWN_TIMEOUT", 600))

    if service_type == "jupyterhub":
        check_fn = partial(check_notebook, url, token, user, timeout, True)
    elif service_type == "binderhub":
        check_fn = partial(check_binder, url)
    else:
        check_fn = partial(fake_check, service_type)

    result = check_and_write_status(check_fn, status_file)
    if os.environ.get("SINGLERUN", "").upper() == "TRUE":
        sys.exit(result)
    schedule.every(1).hour.do(check_and_write_status, check_fn, status_file)
    while True:
        schedule.run_pending()
        time.sleep(10)
