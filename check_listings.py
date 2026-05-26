import requests, json, os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SEEN_FILE = "seen.json"

AREA_IDS = [
    297, 298, 299, 300, 301, 302, 303, 304, 305, 306,
    307, 308, 309, 310, 311, 312, 313, 314, 315, 316,
    317, 318, 319, 320, 104, 105, 106, 107, 108, 109,
    110, 111, 112, 113, 114, 115, 116, 117, 118, 119,
    120, 121, 122, 123, 124, 125
]

AREA_NAMES = {
    297: "Bedford-Stuyvesant", 298: "Boerum Hill", 299: "Brooklyn Heights",
    300: "Bushwick", 301: "Carroll Gardens", 302: "Clinton Hill",
    303: "Cobble Hill", 304: "Crown Heights", 305: "DUMBO",
    306: "Downtown Brooklyn", 307: "East Flatbush", 308: "Flatbush",
    309: "Fort Greene", 310: "Gowanus", 311: "Greenpoint",
    312: "Kensington", 313: "Park Slope", 314: "Prospect Heights",
    315: "Prospect Lefferts Gardens", 316: "Prospect Park South",
    317: "Williamsburg", 318: "Ditmas Park", 319: "Windsor Terrace",
    320: "Ridgewood", 104: "Financial District", 105: "Tribeca",
    106: "SoHo", 107: "Greenwich Village", 108: "West Village",
    109: "Chelsea", 110: "Flatiron", 111: "Gramercy", 112: "Murray Hill",
    113: "Midtown", 114: "Hell's Kitchen", 115: "Upper West Side",
    116: "Upper East Side", 117: "Harlem", 118: "East Harlem",
    119: "Washington Heights", 120: "Inwood", 121: "Lower East Side",
    122: "East Village", 123: "NoHo", 124: "Nolita", 125: "Chinatown"
}

def get_listings():
    all_listings = []
    for area_id in AREA_IDS:
        try:
            url = "https://api.apify.com/v2/acts/qwady~nyc-real-estate-api/run-sync-get-dataset-items"
            # Usamos el endpoint directo de Borough
            url = f"https://nyc-real-estate-api.apify.actor/rentals?areaId={area_id}&priceMax=2500&bedroomsMin=0&perPage=50"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=15)
            data = r.json()
            listings = data.get("edges", data.get("listings", data.get("rentals", [])))
            if isinstance(listings, list):
                for item in listings:
                    node = item.get("node", item)
                    node["_area_name"] = AREA_NAMES.get(area_id, str(area_id))
                    all_listings.append(node)
        except Exception as e:
            print(f"Error fetching area {area_id}: {e}")
    return all_listings

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
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def main():
    seen = load_seen()
    listings = get_listings()
    new_count = 0

    for apt in listings:
        apt_id = str(apt.get("id", apt.get("listingId", apt.get("listing_id", ""))))
        if not apt_id or apt_id in seen:
            continue

        price = apt.get("price", apt.get("rentPrice", apt.get("rent", "?")))
        beds = apt.get("bedrooms", apt.get("beds", "?"))
        area = apt.get("_area_name", apt.get("neighborhood", apt.get("area", "?")))
        address = apt.get("address", apt.get("fullAddress", "Sin dirección"))
        slug = apt.get("slug", apt.get("url", ""))
        if slug and not slug.startswith("http"):
            listing_url = "https://streeteasy.com" + slug
        else:
            listing_url = slug or "https://streeteasy.com/for-rent/nyc"

        beds_label = "Studio" if str(beds) in ["0", "0.0"] else f"{beds} br"

        try:
            price_num = int(str(price).replace("$", "").replace(",", "").strip())
            star = "⭐" if price_num <= 2300 else ""
        except:
            star = ""

        msg = (
            f"🏠 <b>Nuevo depto en NYC</b> {star}\n"
            f"📍 {area} — {address}\n"
            f"💰 ${price}/mes | {beds_label}\n"
            f"🔗 <a href='{listing_url}'>Ver en StreetEasy</a>"
        )

        send_telegram(msg)
        seen.add(apt_id)
        new_count += 1

    save_seen(seen)
    print(f"Enviadas {new_count} alertas nuevas.")

if __name__ == "__main__":
    main()
