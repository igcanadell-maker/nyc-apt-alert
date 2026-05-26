import json, os
import urllib.request, urllib.parse

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SE_AUTH_TOKEN = os.environ["SE_AUTH_TOKEN"]
SEEN_FILE = "seen.json"

AUTH_TOKEN = urllib.parse.unquote(SE_AUTH_TOKEN)

AREA_IDS = "103,104,105,106,107,108,109,110,112,113,115,116,117,120,122,130,131,132,133,137,141,142,143,146,152,157,158,162,302,303,304,305,306,307,310,313,318,319,320,321,322,324,325,326,328,329,340,343,346,354,355,358,364,367,412"

def get_listings():
    url = "https://streeteasy.com/api/v1/listings/rentals?areas=" + AREA_IDS + "&price_max=2500&status=open&sort_by=listed_at_desc&limit=50"
    req = urllib.request.Request(url)
    req.add_header("Authorization", AUTH_TOKEN)
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
    req.add_header("Accept", "application/json")
    req.add_header("Referer", "https://streeteasy.com/")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            print("Respuesta recibida, tipo: " + str(type(data)))
            if isinstance(data, list):
                return data
            for key in ["listings", "rentals", "results", "data", "edges"]:
                if key in data:
                    print("Listings en clave: " + key)
                    return data[key]
            print("Claves disponibles: " + str(list(data.keys()) if isinstance(data, dict) else "no es dict"))
            return []
    except Exception as e:
        print("Error: " + str(e))
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
        listing_url = "https://streeteasy.com" + slug if slug and not slug.startswith("http") else (slug or "https://streeteasy.com")
        beds_label = "Studio" if str(beds) in ["0", "0.0"] else str(beds) + " br"

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
