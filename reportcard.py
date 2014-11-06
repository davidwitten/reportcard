# Reportcard
# Noah Kim

# Import
import tkinter
import tkinter.ttk
import tkinter.scrolledtext
import tkinter.messagebox
import re
import os

import threading

import requests
import bs4

# Constant
MAIN_URL = "http://www.edline.net"
LOGIN_URL = "http://www.edline.net/InterstitialLogin.page"
LOGIN_POST_URL = "https://www.edline.net/post/InterstitialLogin.page"
NOTIFICATIONS_URL = "/Notifications.page"
REPORTS_URL = "/Current_Assignments_Report"

HEADER_DATA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko)"
                  "Chrome/31.0.1650.63"
                  "Safari/537.36"
}

LOGIN_DATA = {
    "TCNK": "authenticationEntryComponent",
    "submitEvent": "1",
    "guestLoginEvent": "",
    "enterClicked": "true",
    "bscf": "",
    "bscv": "",
    "targetEntid": "",
    "ajaxSupported": "yes"
}

# Edline
class Scraper:
    """Automated Edline scraper."""

    def __init__(self, username, password, pages):
        """Initialize a new scraper."""
        self.username = username
        self.password = password
        self.pages = pages

        self.finished = False

    def login(self):
        """Log in to Edline."""
        response = requests.get(LOGIN_URL, headers=HEADER_DATA)
        if response.status_code != 200:
            tkinter.messagebox.showerror("Failed to access Edline!")
            return
        self.cookies = response.cookies

        login_data = LOGIN_DATA.copy()
        login_data.update({"screenName": self.username, "kclq": self.password})
        response = requests.post(LOGIN_POST_URL, login_data,
                                 headers=HEADER_DATA, cookies=self.cookies,
                                 allow_redirects=False)

        self.location = response.headers["location"]
        if self.location == MAIN_URL + NOTIFICATIONS_URL:
            tkinter.messagebox.showerror("Bad login credentials!")
            return

        self.cookies.update(response.cookies)

    def scrape(self):
        """Scrape reports off of Edline."""
        self.reports = []
        for page in self.pages:
            reports_url = page + REPORTS_URL
            response = requests.get(reports_url, headers=HEADER_DATA,
                                    cookies=self.cookies)
            
            soup = bs4.BeautifulSoup(response.text)
            source = soup.findChild("iframe", {"id": "docViewBodyFrame"})["src"]
            response = requests.get(source, headers=HEADER_DATA,
                                    cookies=self.cookies)
            pattern = re.compile(r"Class: ([^(]+) \(\w+\)")
            course = pattern.search(response.text).groups()[0]

            soup = bs4.BeautifulSoup(response.text)
            data = []
            for child in soup.findChildren("td", {"valign": "center"}):
                text = child.get_text()       
                if text == "Current Assignments":
                    break
                data.append(text.replace("\xa0", ""))

            report = Report(course, data)
            self.reports.append(report)

        self.finished = True

class Report:
    """Report container class for Edline data."""

    def __init__(self, course, data):
        """Initialize a new report."""
        self.course = course
        self.data = data
        self.parse()

    def parse(self):
        self.categories = []
        for i in range(0, len(self.data)-3, 5):
            self.categories.append({
                "name": self.data[i],
                "weight": self.data[i+1],
                "percentage": self.data[i+3],
                "fraction": self.data[i+2]
            })
        self.cumulative = {"percentage": self.data[-2], "letter": self.data[-1]}

class Application:
    """Main application framework and user interface."""

    def setup(self):
        """Set up application scraper and interface data."""
        with open("edline.txt") as file:
            contents = file.read()
            lines = [line.strip() for line in contents.split(os.linesep)]
            username, password, *pages = lines

        self.scraper = Scraper(username, password, pages)
        self.scraper.login()
        self.scraper.scrape()

        self.window.destroy()
        self.window.quit()

    def load(self):
        """Load class data."""        
        for report in self.scraper.reports:
            self.treeview.insert(
                "", "end", report.course,
                values=(
                    " "*3+report.course.title(),
                    report.cumulative["percentage"],
                    report.cumulative["letter"]
                ))
            for category in report.categories:
                self.treeview.insert(
                    report.course, "end", report.course+"/"+category["name"],
                    values=(
                        " "*5+category["name"]+" ("+category["weight"]+"%)",
                        " "*2+category["percentage"],
                        " "*2+category["fraction"],
                    ))
                                                        

    def build(self):
        """Build the application interface."""
        self.window = tkinter.Tk()
        self.window.title("Report card")
        self.window.protocol("WM_DELETE_WINDOW", int)

        self.content = tkinter.Frame(self.window)
        self.content.pack(fill="both", padx=10, pady=5)
        self.message = tkinter.Label(self.content)
        self.message.config(text="Loading...", anchor="w", width=30)
        self.message.pack(pady=5, fill="x")
        self.progressbar = tkinter.ttk.Progressbar(self.content)
        self.progressbar.config(mode="indeterminate")
        self.progressbar.pack(fill="x", pady=5)

        setup_thread = threading.Thread(target=self.setup)
        setup_thread.start()

        self.window.mainloop()


        self.window = tkinter.Tk()
        self.window.title("Report card")

        self.treeview = tkinter.ttk.Treeview(self.window)
        self.treeview.config(columns=("Course", "Percentage", "Grade"))
        self.treeview.heading("#1", text="Course", anchor="w")
        self.treeview.heading("#2", text="Percentage", anchor="w")
        self.treeview.heading("#3", text="Grade", anchor="w")
        self.treeview.column('#0', stretch="no", minwidth=0, width=0)
        self.treeview.column('#1', stretch="no", minwidth=200, width=200)
        self.treeview.column('#2', stretch="no", minwidth=100, width=100)
        self.treeview.column('#3', stretch="no", minwidth=90, width=90)
        self.treeview.pack(fill="both", expand=1, padx=10, pady=10)

    def main(self):
        """Run the application."""
        self.window.mainloop()

app = Application()
app.build()
app.load()
app.main()
