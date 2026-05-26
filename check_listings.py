import json, os, time
import urllib.request, urllib.parse

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
APIFY_TOKEN = os.environ["APIFY_TOKEN"]
SEEN_FILE = "seen.json"

SEARCH_URL = "https://streeteasy.com/for-rent/nyc/status:open%7Cprice:500-2500%7Carea:103,104,105,106,107,108,109,110,112,113,115,116,117,120,122,130,131,132,133,137,141,142,143,146,152,157,158,162,302,303,304,305,306,307,310,313,318,319,320,321,322,324,325,326,328,329,340,343,346,354,355,358,364,367,412?sort_by=listed_at_desc"

def run_apify_scraper():
    print("Iniciando scraper en Apify...")
    input_data = json.dumps({
        "startUrls": [{"url": SEARCH_URL}],
        "maxItems": 100,
    }).encode()

    req = urllib.request.Request(
        "https://api.apify.com/v2/acts/memo23~apify-streeteasy-cheerio/run-sync-get-dataset-items?token=" + APIFY_TOKEN + "&timeout=120&memory=1024",
        data=input_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=130) as resp:
            data = json.loads(resp.read())
            print("Items recibidos: " + str(len(data)))
            return data
    except Exception as e:
        print("Error Apify: " + str(e))
        return []

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
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}).encode()
    try:
        urllib.request.urlopen(url, data)
    except Exception as e:
        print("Error Telegram: " + str(e))

def main():
    seen = load_seen()
    new_count = 0
    listings = run_apify_scraper()

    for apt in listings:
        if not isinstance(apt, dict):
            continue

        apt_id = str(apt.get("id", apt.get("listingId", apt.get("url", ""))))
        if not apt_id or apt_id in seen:
            continue

        price = apt.get("price", apt.get("rentPrice", "?"))
        beds = apt.get("bedrooms", apt.get("beds", "?"))
        area = apt.get("neighborhood", apt.get("area", "?"))
        address = apt.get("address", apt.get("fullAddress", "?"))
        listing_url = apt.get("url", apt.get("listingUrl", SEARCH_URL))
        if listing_url and not listing_url.startswith("http"):
            listing_url = "https://streeteasy.com" + listing_url

        beds_label = "Studio" if str(beds) in ["0", "0.0", "studio", "Studio"] else str(beds) + " br"

        try:
            price_num = int(str(price).replace("$","").replace(",","").strip())
            star = " PRECIO IDEAL" if price_num <= 2300 else ""
        except:
            star = ""

        msg = (
            "Nuevo depto en NYC" + star + "\n"
            "Barrio: " + str(area) + " - " + str(address) + "\n"
            "Precio: $" + str(price) + "/mes | " + beds_label + "\n"
            "Ver: <a href='" + str(listing_url) + "'>StreetEasy</a>"
        )

        send_telegram(msg)
        seen.add(apt_id)
        new_count += 1

    save_seen(seen)
    print("Enviadas " + str(new_count) + " alertas nuevas.")

if __name__ == "__main__":
    main()
