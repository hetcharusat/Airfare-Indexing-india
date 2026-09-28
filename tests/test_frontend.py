import sys
from playwright.sync_api import sync_playwright

def test_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://127.0.0.1:8000/', timeout=15000)
        page.wait_for_timeout(2000)
        print("Page Title:", page.title())
        
        # Test KPIs
        kpi_lasp = page.locator("#kpi-laspeyres").inner_text()
        kpi_naive = page.locator("#kpi-naive").inner_text()
        peak_bias = page.locator("#kpi-peak-bias").inner_text()
        print(f"KPIs -> Laspeyres: {kpi_lasp} | Naive: {kpi_naive} | Peak Bias: {peak_bias}")
        assert float(kpi_lasp) > 0, "Laspeyres KPI invalid"
        
        # Test Chart A SVGs
        chart_a_svgs = page.locator("#chart-divergence-div svg").count()
        print("Chart A SVGs:", chart_a_svgs)
        assert chart_a_svgs > 0, "Chart A not rendered"
        
        # Switch to Tab 2: Kitagawa Decomposition
        page.click("button[data-tab='tab-decomposition']")
        page.wait_for_timeout(1500)
        chart_b_svgs = page.locator("#chart-waterfall-div svg").count()
        decomp_delta = page.locator("#decomp-total-delta").inner_text()
        print(f"Chart B SVGs: {chart_b_svgs} | Decomp Delta: {decomp_delta}")
        assert chart_b_svgs > 0, "Chart B Waterfall not rendered"
        
        # Switch to Tab 3: Escalation Curves
        page.click("button[data-tab='tab-curves']")
        page.wait_for_timeout(1500)
        chart_c_svgs = page.locator("#chart-curves-div svg").count()
        print("Chart C Escalation Curves SVGs:", chart_c_svgs)
        assert chart_c_svgs > 0, "Chart C Curves not rendered"

        # Switch to Tab 4: DGCA Table
        page.click("button[data-tab='tab-dgca']")
        page.wait_for_timeout(1000)
        dgca_rows = page.locator("#dgca-table-body tr").count()
        print("DGCA Reference Rows Rendered:", dgca_rows)
        assert dgca_rows > 0, "DGCA table empty"

        print("FRONTEND PLAYWRIGHT TESTS PASSED 100%!")
        browser.close()

if __name__ == "__main__":
    test_frontend()
