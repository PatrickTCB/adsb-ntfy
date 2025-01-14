import json
import time
import geopy.distance
import requests
import yaml
from pathlib import Path
from datetime import datetime
from bincraft import binCraftReader
from urllib.parse import urljoin


class NtfyAction:
    kind = "http"
    label = ""
    url = ""
    parameters = ""

def stringToFile(fileName, contentsRaw):
    contents = str(contentsRaw)
    with open(fileName, "w+") as output_file:
        output_file.write(contents)
        output_file.close()

def ntfy(host, topic, message, title="", prio="3", click="", attach="", at="", actions=[], verbose=False):
    url = "/{}".format(host, topic)
    headers = {}
    headers["Priority"] = "{}".format(prio)
    if title != "":
        headers["Title"] = "{}".format(title)
    if click != "":
        headers["Click"] = "{}".format(click)
    if attach != "":
        # Must be a URL to something the server will then magically attach
        headers["Attach"] = "{}".format(attach)
    if at != "":
        # Delay amount or some timestamp
        headers["Delay"] = "{}".format(at)
    if len(actions) > 0:
        actionHeaderValue = ""
        for action in actions:
            actionHeaderValue = "{}{},{},{},{}\\\n".format(actionHeaderValue, action.kind, action.label, action.url, action.parameters)
        headers["Action"] = actionHeaderValue
    a = requests.post(url,headers=headers, data=message.encode(encoding='utf-8'))
    if a == 200:
        return True
    else:
        if verbose:
            print("Status: {}\n{}".format(a.status_code, a.text))
            print("Headers: {}".format(headers))
        return False

def nearbyAircraft(url):
    text = binCraftReader(url)
    #stringToFile("aircraft.json", json.dumps(text, indent=4))
    return text

def flightDetails(planes):
    d = []
    host = "https://api.adsb.lol"
    aircraftList = []
    callsignToHex = {}
    for plane in planes:
        print("Looking up details for aircraft registration: {}                ".format(plane), end="\r")
        f = {}
        path = "/v2/registration/{}".format(plane)
        fullurl = urljoin("https://{}".format(host), path)
        s = requests.Session()
        raw = s.get(fullurl)
        if raw.status_code == 200:
            r = json.loads(raw.text)
            for ac in r["ac"]:
                if type(0) == type(ac["alt_baro"]):
                    if ac["alt_baro"] > 0:
                        aircraft = {}
                        aircraft["lng"] = ac["lon"]
                        aircraft["lat"] = ac["lat"]
                        aircraft["callsign"] = ac["flight"].strip()
                        callsignToHex[ac["flight"].strip()] = ac["hex"]
                        aircraftList.append(aircraft)
                    else:
                        print("\nalt_baro was {}".format(ac["alt_baro"]))
                else:
                    print("\nalt_baro was {}".format(ac["alt_baro"]))
        else:
            print("Error when retrieving info from {}".format(host))
            print("Status: " + str(raw.status_code))
            print("Attempted to get {}".format(fullurl))
            print("{}".format(raw.text))
            responseName = "error-{}{}.txt".format(raw.status_code, str(fullurl.replace("https://", "")).replace("http://", "").replace("/", "."))
            stringToFile(responseName, raw.text)
            print("Error response saved to {}".format(responseName))
        time.sleep(1)
    body = {}
    body["planes"] = aircraftList
    print("\nGetting routes for {} aircraft.                ".format(len(aircraftList)))
    path = "/api/0/routeset"
    fullurl = urljoin(host, path)
    ps = requests.Session()
    ps.headers["Content-Type"] = "application/json"
    rawDetails = ps.post(fullurl, json=body)
    resp = json.loads(rawDetails.text)
    routes = []
    for route in resp:
        route["hex"] = callsignToHex[route["callsign"]]
        routes.append(route)
    return routes

if __name__ == "__main__":
    conf = yaml.safe_load(Path('conf.yml').read_text())
    now = datetime.now()
    todayDate = now.strftime("%Y-%m-%d %H:%M:%S")
    print("Starting: {}".format(todayDate))
    tar1090URL = "{}/data/aircraft.binCraft.zst".format(conf['tar1090_host'])
    aircraft = nearbyAircraft(tar1090URL)
    #stringToFile("nearby-aircraft.json", json.dumps(aircraft, indent=4))
    planes = []
    acInfo = {}
    for a in aircraft["aircraft"]:
        if "r" in a.keys():
            if a["r"] != "":
                if a["lat"] != 0.0:
                    planes.append(a["r"])
                    acd = {}
                    acd["hex"] = a["hex"]
                    acd["url"] = "{}/?icao={}".format(conf['TAR1090_HOST'], a["hex"])
                    coords_home = (float(conf("home_lat")), float(conf["home_lon"]))
                    coords_plane = (a["lon"], a["lat"])
                    dist = geopy.distance.geodesic(coords_home, coords_plane).km
                    acd["dist"] = round(dist, 2)
                    acd["type"] = a["t"]
                    #print("{} and {} are {}km apart".format(coords_home, coords_plane, round(dist, 2)))
                    acInfo[a["hex"]] = acd
    routes = flightDetails(planes)
    #common.stringToFile("routes.json", json.dumps(routes, indent=4))
    for route in routes:
        acd = acInfo[route["hex"]]
        print("{}: {} ({}km away)".format(route["callsign"], route["_airport_codes_iata"], acd["dist"]))
        if acd["dist"] < float(conf["ntfy_distance"]):
            topic = conf["ntfy_topic"]
            title = "{} Flying By Closely!".format(acd["type"])

            message = "An {} with callsign {} flying {} is only {} km from {}".format(acd["type"], route["callsign"], route["_airport_codes_iata"], acd["dist"], conf["home_name"])
            url = acd["url"]
            ntfy(host=conf["ntfy_host"], topic=topic, message=message, title=title, prio="2", click=url)
    now = datetime.now()
    todayDate = now.strftime("%Y-%m-%d %H:%M:%S")
    print("Ending: {}".format(todayDate))
