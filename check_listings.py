import requests, json, os, hashlib

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SEEN_FILE = "seen.json"

AREA_IDS = [
    "Bedford-Stuyvesant", "Boerum Hill", "Brooklyn Heights", "Bushwick",
    "Carroll Gardens", "Clinton Hill", "Cobble Hill", "Crown Heights",
    "DUMBO", "Downtown Brooklyn", "East Flatbush", "Flatbush",
    "Fort Greene", "Gowanus", "Greenpoint", "Kensington", "Park Slope",
    "Prospect Heights", "Prospect Lefferts Gardens", "Prospect Park South",
    "Williamsburg", "Ditmas Park", "Windsor Terrace", "Ridgewood",
    "Financial District", "Tribeca", "SoHo", "Greenwich Village",
    "West Village", "Chelsea", "Flatiron", "Gramercy", "Murray Hill",
    "Midtown", "Hell's Kitchen", "Upper West Side", "Upper East Side",
    "Harlem", "East Harlem", "Washington Heights", "Inwood",
    "Lower East Side", "East Village", "NoHo", "Nolita", "Chinatown",
    "Battery Park City", "Two Bridges"
]

def get_listings():
    all_listings = []
    for area in AREA_IDS:
        try:
            url = "https://streeteasy.com/api/rental-search"
            params = {
                "area": area,
                "price_max": 2500,
                "bedrooms_min": 0,
                "sort_by": "listed_desc",
                "page": 1
            }
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, params=params, headers=headers, timeout=10)
            data = r.json()
            listings = data.get("listings", data.get("rentals", []))
            all_listings.extend(listings)
        except Exception as e:
            print(f"Error fetching {area}: {e}")
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
        apt_id = str(apt.get("id", apt.get("listing_id", "")))
        if not apt_id or apt_id in seen:
            continue

        price = apt.get("price", apt.get("rent", "?"))
        beds = apt.get("bedrooms", apt.get("beds", "?"))
        area = apt.get("area", apt.get("neighborhood", "?"))
        address = apt.get("address", apt.get("full_address", "Sin dirección"))
        url = apt.get("url", apt.get("listing_url", ""))
        if url and not url.startswith("http"):
            url = "https://streeteasy.com" + url

        beds_label = "Studio" if str(beds) == "0" else f"{beds} br"

        # Highlight si está por debajo de 2300
        star = "⭐" if isinstance(price, (int, float)) and price <= 2300 else ""

        msg = (
            f"🏠 <b>Nuevo depto en NYC</b> {star}\n"
            f"📍 {area} — {address}\n"
            f"💰 ${price}/mes | {beds_label}\n"
            f"🔗 <a href='{url}'>Ver en StreetEasy</a>"
        )

        send_telegram(msg)
        seen.add(apt_id)
        new_count += 1

    save_seen(seen)
    print(f"Enviadas {new_count} alertas nuevas.")

if __name__ == "__main__":
    main()
