# Edline
# Noah Kim

# Import
import re

import requests
import bs4

# File
print("Parsing edline file...")
with open("edline.txt") as file:
    contents = file.read()
    username, password, *pages = [line.strip() for line in contents.split("\n")]

# Constant
URL = "http://www.edline.net"
LOGIN_URL = "http://www.edline.net/InterstitialLogin.page"
LOGIN_POST_URL = "https://www.edline.net/post/InterstitialLogin.page"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko)"
                  "Chrome/31.0.1650.63"
                  "Safari/537.36"
}

DATA = {
    "TCNK": "authenticationEntryComponent",
    "submitEvent": "1",
    "guestLoginEvent": "",
    "enterClicked": "true",
    "bscf": "",
    "bscv": "",
    "targetEntid": "",
    "ajaxSupported": "yes",
    "screenName": username,
    "kclq": password
}

# Login
print("Logging in...")
response = requests.get(LOGIN_URL, headers=HEADERS)
if response.status_code != 200:
    print("Failed to access Edline")
cookies = response.cookies
response = requests.post(LOGIN_POST_URL, data=DATA, headers=HEADERS,
                         cookies=cookies, allow_redirects=False)
location_url = response.headers["location"]
if location_url == URL + "/Notification.page":
    print("Bad credentials")
cookies.update(response.cookies)

# Class list
print("Retrieving grades...")
print()
for page in pages:
    report_url = page + "/Current_Assignments_Report/Kim__Noah"
    response = requests.get(report_url, headers=HEADERS, cookies=cookies)
    soup = bs4.BeautifulSoup(response.text)
    iframe = soup.findChild("iframe", {"id": "docViewBodyFrame"})
    report_actual_url = iframe["src"]
    response = requests.get(report_actual_url, headers=HEADERS, cookies=cookies)
    class_name = re.search(r"Class: ([^(]+) \(\w+\)", response.text).groups()[0]
    soup = bs4.BeautifulSoup(response.text)

    lines = []
    for child in soup.findChildren("td", {"valign": "center"}):
        text = child.get_text()       
        if text == "Current Assignments":
            break
        if text:
            lines.append(text)

    print("%-20s%-6s%-1s" % (class_name, lines[-2], lines[-1]))
