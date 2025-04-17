import os
import json
import requests
from urllib.parse import urljoin

def post(host, path, contentType, body={}):
    if "https://" in host or "http://" in host:
        fullurl = urljoin(host, path)
    else:
        fullurl = urljoin("https://{}".format(host), path)
    s = requests.Session()
    s.headers["Content-Type"] = contentType
    result = s.post(fullurl, json=body)
    if result.status_code > 199 and result.status_code < 300:
        return result
    else:
        print("Error when retrieving info from {}".format(host))
        print("Status: " + str(result.status_code))
        print("Attempted to get " + str(path))
        return False


def log(message, conf):
    payload = {}
    payload["message"] = message
    if "logger_host" in conf.keys():
        post(host=conf["logger_host"], path=conf["logger_application_name"], contentType="application/json", body=payload)
    else:
        # Logging to stdout when no little logger backend is defined
        print("Log: {}".format(json.dumps(message)))