# Reportcard
# Noah Kim

# Import
import tkinter
import tkinter.ttk
import tkinter.scrolledtext
import re
import requests
import bs4

# Constant
URL = "http://www.edline.net"
LOGIN_URL = "http://www.edline.net/InterstitialLogin.page"
LOGIN_POST_URL = "https://www.edline.net/post/InterstitialLogin.page"

# Function
def shorten(string, length):
    """If a string is too long truncate and add ellipsis."""
    return string[:length-3] + "..." if len(string) > length else string

# Class
class Scraper:
    """Automated Edline scraper."""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko)"
                      "Chrome/31.0.1650.63"
                      "Safari/537.36"
    }

    data = {
        "TCNK": "authenticationEntryComponent",
        "submitEvent": "1",
        "guestLoginEvent": "",
        "enterClicked": "true",
        "bscf": "",
        "bscv": "",
        "targetEntid": "",
        "ajaxSupported": "yes"
    }

    def __init__(self, username, password, pages):
        """Initialize a new scraper."""
        self.data["screenName"] = username
        self.data["kclq"] = password
        self.pages = pages

    def log_in(self):
        """Log in to Edline."""
        response = requests.get(LOGIN_URL, headers=self.headers)
        if response.status_code != 200:
            print("Failed to access Edline!")
            quit()
        self.cookies = response.cookies
        response = requests.post(LOGIN_POST_URL, data=self.data,
                                 headers=self.headers, cookies=self.cookies,
                                 allow_redirects=False)
        location_url = response.headers["location"]
        if location_url == URL + "/Notification.page":
            print("Bad credentials")
            quit()
        self.cookies.update(response.cookies)

    def scrape_reports(self):
        """Scrape reports from Edline"""
        self.reports = []
        for page in self.pages:
            reports_url = page + "/Current_Assignments_Report"
            response = requests.get(reports_url, headers=self.headers,
                                    cookies=self.cookies)
            soup = bs4.BeautifulSoup(response.text)
            iframe = soup.findChild("iframe", {"id": "docViewBodyFrame"})
            reports_actual_url = iframe["src"]
            
            response = requests.get(reports_actual_url, headers=self.headers,
                                    cookies=self.cookies)
            course = re.search(r"Class: ([^(]+) \(\w+\)", response.text)
            course = course.groups()[0]
            soup = bs4.BeautifulSoup(response.text)

            data = []
            for child in soup.findChildren("td", {"valign": "center"}):
                text = child.get_text()       
                if text == "Current Assignments":
                    break
                data.append(text.replace("\xa0", ""))

            report = Report(course, data)
            self.reports.append(report)

class Report:
    """Generated report based on Edline data."""

    def __init__(self, course, data):
        """Initialize a new report."""
        self.course = course
        self.data = data

        self.parse_data()

    def parse_data(self):
        self.categories = []
        for i in range(0, len(self.data) - 3, 5):
            self.categories.append((self.data[i], self.data[i+1],
                                    self.data[i+3], self.data[i+2]))
        self.cumulative = (self.data[-2], self.data[-1])

class Viewer:
    """Main application user interface."""

    def __init__(self):
        """Initialize a new reportcard viewer."""
        pass

    def load(self):
        """Load the application."""        
        with open("edline.txt") as file:
            contents = file.read()
            username, password, *pages = [line.strip() for line in contents.split("\n")]
        self.progressbar.step(10) # 10
        self.window.update()

        self.scraper = Scraper(username, password, pages)
        self.progressbar.step(10) # 20
        self.window.update()
    
        self.scraper.log_in()
        self.progressbar.step(15) # 35
        self.window.update()

        self.scraper.scrape_reports()
        self.progressbar.step(64) # 99
        self.window.update()

        self.window.destroy()
        self.window.quit()

    def setup(self):
        """Set up for Edline data."""#List on side
        if self.sidebar_list.size() == 0:
            self.sidebar_list.insert("end", "Summary")
            for report in self.scraper.reports:
                self.sidebar_list.insert("end", report.course.title())
        self.sidebar_list.selection_set(0)

    def poll(self):
        z = []
        """Update the current content."""
        if self.sidebar_list.curselection():
            selection = int(self.sidebar_list.curselection()[0])#Which class is selected (summary is 0)
            if selection == 0:
                display = ""
                for report in self.scraper.reports:
                    display += "%-20s%-8s%s\n" % ((report.course.title(),) + report.cumulative)
                    z.append(['E','D','C','B','A'].index(report.cumulative[1]))
                self.content_text.config(state="normal")
                self.content_text.delete("1.0", "end")
                self.content_text.insert("1.0", display)
                self.content_text.insert("9.0","-"*30+'\n')
                self.content_text.insert("10.0","%-20s%-8s"%('GPA',str(sum(z)/len(z))))
                self.content_text.config(state="disabled")
            else:
                selection -= 1
                report = self.scraper.reports[selection]
                display = ""
                display += "%s\n\n" % report.course.title()
                for category in report.categories:
                    name = "%s (%s%%)" % (shorten(category[0], 17), category[1])
                    display += "%-27s%-7s%s\n" % (name, category[2],
                                                  category[3])
                display += "\n%-27s%-7s%s\n" % (("Cumulative",) +
                                                report.cumulative)
                self.content_text.config(state="normal")
                self.content_text.delete("1.0", "end")
                self.content_text.insert("1.0", display)
                self.content_text.config(state="disabled")               
                    
        self.window.after(100, self.poll)#updates every 10th of a second

    def build(self):
        """Build the interface."""
        self.window = tkinter.Tk()
        self.window.title("Report Card")
        self.window.config(width=500)

        self.content = tkinter.Frame(self.window)
        self.content.pack(fill="both", padx=10, pady=5)
        self.message = tkinter.Label(self.content)
        self.message.config(text="Loading...")
        self.message.pack(pady=5)
        self.progressbar = tkinter.ttk.Progressbar(self.content)
        self.progressbar.pack(side="bottom", pady=5)

        self.window.after(15, self.load)
        self.window.mainloop()

        self.window = tkinter.Tk()
        self.window.title("Report Card")

        self.sidebar = tkinter.Frame(self.window)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar_list = tkinter.Listbox(self.sidebar)
        self.sidebar_list.config(width=25, selectmode="single")
        self.sidebar_list.pack(side="left", fill="y")
        self.sidebar_scroll = tkinter.Scrollbar(self.sidebar)
        self.sidebar_scroll.pack(side="right", fill="y")
        self.sidebar_list.config(yscrollcommand=self.sidebar_scroll.set)
        self.sidebar_scroll.config(command=self.sidebar_list.yview)
        
        self.content = tkinter.Frame(self.window)
        self.content.pack(side="right", fill="y")
        self.content_text = tkinter.scrolledtext.ScrolledText(self.content)
        self.content_text.config(width=50, state="disabled")
        self.content_text.pack(fill="both")

        self.window.after(10, self.setup)
        self.window.after(100, self.poll)

    def main(self):
        """Run the interface."""
        self.window.mainloop()

v = Viewer()
v.build()
v.main()
