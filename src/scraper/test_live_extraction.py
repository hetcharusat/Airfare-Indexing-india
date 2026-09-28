import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re
import json

def test_google_flights_deep_scrape(origin="DEL", destination="BOM", days_out=7):
    flight_date = (datetime.now() + timedelta(days=days_out)).strftime("%Y-%m-%d")
    url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{flight_date}%20oneway&curr=INR"
    print(f"Scraping real flights from: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-IN"
        )
        page = context.new_page()

        # Intercept any XHR/Fetch calls containing flight data
        captured_json_payloads = []
        page.on("response", lambda res: captured_json_payloads.append(res.url) if "flights" in res.url or "search" in res.url else None)

        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)

        # Let's inspect the flight listings
        # Google Flights renders cards inside li.pIav2d
        cards = page.locator("li.pIav2d").all()
        print(f"Total real flight cards found: {len(cards)}")

        extracted_flights = []
        for i, card in enumerate(cards):
            text = card.inner_text()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            
            # Find price
            price = None
            price_match = re.search(r"₹\s*([\d,]+)", text)
            if price_match:
                price = int(price_match.group(1).replace(",", ""))

            # Identify airline
            airline = "Unknown"
            if "Air India Express" in text:
                airline = "Air India Express"
            elif "Air India" in text:
                airline = "Air India"
            elif "IndiGo" in text:
                airline = "IndiGo"
            elif "Akasa Air" in text:
                airline = "Akasa Air"
            elif "SpiceJet" in text:
                airline = "SpiceJet"
            elif "Vistara" in text:
                airline = "Vistara"

            # Departure / Arrival times
            times = re.findall(r"\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b", text)
            dep_time = times[0] if len(times) > 0 else None
            arr_time = times[1] if len(times) > 1 else None

            # Non-stop vs stops
            is_nonstop = "Nonstop" in text or "non-stop" in text.lower() or "direct" in text.lower()

            if price:
                extracted_flights.append({
                    "airline": airline,
                    "price_inr": price,
                    "departure_time": dep_time,
                    "arrival_time": arr_time,
                    "non_stop": is_nonstop,
                    "raw_text_snippet": " | ".join(lines[:4])
                })

        print(f"Successfully parsed {len(extracted_flights)} real flight options:")
        for idx, fl in enumerate(extracted_flights[:10]):
            print(f"  {idx+1}. [{fl['airline']}] INR {fl['price_inr']:,} | Dep: {fl['departure_time']} -> Arr: {fl['arrival_time']} | Non-stop: {fl['non_stop']}")

        browser.close()
        return extracted_flights

if __name__ == "__main__":
    test_google_flights_deep_scrape()
