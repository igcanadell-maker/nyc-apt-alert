import json, os, re, subprocess, sys

subprocess.run([sys.executable, "-m", "pip", "install", "playwright", "-q"])
subprocess.run(["playwright", "install", "chromium", "--with-deps"], capture_output=True)

from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SEEN_FILE = "seen.json"

SEARCH_URL = "https://streeteasy.com/for-rent/nyc/status:open%7Cprice:500-2500%7Carea:103,104,105,106,107,108,109,110,112,113,115,116,117,120,122,130,131,132,133,137,141,142,143,146,152,157,158,162,302,303,304,305,306,307,310,313,318,319,320,321,322,324,325,326,328,329,340,343,346,354,355,358,364,367,412?sort_by=listed_at_desc"

captured = []

def handle_response(response):
    url = response.url
    if "listing" in url.lower() or "search" in url.lower() or "rental" in url.lower():
        try:
            data = response.json()
            print("API capturada: " + url[:80])
            if isinstance(data, list):
                captured.extend(data)
            elif isinstance(data, dict):
                for key in ["listings", "rentals", "edges", "results", "data"]:
                    if key in data:
                        items = data[key]
                        if isinstance(items, list):
                            captured.extend(items)
                            break
        except:
            pass

def get_listings():
    global captured
    captured = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("response", handle_response)
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })
        try:
            page.goto(SEARCH_URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(8000)
            print("Total respuestas capturadas: " + str(len(captured)))
        except Exception as e:
            print("Error: " + str(e))
        browser.close()
    return captured

def load_seen():
    try:
        with open(SEEN_FILE) as f:
