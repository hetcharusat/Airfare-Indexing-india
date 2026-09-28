from playwright.sync_api import sync_playwright

def capture_all():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://127.0.0.1:8000/", timeout=15000)
        page.wait_for_timeout(2000)
        
        # 1. Divergence (Chart A)
        page.screenshot(path="backend/app/static/preview_chart_a.png", full_page=True)
        print("Captured Chart A")

        # 2. Decomposition (Chart B)
        page.click("button[data-tab='tab-decomposition']")
        page.wait_for_timeout(1500)
        page.screenshot(path="backend/app/static/preview_chart_b.png", full_page=True)
        print("Captured Chart B")

        # 3. Dynamic Curves
        page.click("button[data-tab='tab-curves']")
        page.wait_for_timeout(1500)
        page.screenshot(path="backend/app/static/preview_curves.png", full_page=True)
        print("Captured Curves")

        # 4. Live Scraper
        page.click("button[data-tab='tab-scraper']")
        page.wait_for_timeout(1000)
        page.screenshot(path="backend/app/static/preview_scraper.png", full_page=True)
        print("Captured Scraper")

        browser.close()

if __name__ == "__main__":
    capture_all()
