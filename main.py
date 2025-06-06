import requests
import time
import os
from bs4 import BeautifulSoup

# --- CONFIGURA QUI ---
SEARCH_URLS = [
    "https://www.catawiki.com/it/s?q=Gold%20%26%20gold%20NIkka",
    "https://www.catawiki.com/it/s?q=Suntory",
    "https://www.catawiki.com/it/s?q=macallan"
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

def main_loop():
    global notified_ids
    while True:
        for url in SEARCH_URLS:
            try:
                resp = requests.get(url)
                ids = extract_auction_ids(resp.text)
                for auction_id in ids:
                    if auction_id not in notified_ids:
                        # Invia la notifica e marca come notificato
                        message = f"Nuova asta trovata: https://www.catawiki.com/it/l/{auction_id}"
                        send_telegram(message)
                        notified_ids.add(auction_id)
            except Exception as e:
                print(f"Errore su {url}: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
