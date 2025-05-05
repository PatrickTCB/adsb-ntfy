import json
import time
import geopy.distance
import yaml
import sys
from lib import logger, web
from datetime import datetime
from zoneinfo import ZoneInfo
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
    a = web.post(host=host, contentType="text/plain", path=topic, body=message.encode(encoding='utf-8'))
    if a.status_code == 200:
        return True
    else:
        if verbose:
            print("Status: {}\n{}".format(a.status_code, a.text))
            print("Headers: {}".format(headers))
        return False

def nearbyAircraft(host):
    text = binCraftReader(host)
    #stringToFile("aircraft.json", json.dumps(text, indent=4))
    return text

def flightDetails(planes, conf):
    host = "https://api.adsb.lol"
    aircraftList = []
    callsignToHex = {}
    for plane in planes:
        print("Looking up details for aircraft registration: {}                ".format(plane), end="\r")
        path = "/v2/registration/{}".format(plane)
        raw = web.get(host=host, path=path)
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
        time.sleep(1)
    body = {}
    body["planes"] = aircraftList
    print("\nGetting routes for {} aircraft.                ".format(len(aircraftList)))
    path = "/api/0/routeset"
    rawDetails = web.post(host=host, path=path, contentType="application/json", body=body, jsonBody=True, ignoreErrors=True, conf=conf)
    resp = json.loads(rawDetails.text)
    routes = []
    for route in resp:
        route["hex"] = callsignToHex[route["callsign"]]
        routes.append(route)
    return routes

if __name__ == "__main__":
    while True:
        conf = yaml.safe_load(Path('conf.yml').read_text())
        notifyDistance = conf["ntfy_distance"]
        sleepInterval = int(conf["sleep_interval"])
        now = datetime.now(ZoneInfo(conf["tz"]))
        todayDate = now.strftime("%Y-%m-%d %H:%M:%S")
        tar1090Host = conf["tar1090_host"]
        print("Starting: {}".format(todayDate))
        aircraft = nearbyAircraft(conf)
        stringToFile("nearby-aircraft.json", json.dumps(aircraft, indent=4))
        planes = []
        acInfo = {}
        for a in aircraft["aircraft"]:
            if "r" in a.keys():
                if a["r"] != "":
                    if a["lat"] != 0.0:
                        planes.append(a["r"])
                        acd = {}
                        acd["hex"] = a["hex"]
                        if "flight" in a.keys():
                            acd["flight"] = a["flight"]
                        else:
                            acd["flight"] = "unknown"
                        acd["url"] = "{}/?icao={}".format(tar1090Host, a["hex"])
                        coords_home = (float(conf["lat"]), float(conf["lon"]))
                        coords_plane = (a["lon"], a["lat"])
                        dist = geopy.distance.geodesic(coords_home, coords_plane).km
                        acd["dist"] = round(dist, 2)
                        acd["type"] = a["t"]
                        #print("{} and {} are {}km apart".format(coords_home, coords_plane, round(dist, 2)))
                        acInfo[a["hex"]] = acd
        ntfyNumber = conf["ntfy_number"]
        planesWithinRange = len(planes)
        if planesWithinRange > ntfyNumber:
            message = "{} can see {} different aircraft right now!".format(conf["location_name"], planesWithinRange)
            title = "Lots of Traffic at {}!".format(conf["location_name"])
            ntfy(host=conf["ntfy_host"], topic=conf["ntfy_topic"], message=message, title=title, prio="{}".format(conf["ntfy_prio"]), click=tar1090Host)
        routes = flightDetails(planes, conf)
        stringToFile("routes.json", json.dumps(routes, indent=4))
        for route in routes:
            acd = acInfo[route["hex"]]
            watchedFlights = conf["ntfy_watched_flights"]
            print("{}: {} ({}km away)".format(route["callsign"], route["_airport_codes_iata"], acd["dist"]))
            acd["route"] = route["_airport_codes_iata"]
            acd["callsign"] = route["callsign"]
            logger.log(message=acd, conf=conf)
            notify = False
            if route["callsign"] in watchedFlights:
                print("{} is a watched flight".format(route["callsign"]))
                notify = True
            if acd["dist"] < notifyDistance:
                print("{} is within {}km of {}".format(route["callsign"], acd["dist"], conf["location_name"]))
                notify = True
            title = "{} Flying By Closely!".format(acd["type"])
            firstLetterOfType = str(acd["type"][0]).upper()
            article = "A"
            articleAnList = ["A", "E", "F", "H", "I", "L", "M", "N", "O", "R", "S", "X"]
            if firstLetterOfType in articleAnList:
                article = "An"
            message = "{} {} with callsign {} flying {} is only {} km from {}".format(article, acd["type"], route["callsign"], route["_airport_codes_iata"], acd["dist"], conf["location_name"])
            url = acd["url"]
            print("notify is {}".format(notify))
            if notify:
                print("I'm inside the notify block")
                ntfy(host=conf["ntfy_host"], topic=conf["ntfy_topic"], message=message, title=title, prio="{}".format(conf["ntfy_prio"]), click=url)
            else:
                print("No notification for {}".format(route["callsign"]))
        now = datetime.now(ZoneInfo(conf["tz"]))
        todayDate = now.strftime("%Y-%m-%d %H:%M:%S")
        print("Ending: {}".format(todayDate))
        time.sleep(sleepInterval)