import requests
import time
from bs4 import BeautifulSoup
import re

# Header per simulare browser reale
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# --- CONFIGURA QUI ---
SEARCH_URLS = [
    "https://www.catawiki.com/it/s?q=Gold%20%26%20gold%20NIkka",
]
TELEGRAM_BOT_TOKEN = '7825951821:AAHZL0usBlDhM3GEekTgRoNc-DArOipCdjc'
CHAT_ID = '633015535'
CHECK_INTERVAL = 60  # secondi
# ---------------------

notified_ids = set()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

def extract_auction_ids(html):
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)
    ids = []
    for link in links:
        if "/l/" in link["href"]:
            # Match tipo "/l/92517579-nikka-gold-..." -> prendi l'ID
            parts = link["href"].split("/")
            for i, p in enumerate(parts):
                if p == "l" and i+1 < len(parts):
                    id_part = parts[i+1].split("-")[0]
                    if id_part.isdigit():
                        ids.append(id_part)
    return list(set(ids))

def extract_auction_details(auction_url):
    resp = requests.get(auction_url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # debug
    with open("debug_catawiki.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
    
    # Prezzo attuale
    try:
        price_str = soup.select_one('[data-test="lot-current-price"]').text
        price = float(price_str.replace('€', '').replace('.', '').replace(',', '.').strip())
    except Exception as e:
        price = None

    # Paese venditore
    try:
        location = soup.select_one('[data-test="seller-location"]').text.strip()
    except Exception as e:
        location = "?"

    # Spedizione
    shipping = 0
    try:
        # Cerca il valore della spedizione in euro, se disponibile
        ship_text = ""
        for div in soup.find_all('div'):
            if div.text and "Spedizione" in div.text and "€" in div.text:
                ship_text = div.text
                break
        if ship_text:
            m = re.search(r"€\s*([\d\.,]+)", ship_text)
            if m:
                shipping = float(m.group(1).replace('.', '').replace(',', '.'))
    except Exception as e:
        shipping = 0

    # Scadenza asta
    try:
        time_tag = soup.find('time')
        auction_end = time_tag['datetime']
    except Exception as e:
        auction_end = "?"

    # Commissione Catawiki (default 12.5%)
    commission_rate = 0.125
    try:
        comm_elem = soup.find(string=lambda x: x and "Commissione Catawiki" in x)
        if comm_elem:
            m = re.search(r'(\d{1,2}[,.]?\d*)\%', comm_elem)
            if m:
                commission_rate = float(m.group(1).replace(',', '.')) / 100
    except Exception as e:
        commission_rate = 0.125

    if price:
        commission = round(price * commission_rate, 2)
        totale = round(price + commission + shipping, 2)
    else:
        commission = totale = 0

    return {
        'prezzo': price,
        'ubicazione': location,
        'spedizione': shipping,
        'commissione': commission,
        'totale': totale,
        'fine': auction_end
    }

def main_loop():
    global notified_ids
    while True:
        for url in SEARCH_URLS:
            try:
                resp = requests.get(url, headers=HEADERS)
                ids = extract_auction_ids(resp.text)
                for auction_id in ids:
                    if auction_id not in notified_ids:
                        auction_url = f"https://www.catawiki.com/it/l/{auction_id}"
                        details = extract_auction_details(auction_url)
                        msg = (
                            f"🟡 NUOVA ASTA\n"
                            f"{auction_url}\n"
                            f"Ubicazione: {details['ubicazione']}\n"
                            f"Prezzo attuale: €{details['prezzo']}\n"
                            f"Spedizione: €{details['spedizione']}\n"
                            f"Commissione stimata: €{details['commissione']}\n"
                            f"Totale stimato: €{details['totale']}\n"
                            f"Fine asta: {details['fine']}\n"
                        )
                        send_telegram(msg)
                        notified_ids.add(auction_id)
            except Exception as e:
                print(f"Errore su {url}: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
