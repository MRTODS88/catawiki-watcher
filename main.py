def extract_auction_details(auction_url):
    resp = requests.get(auction_url, headers=HEADERS)
    
    # debug
    with open("debug_catawiki.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
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
