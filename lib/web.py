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
    
    if "custom_headers" in conf.keys():
        customHeaderDomains = conf["custom_headers_domains"]
        if host in customHeaderDomains:
            customHeaders = conf["custom_headers"]
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
            responseDict["path"] = path
            responseDict["responseHeaders"] = dict(result.headers)
            try:
                import curlify
                requestSent = result.request
                responseDict["curl"] = curlify.to_curl(requestSent)
            except:
                print("Couldn't add curl version of request to error dict\nInstall curlify if you want that to work.")
            saveResponse(responseName, json.dumps(responseDict, default=str))
        except:
            output = {}
            output["headers"] = dict(result.headers)
            output["text"] = result.text
            try:
                import curlify
                requestSent = result.request
                output["curl"] = curlify.to_curl(requestSent)
            except:
                print("Couldn't add curl version of request to error dict\nInstall curlify if you want that to work.")
            saveResponse(responseName, json.dumps(output, default=str))
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
    if "custom_headers" in conf.keys():
        customHeaderDomains = conf["custom_headers_domains"]
        if host in customHeaderDomains:
            customHeaders = conf["custom_headers"]
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
            responseDict["path"] = path
            responseDict["responseHeaders"] = dict(result.headers)
            try:
                import curlify
                requestSent = result.request
                responseDict["curl"] = curlify.to_curl(requestSent)
            except:
                print("Couldn't add curl version of request to error dict\nInstall curlify if you want that to work.")
            saveResponse(responseName, json.dumps(responseDict, default=str))
        except:
            output = {}
            output["headers"] = dict(result.headers)
            output["text"] = result.text
            try:
                import curlify
                requestSent = result.request
                output["curl"] = curlify.to_curl(requestSent)
            except:
                print("Couldn't add curl version of request to error dict\nInstall curlify if you want that to work.")
            saveResponse(responseName, json.dumps(output, default=str))
        print("Error response saved to {}".format(responseName))
        return False
