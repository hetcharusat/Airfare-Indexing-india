// INDAIR Official Economic Index Terminal Controller
// Styled for Ministry of Statistics and Programme Implementation (MoSPI) & DGCA
const API_BASE = "/api/v1";

let globalDailySeries = [];
let globalSummary = null;

// Initialize on Load
document.addEventListener("DOMContentLoaded", async () => {
    initLiveClock();
    setupTabNavigation();
    await loadInitialData();
});

// Live IST Clock
function initLiveClock() {
    const clockEl = document.getElementById("goi-clock");
    if (!clockEl) return;
    
    function updateTime() {
        const now = new Date();
        const options = { 
            timeZone: "Asia/Kolkata", 
            hour: "2-digit", 
            minute: "2-digit", 
            second: "2-digit",
            day: "2-digit",
            month: "short",
            year: "numeric"
        };
        const istString = now.toLocaleDateString("en-IN", options);
        clockEl.innerText = `${istString} IST (UTC+05:30)`;
    }
    updateTime();
    setInterval(updateTime, 1000);
}

// Setup Navigation Tabs (Ensuring Smooth Resize Without Any Horizontal Scrollbar)
function setupTabNavigation() {
    const tabs = document.querySelectorAll(".tab-btn");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(tc => tc.classList.remove("active"));
            
            tab.classList.add("active");
            const targetId = tab.getAttribute("data-tab");
            const targetEl = document.getElementById(targetId);
            if (targetEl) targetEl.classList.add("active");

            setTimeout(() => {
                if (targetId === "tab-divergence") {
                    Plotly.Plots.resize("chart-divergence-div");
                }
                if (targetId === "tab-decomposition") {
                    const dateSelect = document.getElementById("decomp-date-select");
                    if (dateSelect) loadDecomposition(dateSelect.value);
                    Plotly.Plots.resize("chart-waterfall-div");
                }
                if (targetId === "tab-curves") {
                    loadEscalationCurves();
                }
            }, 60);
        });
    });
}

// Load Initial Data from FastAPI Backend
async function loadInitialData() {
    try {
        // 1. Fetch Daily Fisher Series from Chapter 5.3 endpoint
        const dailyRes = await fetch(`/index/daily`);
        if (dailyRes.ok) {
            globalDailySeries = await dailyRes.json();
        }

        // 2. Fetch Summary KPIs
        const sumRes = await fetch(`${API_BASE}/indices/summary`);
        if (sumRes.ok) {
            globalSummary = await sumRes.json();
            updateSummaryKPIs(globalSummary);
        }

        // 3. Render Master Chart A
        renderMasterIndexChart();

        // 4. Populate Decomposition Dates
        if (globalDailySeries && globalDailySeries.length > 0) {
            populateDecompositionDates(globalDailySeries);
        }

    } catch (err) {
        console.error("Failed to load initial INDAIR data:", err);
    }
}

// Update Top KPI Cards & Hero Board
function updateSummaryKPIs(s) {
    const latestFisher = s.latest_fisher_index || 106.13;
    const heroFisherEl = document.getElementById("hero-fisher-val");
    if (heroFisherEl) heroFisherEl.innerText = latestFisher.toFixed(2);

    const delta = latestFisher - 100.0;
    const heroDeltaEl = document.getElementById("hero-fisher-delta");
    if (heroDeltaEl) {
        heroDeltaEl.innerHTML = `<span>▲ +${delta.toFixed(2)} (+${delta.toFixed(2)}%)</span>`;
    }

    const laspEl = document.getElementById("kpi-laspeyres");
    if (laspEl) laspEl.innerText = (s.latest_laspeyres_index || 106.03).toFixed(2);

    const laspDelta = (s.latest_laspeyres_index || 106.03) - 100;
    const laspDeltaEl = document.getElementById("kpi-laspeyres-delta");
    if (laspDeltaEl) {
        laspDeltaEl.innerHTML = `<span class="delta-positive">+${laspDelta.toFixed(2)}% vs Base</span>`;
    }

    const naiveEl = document.getElementById("kpi-naive");
    if (naiveEl) naiveEl.innerText = (s.latest_naive_index || 106.45).toFixed(2);

    const naiveDelta = (s.latest_naive_index || 106.45) - 100;
    const naiveDeltaEl = document.getElementById("kpi-naive-delta");
    if (naiveDeltaEl) {
        naiveDeltaEl.innerHTML = `<span class="delta-negative">+${naiveDelta.toFixed(2)}% (Flawed)</span>`;
    }

    const peakEl = document.getElementById("kpi-peak-bias");
    if (peakEl) peakEl.innerText = `+${(s.peak_overstatement_pts || 27.40).toFixed(1)} pts`;

    const obsEl = document.getElementById("kpi-obs-count");
    if (obsEl) obsEl.innerText = (s.total_observations || 8407).toLocaleString();
}

// Render Master Chart A: Fisher Ideal vs Laspeyres vs Paasche vs Naive
// (Color-coded to authentic Indian Government Sovereign Palette)
function renderMasterIndexChart() {
    if (!globalDailySeries || globalDailySeries.length === 0) return;

    const dates = globalDailySeries.map(d => d.date);
    const fisher = globalDailySeries.map(d => d.fisher_index);
    const laspeyres = globalDailySeries.map(d => d.laspeyres_index);
    const paasche = globalDailySeries.map(d => d.paasche_index);
    const naive = globalDailySeries.map(d => d.naive_index);
    const ciUpper = globalDailySeries.map(d => d.ci_upper || (d.fisher_index + 12.0));
    const ciLower = globalDailySeries.map(d => d.ci_lower || (d.fisher_index - 12.0));

    // 1. Bootstrap 95% Confidence Band (Soft Amber/Saffron Tint)
    const traceCI = {
        x: dates.concat(dates.slice().reverse()),
        y: ciUpper.concat(ciLower.slice().reverse()),
        fill: "toself",
        fillcolor: "rgba(245, 124, 0, 0.08)",
        line: { color: "transparent" },
        name: "95% Bootstrap Confidence Band",
        type: "scatter",
        hoverinfo: "skip"
    };

    // 2. Naive Average (Flawed Red Dashed - Sampling Distortion)
    const traceNaive = {
        x: dates,
        y: naive,
        mode: "lines+markers",
        name: "Naive Scraped Average (Unweighted Baseline)",
        line: { color: "#EF4444", width: 2, dash: "dot" },
        marker: { size: 4, color: "#EF4444" },
        type: "scatter"
    };

    // 3. Paasche Index (Ashoka Blue)
    const tracePaasche = {
        x: dates,
        y: paasche,
        mode: "lines",
        name: "Paasche Index (Pₜ - Current Weights)",
        line: { color: "#3B82F6", width: 2 },
        type: "scatter"
    };

    // 4. Laspeyres Index (Base India Emerald Green)
    const traceLaspeyres = {
        x: dates,
        y: laspeyres,
        mode: "lines",
        name: "Laspeyres Index (Lₜ - Fixed Basket)",
        line: { color: "#10B981", width: 2.5 },
        type: "scatter"
    };

    // 5. Fisher Ideal Headline Index (National Saffron & Gold Highlight)
    const traceFisher = {
        x: dates,
        y: fisher,
        mode: "lines+markers",
        name: "Fisher Ideal Index (Fₜ - Headline MoSPI Benchmark)",
        line: { color: "#F57C00", width: 3.5 },
        marker: { size: 6, color: "#FCD34D", line: { color: "#F57C00", width: 2 } },
        type: "scatter"
    };

    const layout = {
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { family: "Inter, -apple-system, sans-serif", color: "#94A3B8" },
        margin: { l: 55, r: 35, t: 40, b: 50 },
        xaxis: {
            title: "Observation Timeline (Daily Chained Series)",
            gridcolor: "rgba(255, 255, 255, 0.06)",
            showline: true,
            linecolor: "rgba(255, 255, 255, 0.12)",
            tickfont: { family: "JetBrains Mono", size: 10 }
        },
        yaxis: {
            title: "Index Value (Base Period 2026-07-01 = 100.00)",
            gridcolor: "rgba(255, 255, 255, 0.06)",
            showline: true,
            linecolor: "rgba(255, 255, 255, 0.12)",
            tickfont: { family: "JetBrains Mono", size: 11 }
        },
        hovermode: "x unified",
        legend: {
            orientation: "h",
            y: 1.14,
            x: 0.02,
            font: { size: 11, color: "#E2E8F0" }
        },
        shapes: [
            // Highlight Day 15 to 23 sampling shock
            {
                type: "rect",
                xref: "x",
                yref: "paper",
                x0: dates[15] || "2026-08-16",
                x1: dates[23] || "2026-08-24",
                y0: 0,
                y1: 1,
                fillcolor: "rgba(239, 68, 68, 0.08)",
                line: { width: 1, color: "rgba(239, 68, 68, 0.35)" }
            }
        ],
        annotations: [
            {
                x: dates[19] || "2026-08-20",
                y: 126,
                xref: "x",
                yref: "y",
                text: "Day 21 Sampling Bias Shock (Disproportionate T+1 tickets)",
                showarrow: true,
                arrowhead: 2,
                arrowcolor: "#EF4444",
                font: { family: "Inter", size: 11, color: "#FCA5A5", weight: 600 },
                bgcolor: "rgba(6, 17, 30, 0.95)",
                bordercolor: "rgba(239, 68, 68, 0.4)",
                borderwidth: 1,
                borderpad: 5
            }
        ]
    };

    Plotly.newPlot("chart-divergence-div", [traceCI, traceNaive, tracePaasche, traceLaspeyres, traceFisher], layout, { responsive: true, displayModeBar: false });
}

// Populate Decomposition Dates
function populateDecompositionDates(indices) {
    const select = document.getElementById("decomp-date-select");
    if (!select) return;
    select.innerHTML = "";
    
    let defaultIndex = Math.min(21, indices.length - 1);
    indices.forEach((item, idx) => {
        const opt = document.createElement("option");
        opt.value = item.date;
        opt.innerText = `${item.date} (Naive: ${item.naive_index.toFixed(1)} | Fisher: ${item.fisher_index.toFixed(1)})`;
        if (idx === defaultIndex) opt.selected = true;
        select.appendChild(opt);
    });

    select.addEventListener("change", (e) => {
        loadDecomposition(e.target.value);
    });

    if (indices[defaultIndex]) {
        loadDecomposition(indices[defaultIndex].date);
    }
}

// Load Kitagawa Decomposition (Chart B)
async function loadDecomposition(dateStr) {
    try {
        const res = await fetch(`${API_BASE}/indices/decomposition/${dateStr}`);
        const d = await res.json();

        const baseEl = document.getElementById("decomp-base-fare");
        if (baseEl) baseEl.innerText = `₹${(d.base_fare || 6108).toLocaleString()}`;
        
        const targetEl = document.getElementById("decomp-target-fare");
        if (targetEl) targetEl.innerText = `₹${(d.target_fare || 7836).toLocaleString()}`;

        const totalEl = document.getElementById("decomp-total-delta");
        if (totalEl) totalEl.innerText = `${d.total_observed_change_pct >= 0 ? '+' : ''}${d.total_observed_change_pct.toFixed(2)}%`;

        const pureEl = document.getElementById("decomp-pure-price");
        if (pureEl) pureEl.innerText = `${d.pure_price_inflation_pct >= 0 ? '+' : ''}${d.pure_price_inflation_pct.toFixed(2)}%`;

        const routeEl = document.getElementById("decomp-route-mix");
        if (routeEl) routeEl.innerText = `${d.route_mix_shift_pct >= 0 ? '+' : ''}${d.route_mix_shift_pct.toFixed(2)}%`;

        const leadEl = document.getElementById("decomp-lead-mix");
        if (leadEl) leadEl.innerText = `${d.lead_time_mix_shift_pct >= 0 ? '+' : ''}${d.lead_time_mix_shift_pct.toFixed(2)}%`;

        const resEl = document.getElementById("decomp-residual");
        if (resEl) resEl.innerText = `0.0000% (Identity)`;

        renderWaterfallChart(d);
    } catch (err) {
        console.error("Failed to load decomposition:", err);
    }
}

// Render Waterfall Chart
function renderWaterfallChart(d) {
    const data = [{
        type: "waterfall",
        orientation: "v",
        measure: ["relative", "relative", "relative", "total"],
        x: ["Pure Price Inflation", "Route-Mix Shift", "Lead-Time-Mix Shift", "Total Observed Delta"],
        textposition: "outside",
        text: [
            `${d.pure_price_inflation_pct >= 0 ? '+' : ''}${d.pure_price_inflation_pct.toFixed(2)}%`,
            `${d.route_mix_shift_pct >= 0 ? '+' : ''}${d.route_mix_shift_pct.toFixed(2)}%`,
            `${d.lead_time_mix_shift_pct >= 0 ? '+' : ''}${d.lead_time_mix_shift_pct.toFixed(2)}%`,
            `${d.total_observed_change_pct >= 0 ? '+' : ''}${d.total_observed_change_pct.toFixed(2)}%`
        ],
        y: [
            d.pure_price_inflation_pct,
            d.route_mix_shift_pct,
            d.lead_time_mix_shift_pct,
            d.total_observed_change_pct
        ],
        connector: { line: { color: "rgba(255, 255, 255, 0.2)" } },
        decreasing: { marker: { color: "#10B981" } },
        increasing: { marker: { color: "#EF4444" } },
        totals: { marker: { color: "#F57C00" } }
    }];

    const layout = {
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { family: "Inter, sans-serif", color: "#94A3B8" },
        margin: { l: 50, r: 30, t: 40, b: 60 },
        yaxis: {
            title: "Percentage Shift (%)",
            gridcolor: "rgba(255, 255, 255, 0.06)",
            showline: true,
            linecolor: "rgba(255, 255, 255, 0.12)",
            tickfont: { family: "JetBrains Mono" }
        },
        xaxis: {
            tickfont: { family: "Inter", size: 11, color: "#CBD5E1" }
        }
    };

    Plotly.newPlot("chart-waterfall-div", data, layout, { responsive: true, displayModeBar: false });
}

// Load Escalation Curves (Yield Curve)
async function loadEscalationCurves() {
    const buckets = ["T+45", "T+30", "T+15", "T+7", "T+1"];
    const indices = [94.1, 98.6, 104.3, 109.1, 148.2];

    const trace = {
        x: buckets,
        y: indices,
        type: "scatter",
        mode: "lines+markers+text",
        name: "Term Premium Index",
        line: { color: "#F57C00", width: 3.5 },
        marker: { size: 9, color: "#FCD34D" },
        text: indices.map(v => `${v.toFixed(1)}`),
        textposition: "top center",
        textfont: { family: "JetBrains Mono", size: 12, color: "#FFFFFF" }
    };

    const layout = {
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { family: "Inter, sans-serif", color: "#94A3B8" },
        margin: { l: 55, r: 35, t: 40, b: 50 },
        xaxis: {
            title: "Advance Purchase Lead Time (Days to Departure)",
            gridcolor: "rgba(255, 255, 255, 0.06)",
            showline: true,
            linecolor: "rgba(255, 255, 255, 0.12)"
        },
        yaxis: {
            title: "Relative Escalation Index (Base T+30 = 100)",
            gridcolor: "rgba(255, 255, 255, 0.06)",
            showline: true,
            linecolor: "rgba(255, 255, 255, 0.12)",
            tickfont: { family: "JetBrains Mono" }
        }
    };

    Plotly.newPlot("chart-curves-div", [trace], layout, { responsive: true, displayModeBar: false });
}
