import requests, json, os, re
from html.parser import HTMLParser

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SEEN_FILE = "seen.json"

SEARCH_URLS = [
    "https://streeteasy.com/for-rent/brooklyn/bed_stuy,boerum_hill,brooklyn_heights,bushwick,carroll_gardens,clinton_hill,cobble_hill,crown_heights,dumbo,downtown_brooklyn,east_flatbush,flatbush,fort_greene,gowanus,greenpoint,kensington,park_slope,prospect_heights,prospect_lefferts_gardens,prospect_park_south,williamsburg,ditmas_park,windsor_terrace,ridgewood?price=-2500&beds=0,1,2,3,4",
    "https://streeteasy.com/for-rent/manhattan/financial_district,tribeca,soho,greenwich_village,west_village,chelsea,flatiron,gramercy,murray_hill,midtown,hells_kitchen,upper_west_side,upper_east_side,harlem,east_harlem,washington_heights,inwood,lower_east_side,east_village,noho,nolita,chinatown,battery_park_city?price=-2500&beds=0,1,2,3,4",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_listings_from_url(url):
    listings = []
    try:
        api_url = url.replace("streeteasy.com/for-rent/", "streeteasy.com/api/v1/listings/rentals?areas=")
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        # Buscar JSON embebido en la página
        content = r.text
        match = re.search(r'"listings"\s*:\s*(\[.*?\])\s*[,}]', content, re.DOTALL)
        if match:
            try:
                listings = json.loads(match.group(1))
            except:
                pass
        
        # Alternativa: buscar por listing IDs
        if not listings:
            ids = re.findall(r'"id"\s*:\s*(\d+)', content)
            prices = re.findall(r'"price"\s*:\s*(\d+)', content)
            addresses = re.findall(r'"address"\s*:\s*"([^"]+)"', content)
            neighborhoods = re.findall(r'"neighborhood"\s*:\s*"([^"]+)"', content)
            slugs = re.findall(r'"slug"\s*:\s*"(/rental/[^"]+)"', content)
            beds_list = re.findall(r'"bedrooms"\s*:\s*(\d+)', content)
            
            for i, apt_id in enumerate(ids[:50]):
                listings.append({
                    "id": apt_id,
                    "price": prices[i] if i < len(prices) else "?",
                    "address": addresses[i] if i < len(addresses) else "?",
                    "neighborhood": neighborhoods[i] if i < len(neighborhoods) else "?",
                    "slug": slugs[i] if i < len(slugs) else "",
                    "bedrooms": beds_list[i] if i < len(beds_list) else "?",
                })
    except Exception as e:
        print(f"Error: {e}")
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
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def main():
    seen = load_seen()
    new_count = 0

    for search_url in SEARCH_URLS:
        listings = get_listings_from_url(search_url)
        print(f"Encontrados {len(listings)} listings en {search_url[:60]}...")

        for apt in listings:
            apt_id = str(apt.get("id", ""))
            if not apt_id or apt_id in seen:
                continue

            price = apt.get("price", "?")
            beds = apt.get("bedrooms", "?")
            area = apt.get("neighborhood", apt.get("area", "?"))
            address = apt.get("address", "?")
            slug = apt.get("slug", apt.get("url", ""))
            listing_url = ("https://streeteasy.com" + slug) if slug and not slug.startswith("http") else (slug or search_url)

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
                f"🔗
