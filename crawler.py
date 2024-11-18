import urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["crawler_db"]
pages_collection = db["pages"]

START_URL = "https://www.cpp.edu/sci/computer-science"
TARGET_URL = "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"
TARGET_H1_CLASS = "cpp-h1"

class Frontier:
    def __init__(self):
        self.queue = [START_URL]
        self.visited = set()

    def nextURL(self):
        return self.queue.pop(0) if self.queue else None

    def addURL(self, url):
        if url not in self.visited:
            self.queue.append(url)

    def done(self):
        return not self.queue

    def markVisited(self, url):
        self.visited.add(url)

def retrieveHTML(url):
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                return response.read()
            else:
                print(f"skipping {url}: HTTP {response.status}")
                return None
    except Exception as e:
        print(f"error fetching {url}: {e}")
        return None

def storePage(url, html):
    pages_collection.insert_one({"url": url, "html": html.decode('utf-8')})
    print(f"Stored page: {url}")

def isTargetPage(html):
    soup = BeautifulSoup(html, "html.parser")
    target_h1 = soup.find("h1", {"class": TARGET_H1_CLASS})
    return target_h1 is not None and "Permanent Faculty" in target_h1.text

def extractLinks(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base_url, href)
        #validate relevant links
        if full_url.endswith((".html", ".shtml")) and "computer-science" in full_url.lower():
            if "faculty" in full_url.lower() or "staff" in full_url.lower():
                print(f"Valid link: {full_url}")
                links.append(full_url)
    return links

def crawlerThread(frontier):
    while not frontier.done():
        url = frontier.nextURL()
        if url in frontier.visited:
            print(f"already visited: {url}")
            continue

        print(f"Crawling: {url}")
        html = retrieveHTML(url)
        if not html:
            print(f"fail: {url}")
            continue

        #store page content
        storePage(url, html)

        #mark url as visited
        frontier.markVisited(url)

        #check if target page
        if url == TARGET_URL or isTargetPage(html):
            print(f"target found: {url}")
            return

        #add unvisited urls to the frontier
        for link in extractLinks(html, url):
            if link not in frontier.visited:
                print(f"Adding to frontier: {link}")
                frontier.addURL(link)

#initialize frontier
frontier = Frontier()
crawlerThread(frontier)
