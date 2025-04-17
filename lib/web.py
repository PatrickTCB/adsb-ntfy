import requests
import json
from urllib.parse import urljoin

def saveResponse(fileName, contentsRaw):
    contents = str(contentsRaw)
    with open(fileName, "w+") as output_file:
        output_file.write(contents)
        output_file.close()

def get(host, path, headers={}, params={}, printMe=False, ignoreErrors=False, session=None, conf={}):
    if "https://" in host or "http://" in host:
        fullurl = urljoin(host, path)
    else:
        fullurl = urljoin("https://{}".format(host), path)
    if printMe:
        print("Trying: {}".format(fullurl))
    if session == None:
        s = requests.Session()
    else:
        s = session
    for k in headers.keys():
        s.headers[k] = headers[k]
    
    if "CUSTOM_HEADERS" in conf.keys():
        customHeaderDomains = conf["CUSTOM_HEADER_DOMAINS"]
        if host in customHeaderDomains:
            customHeaders = conf["CUSTOM_HEADERS"]
            for h in customHeaders.keys():
                s.headers[h] = customHeaders[h]

    if params == {}:
        result = s.get(fullurl)
    else:
        result = s.get(fullurl, params=params)
    if printMe:
        print(str(result.text))
    if result.status_code > 199 and result.status_code < 300:
        return result
    else:
        if ignoreErrors:
            return False
        print("Error when retrieving info from {}".format(host))
        print("Status: " + str(result.status_code))
        print("Attempted to get {}".format(fullurl))
        responseName = "error-{}{}.json".format(result.status_code, str(fullurl.replace("https:", "")).replace("/", "."))
        try:
            responseDict = json.loads(result.text)
            responseDict["path called"] = path
            responseDict["responseHeaders"] = result.headers
            saveResponse(responseName, json.dumps(responseDict))
        except:
            output = "{}\n{}".format(result.headers, result.text)
            saveResponse(responseName, output)
        print("Error response saved to {}".format(responseName))
        return False

def post(host, path, contentType, body={}, jsonBody=False, headers={}, printMe=False, session=None, ignoreErrors=False, conf={}):
    if "https://" in host or "http://" in host:
        fullurl = urljoin(host, path)
    else:
        fullurl = urljoin("https://{}".format(host), path)
    if printMe:
        print("Trying: {}".format(fullurl))
    if session == None:
        s = requests.Session()
    else:
        s = session
    s.headers["Content-Type"] = contentType
    for k in headers.keys():
        s.headers[k] = headers[k]
    if "CUSTOM_HEADERS" in conf.keys():
        customHeaderDomains = conf["CUSTOM_HEADER_DOMAINS"]
        if host in customHeaderDomains:
            customHeaders = conf["CUSTOM_HEADERS"]
            for h in customHeaders.keys():
                s.headers[h] = customHeaders[h]
    if jsonBody:
        result = s.post(fullurl, json=body)
    else:
        result = s.post(fullurl, data=body)
    if printMe:
        print(str(result.text))
    if result.status_code > 199 and result.status_code < 300:
        return result
    else:
        print("Error when retrieving info from {}".format(host))
        print("Status: " + str(result.status_code))
        print("Attempted to get " + str(path))
        if ignoreErrors:
            return False
        responseName = "error-{}{}.json".format(result.status_code, host.replace("https://", ""), path.replace("/", "."))
        try:
            responseDict = json.loads(result.text)
            responseDict["responseHeaders"] = result.headers
            responseDict["host"] = host
            responseDict["path called"] = path
            responseDict["requestBody"] = body
            saveResponse(responseName, json.dumps(responseDict))
        except:
            output = "{}\n{}".format(result.headers, result.text)
            saveResponse(responseName, output)
        print("Error response saved to {}".format(responseName))
        return False
