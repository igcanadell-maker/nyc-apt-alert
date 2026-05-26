import json, os, re, subprocess, sys

subprocess.run([sys.executable, "-m", "pip", "install", "playwright", "-q"])
subprocess.run(["playwright", "install", "chromium", "--with-deps"], capture_output=True)

from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SEEN_FILE = "seen.json"

SEARCH_URL = "https://streeteasy.com/for-rent/nyc/status:open%7Cprice:500-2500%7Carea:103,104,105,106,107,108,109,110,112,113,115,116,117,120,122,130,131,132,133,137,141,142,143,146,152,157,158,162,302,303,304,305,306,307,310,313,318,319,320,321,322,324,325,326,328,329,340,343,346,354,355,358,364,367,412?sort_by=listed_at_desc"

def get_listings():
    listings = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"})
        try:
            page.goto(SEARCH_URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            content = page.content()
            ids = re.findall(r'"id"\s*:\s*(\d{6,})', content)
            prices = re.findall(r'"price"\s*:\s*(\d+)', content)
            addresses = re.findall(r'"address"\s*:\s*"([^"]+)"', content)
            neighborhoods = re.findall(r'"neighborhood"\s*:\s*"([^"]+)"', content)
            slugs = re.findall(r'"/rental/[^"]{5,}"', content)
            beds_list = re.findall(r'"bedrooms"\s*:\s*(\d+)', content)
            print("IDs encontrados: " + str(len(ids)))
            for i, apt_id in enumerate(ids[:50]):
                listings.append({
                    "id": apt_id,
                    "price": prices[i] if i < len(prices) else "?",
                    "address": addresses[i] if i < len(addresses) else "?",
                    "neighborhood": neighborhoods[i] if i < len(neighborhoods) else "?",
                    "slug": slugs[i].strip('"') if i < len(slugs) else "",
                    "bedrooms": beds_list[i] if i < len(beds_list) else "?",
                })
        except Exception as e:
            print("Error playwright: " + str(e))
        browser.close()
    return listings

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
    print("Total listings: " + str(len(listings)))

    for apt in listings:
        apt_id = str(apt.get("id", ""))
        if not apt_id or apt_id in seen:
            continue

        price = apt.get("price", "?")
        beds = apt.get("bedrooms", "?")
        area = apt.get("neighborhood", "?")
        address = apt.get("address", "?")
        slug = apt.get("slug", "")
        listing_url = "https://streeteasy.com" + slug if slug else SEARCH_URL
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
