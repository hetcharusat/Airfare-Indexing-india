# Project APIx: Airfare Price Index for India
### A Composition-Corrected Alternative to Naive Fare Averaging for Augmentation of the Consumer Price Index (CPI)
**Smart India Hackathon 2026** | **Problem Statement:** SIH26056  
**Ministry / Authority:** Ministry of Statistics and Programme Implementation (MoSPI) / Directorate General of Civil Aviation (DGCA)

---

## 🎯 The Core Philosophy
> *"Every naive average confuses two questions: what did prices do, and what did we happen to look at. This project is about never confusing those two questions again."*

Out of competing teams on this problem, most build a naive pipeline:
$$\text{Scrape raw prices} \longrightarrow \text{Compute arithmetic average} \longrightarrow \text{Display on dashboard}$$

**The Fatal Flaw:** A naive average conflates **real price inflation** with **composition/mix shifts** (e.g., scraping more last-minute $T+1$ tickets or longer routes on a given week).

APIx implements a **fixed-basket, lead-time stratified Laspeyres Price Index** that isolates pure price movements, accompanied by an exact **Kitagawa mathematical decomposition** and **Bootstrap 95% Confidence Intervals**.

---

## 🏗️ System Architecture

```
d:\AIRFARE-SIH\
├── APIx_System_Requirements_and_Architecture.md  # Master specification document
├── SIH26056_APIx_Strategy_Document.pdf           # Original SIH strategy document
├── data/
│   ├── historical_airfare_panel.csv              # 40-day, 8,200+ flight record panel
│   └── dgca_monthly_reference.csv                # Official DGCA monthly benchmarks
├── src/
│   ├── scraper/
│   │   └── playwright_scraper.py                 # Playwright Chromium headless flight scraper
│   ├── engine/
│   │   └── index_engine.py                       # Laspeyres Index + Kitagawa Decomposition + Bootstrap CI
│   ├── data/
│   │   └── synthetic_backtest_generator.py       # 40-day panel generator with calibrated shocks
│   └── dashboard/
│       └── app.py                                # MoSPI / SIH Interactive Executive Dashboard
└── README.md
```

---

## 🚀 Quickstart & How to Run

### 1. Launch the MoSPI Executive Dashboard
```powershell
streamlit run src/dashboard/app.py
```
Open your browser at `http://localhost:8501` to view:
- **Chart A (The Divergence Chart):** Naive Average vs. Laspeyres Corrected Index with 95% Bootstrap Confidence Band.
- **Chart B (Kitagawa Decomposition):** Interactive waterfall decomposition separating Pure Price Inflation, Route-Mix Shift, and Lead-Time-Mix Shift.
- **Dynamic Pricing Curves:** Advance booking escalation from $T+45$ down to $T+1$.
- **DGCA Benchmark Validation:** Structural reconciliation between retrospective monthly yields and prospective forward-looking indices.
- **Live Playwright Scraper:** On-demand Chromium headless flight query interface.

### 2. Run the Live Playwright Scraper
Test live flight data extraction from Google Flights across Indian metro corridors:
```powershell
python src/scraper/playwright_scraper.py
```

### 3. Run the Index Engine Test & Verification
Execute the econometric calculation suite:
```powershell
python src/engine/index_engine.py
```

---

## 📊 The Two Winning Charts
1. **Chart A (Divergence Chart):** Demonstrates that a naive average overstates fare spikes (e.g. falsely indicating a +27% spike during Day 18), whereas the APIx Laspeyres index holds the basket constant and reveals that true underlying price inflation was only +1.7%.
2. **Chart B (Kitagawa Decomposition Waterfall):** Proves with exact mathematical precision ($0.0\%$ residual) that $+25.8$ percentage points of the $+27.5\%$ spike was an artifact of sampling shifts toward last-minute bookings.

---

## 🏛️ Rehearsed Judge Defense Highlights
- **"Isn't this just a scraper with a dashboard?"**  
  *No. A scraper reports what was observed on a screen. APIx calculates what actually changed economically, holding the observation mix constant. We are an index-construction system extending MoSPI's own Laspeyres CPI methodology to online airfares.*
- **"Why does your index diverge from DGCA monthly published numbers?"**  
  *DGCA publishes retrospective, unstratified average passenger revenues across all tickets sold throughout the month. APIx measures prospective, forward-looking fares stratified across 5 distinct lead times. A T+1 fare and a T+45 fare are different economic goods; pooling them without stratification creates mix bias. Our divergence is the discovery, not an error.*
