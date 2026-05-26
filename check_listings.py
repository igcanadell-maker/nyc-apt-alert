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
            return set(json.load(f))
    except:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def send_telegram(msg):
    import urllib.request, urllib.parse
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}).encode()
    urllib.request.urlopen(url, data)

def main():
    seen = load_seen()
    new_count = 0
    listings = get_listings()
    print("Listings encontrados: " + str(len(listings)))

    for apt in listings:
        if not isinstance(apt, dict):
            continue
        apt_id = str(apt.get("id", apt.get("listingId", "")))
        if not apt_id or apt_id in seen:
            continue

        price = apt.get("price", apt.get("rentPrice", "?"))
        beds = apt.get("bedrooms", apt.get("beds", "?"))
        area = apt.get("neighborhood", apt.get("area", apt.get("areaName", "?")))
        address = apt.get("address", apt.get("fullAddress", "?"))
        slug = apt.get("slug", apt.get("url", ""))
        listing_url = "https://streeteasy.com" + slug if slug and not slug.startswith("http") else (slug or SEARCH_URL)
        beds_label = "Studio" if str(beds) in ["0", "0.0"] else str(beds) + " br"

        try:
            price_num = int(str(price).replace("$","").replace(",","").strip())
            star = " PRECIO IDEAL" if price_num <= 2300 else ""
        except:
            star = ""

        msg = (
            "Nuevo depto en NYC" + star + "\n"
            "Barrio: " + area + " - " + address + "\n"
            "Precio: $" + str(price) + "/mes | " + beds_label + "\n"
            "Ver: <a href='" + listing_url + "'>StreetEasy</a>"
        )

        send_telegram(msg)
        seen.add(apt_id)
        new_count += 1

    save_seen(seen)
    print("Enviadas " + str(new_count) + " alertas nuevas.")

if __name__ == "__main__":
    main()
