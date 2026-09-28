# INDAIR / APIx: Econometrically Rigorous Airfare Indexing System
## Master Technical & Econometric Dossier for Smart India Hackathon (SIH 2025)

> **Live System:** [https://airfare.atmyhome.tech](https://airfare.atmyhome.tech)  
> **Interactive API Docs:** [https://airfare.atmyhome.tech/docs](https://airfare.atmyhome.tech/docs)  
> **Source Repository:** [https://github.com/hetcharusat/Airfare-Indexing-india](https://github.com/hetcharusat/Airfare-Indexing-india)  
> **Problem Statement ID:** SIH26056 (MoSPI / DGCA - Domestic Aviation Price Index)

---

## PART 1: MASTER CHATGPT / AI PROMPT (Copy-Paste Ready)

Copy and paste the prompt below into ChatGPT, Claude, or Midjourney to generate presentation visuals, infographics, and slide scripts:

```text
You are an expert Chief Economist and Presentation Designer specialized in Civil Aviation Price Statistics and Econometrics.
I need to create a visual, high-scoring 6-slide Smart India Hackathon (SIH 2025) PPT submission based on the official template. 

CRITICAL REQUIREMENT:
Judges hate text-heavy slides. Do NOT give me bullet-point heavy paragraphs. Instead, for each slide give me:
1. Exact Slide Heading & Sub-headings (matching SIH template).
2. The Visual Layout Concept (Infographic / Architecture / Flowchart / Comparison Matrix).
3. The exact Text Prompts to generate custom diagram images (for DALL-E 3 / Midjourney / Mermaid.js).
4. Short, punchy callout labels (max 4-5 words per node).
5. The 30-second Judge Pitch Script emphasizing ECONOMETRICS, MATHEMATICAL ACCURACY, and our AUTONOMOUS AI SUPERVISOR.

PROJECT CONTEXT:
- Problem: MoSPI currently has no high-frequency domestic airfare index; simple average scraping creates massive bias (yield management booking curves, seat scarcity spikes, airline substitution).
- Solution: INDAIR / APIx — An econometric pipeline calculating chained Fisher Ideal and Jevons indices stratified by Advance Purchase Windows (APW), reconciled with monthly DGCA passenger traffic weights, and monitored 24/7 by an Autonomous AI Supervisor that audits data fidelity, detects volatility anomalies, and guarantees mathematical accuracy.
- Equations used: Jevons Geometric Mean, Laspeyres, Paasche, Fisher Ideal Superlative Index, Bortkiewicz Covariance Decomposition, and 5-Day Block Bootstrap.
- Live Public Deployment: https://airfare.atmyhome.tech with FastAPI, React 19 Cockpit, and automated Playwright/GDS ingestion.

Generate the visual slide breakdown following this context.
```

---

## PART 2: CORE ECONOMETRIC FORMULAS & MATHEMATICAL SPECIFICATIONS

### 1. The Fundamental Problem: Why Naive Scraping Fails Economically
Simple arithmetic averaging of scraped prices ($\frac{1}{n} \sum p_i$) violates three core axioms of consumer price theory:
1. **Dynamic Yield Curve Bias:** A ticket bought at $T+1$ (1 day before departure) costs 3× a ticket at $T+30$. A naive average that samples more last-minute tickets indicates artificial inflation when actual fares may be falling.
2. **Carli Upward Bias (Axiom Failure):** The arithmetic mean of price relatives $\frac{1}{n} \sum \frac{p_i^t}{p_i^0}$ fails the **Time Reversal Test** ($I_{0,t} \times I_{t,0} \neq 1$) and steadily drifts upward.
3. **Consumer Substitution Bias:** Fixed baskets assume consumers keep buying high-priced airlines regardless of price spikes. In reality, passengers substitute toward lower-cost carriers (IndiGo, Akasa).

---

### 2. Equation 1: Elementary Aggregation via Jevons Geometric Mean
At the lowest level (individual flight microdata within a specific Route $\times$ Lead-Time bucket), we aggregate prices using the **Jevons Index**:

$$P_{J}(p^0, p^t) = \prod_{i=1}^{n} \left( \frac{p_{i,t}}{p_{i,0}} \right)^{\frac{1}{n}} = \frac{\exp\left( \frac{1}{n} \sum_{i=1}^{n} \ln p_{i,t} \right)}{\exp\left( \frac{1}{n} \sum_{i=1}^{n} \ln p_{i,0} \right)}$$

* **Why Jevons?**
  * Satisfies the **Time Reversal Test** and **Transitivity Test**.
  * Unit-independent and immune to extreme luxury outlier spikes.
  * In our code: `np.exp(np.log(cell_data["base_fare"]).mean())`.

---

### 3. Equation 2 & 3: Laspeyres and Paasche Price Indices
At the composite route and macro level, we evaluate upper and lower economic bounds:

#### **Laspeyres Price Index (Base-Period Fixed Weights):**
$$I_{L}^{0 \to t} = \frac{\sum_{i=1}^{K} p_{i,t} \, q_{i,0}}{\sum_{i=1}^{K} p_{i,0} \, q_{i,0}} \times 100 = \sum_{i=1}^{K} w_{i,0} \left( \frac{p_{i,t}}{p_{i,0}} \right) \times 100$$
* *Economic Property:* Overstates inflation because it ignores consumer substitution away from expensive carriers.

#### **Paasche Price Index (Current-Period Dynamic Weights):**
$$I_{P}^{0 \to t} = \frac{\sum_{i=1}^{K} p_{i,t} \, q_{i,t}}{\sum_{i=1}^{K} p_{i,0} \, q_{i,t}} \times 100 = \left[ \sum_{i=1}^{K} w_{i,t} \left( \frac{p_{i,0}}{p_{i,t}} \right) \right]^{-1} \times 100$$
* *Economic Property:* Understates inflation because it overweights goods whose quantities increased as prices fell.

---

### 4. Equation 4: The Fisher Ideal Superlative Price Index
To capture true economic inflation, INDAIR synthesizes Laspeyres and Paasche into the **Fisher Ideal Index**:

$$I_{F}^{0 \to t} = \sqrt{I_{L}^{0 \to t} \times I_{P}^{0 \to t}}$$

* **Axiomatic Proofs Satisfied:**
  * **Time-Reversal:** $I_F(p^0, p^t, q^0, q^t) \times I_F(p^t, p^0, q^t, q^0) = 1$
  * **Factor-Reversal:** Price index $\times$ Quantity index = Total Expenditure ratio.
  * **Exact & Superlative:** Diewert (1976) proved Fisher is exact for a flexible quadratic utility aggregator function.

---

### 5. Equation 5: Ladislaus von Bortkiewicz Covariance Decomposition
To statistically audit the divergence between Laspeyres and Paasche and detect dynamic substitution in air travel, we compute the Bortkiewicz decomposition:

$$\frac{I_L}{I_P} = 1 + \frac{\text{Cov}_{w_0}(r_p, r_q)}{\bar{r}_p \cdot \bar{r}_q}$$

Where:
* $r_{p,i} = \frac{p_{i,t}}{p_{i,0}}$ is the Price Relative.
* $r_{q,i} = \frac{q_{i,t}}{q_{i,0}}$ is the Quantity Relative.
* $\bar{r}_p = \sum w_{i,0} r_{p,i}$ and $\bar{r}_q = \sum w_{i,0} r_{q,i}$.
* **Economic Audit Criterion:**
  * In normal rational markets, price elasticity is negative ($\text{Cov}(r_p, r_q) < 0$), meaning $I_L > I_P$.
  * If $\text{Cov}(r_p, r_q) > 0$, the AI Supervisor detects abnormal panic-buying or speculative ticket hoarding (common in festive emergencies).

---

### 6. Equation 6: 5-Day Block Bootstrap 95% Confidence Intervals
Airfare time-series exhibit strong temporal autocorrelation (today's fare correlates with yesterday's). Independent random sampling fails. We implement a **5-Day Stationary Block Bootstrap**:

$$\widehat{\text{SE}}(I_F) = \sqrt{\frac{1}{B-1} \sum_{b=1}^{B} \left( I_{F}^{*(b)} - \bar{I}_F^* \right)^2}, \quad B=200$$
$$\text{CI}_{95\%} = \left[ I_F - 1.96 \cdot \widehat{\text{SE}}(I_F), \; I_F + 1.96 \cdot \widehat{\text{SE}}(I_F) \right]$$

---

### 7. Equation 7: Advance Purchase Window (APW) Stratification Matrix
Total composite cell weight $w_i^0$ is decomposed into:

$$w_{(r, lt)}^0 = w_{\text{route}}^{\text{DGCA}} \times w_{\text{lead-time}}$$

| Lead Time Bucket ($lt$) | Horizon | DGCA Route Weight ($w_r$) | Lead Weight ($w_{lt}$) |
| :--- | :--- | :--- | :--- |
| **T+1** | 0 to 3 days (Urgent/Emergency) | DEL-BOM (0.22) | 0.15 |
| **T+7** | 4 to 7 days (Business/Short-plan) | BOM-DEL (0.20) | 0.25 |
| **T+15** | 8 to 14 days (Standard Leisure) | DEL-BLR (0.16) | 0.30 |
| **T+30** | 15 to 30 days (Planned Leisure) | BOM-BLR (0.12) | 0.20 |
| **T+45** | 31+ days (Early Bird) | Regional/UDAN (0.20) | 0.10 |

---

### 8. Equation 8: DGCA 4-Step Bridge Series Reconciliation
To reconcile high-frequency daily scraped fares ($F_t^{\text{daily}}$) with official monthly DGCA traffic figures ($M_m^{\text{DGCA}}$):

1. **Step 1 (Monthly Average):** $\bar{F}_m = \frac{1}{D_m} \sum_{t \in m} F_t^{\text{daily}}$
2. **Step 2 (Discrepancy Ratio):** $R_m = \frac{M_m^{\text{DGCA}}}{\bar{F}_m}$
3. **Step 3 (Spline Interpolation):** Smooth monthly ratios into daily calibration factors $r_t$ using cubic spline interpolation to avoid cliff-edge jumps at month boundaries.
4. **Step 4 (Bridged Daily Index):** $F_t^{\text{Bridged}} = F_t^{\text{daily}} \times r_t$

---

## PART 3: THE AUTONOMOUS AI SUPERVISOR ARCHITECTURE

The core differentiator of this system is that it does not merely run a scraper; it features an **Autonomous Ingestion & Statistical Supervisor Daemon** that ensures continuous index validity:

```
               ┌────────────────────────────────────────────────────────┐
               │         AUTONOMOUS AI SUPERVISOR (24/7 DAEMON)         │
               └──────────────────────────┬─────────────────────────────┘
                                          │
    ┌─────────────────────────────────────┼─────────────────────────────────────┐
    ▼                                     ▼                                     ▼
[ 1. Ingestion Goal Engine ]   [ 2. Anti-Bias Auditor ]              [ 3. Statistical Anomaly Judge ]
• Paces 420 obs/hr             • Detects Carrier Starvation          • Z-score test on price relatives (σ > 3.5)
• Calibrated to 24hr diurnal    • Prevents single-airline bias       • Carli-Jevons spread monitoring
  flight search traffic        • Triggers targeted probes            • Kurtosis & heavy-tail audit
    │                                     │                                     │
    └─────────────────────────────────────┼─────────────────────────────────────┘
                                          │
                                          ▼
                       [ 4. Automated Decision & Action ]
                       ├── Passed: Clears microdata for Index Compilation
                       ├── Quarantined: Filters luxury business-class / bot anomalies
                       ├── Auto-Calibrated: Reweights starved carriers
                       └── Freeze Policy: Locks weights to prevent overfitting drift
```

### Self-Monitoring Capabilities Built-in:
1. **Carrier Parity Audit:** If IndiGo or Air India microdata drops below 25% of expected route volume due to website blocking, the supervisor flags an `ANTI_NARROWING_ALERT` and switches to the GDS backup API.
2. **Indian Cultural Calendar Engine:** Tracks 30-day forward horizons for festivals (Diwali, Chhath, Durga Puja, Eid, Onam) and boosts sampling density on affected corridors (e.g., DEL-PAT, BOM-CCU).
3. **Overfit Prevention Switch:** Learns route seasonality weights, then freezes policy to prevent dynamic drift from overfitting short-term demand anomalies.

---

## PART 4: SLIDE-BY-SLIDE VISUAL BLUEPRINT FOR PPT

### **SLIDE 1: Title & System Identity**
* **Visual:** High-tech split graphic: On the left, Indian aviation flight route map; on the right, glassmorphic terminal showing live ticker: `INDAIR INDEX: 114.28 (+1.42%) | DGCA RECONCILED`.
* **Badges:** `Live Production Server: airfare.atmyhome.tech` | `Open API /docs` | `Docker Architecture`.

### **SLIDE 2: Problem & Proposed Solution**
* **Visual Infographic:** **"The Naive Scraper Fallacy vs. INDAIR Econometric Precision"**
  * *Left Side (Old Way - Red X):* Web scraper → Simple Average → Distorted by $T+1$ surge prices & single luxury seats → Massive upward inflation bias.
  * *Right Side (INDAIR Way - Green Check):* Stratified APW Buckets → Jevons Elementary Aggregator → Chained Fisher Ideal Index → Reconciled with DGCA weights → True Macroeconomic Inflation.

### **SLIDE 3: Technical & Mathematical Architecture**
* **Visual Diagram:** End-to-end multi-tier architectural blueprint:
  * Ingestion Tier (Playwright + GDS APIs) → Processing Tier (APW Stratification) → Superlative Math Core (Fisher, Jevons, Bortkiewicz) → Autonomous AI Supervisor (Audits & Flags) → Delivery Tier (FastAPI, React Cockpit).

### **SLIDE 4: Feasibility, Viability & Anomaly Quarantine**
* **Visual Graphic:** **"Autonomous Accuracy Guarantee Flow"**
  * Flowchart showing incoming price ratio:
    * Condition $\Delta P \le 3.5\sigma$ → Accepted into Fisher calculation.
    * Condition $\Delta P > 3.5\sigma$ → Evaluated against multi-airline corridor cross-check → If single-carrier spike: Quarantined as yield-management anomaly; If multi-carrier: Flagged as genuine market supply shock.

### **SLIDE 5: Macro Impact & Regulatory Benefits**
* **Visual Matrix:** 3-Column Stakeholder Value Grid:
  * **MoSPI:** Real-time CPI Transport component without 30-day survey lag.
  * **DGCA / MoCA:** Early-warning surge radar for emergency corridors (festivals, weather disruptions).
  * **Competition Commission (CCI):** Algorithmic pricing audit trail detecting cartelization or predatory pricing.

### **SLIDE 6: References, Standards & Working Artifacts**
* **Visual:** Logos and citations of IMF CPI Manual (2020), UN System of National Accounts (SNA), DGCA Monthly Circulars, and live QR code / interactive screenshot of `https://airfare.atmyhome.tech`.
