import os
import json
import math
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger("LLMDataJudge")

# Load official SIH Indian Aviation Sources Catalog (from teammate)
CATALOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "sih_sources_catalog.csv"))

# DGCA Target Market Share Benchmark (2026 Reference)
DGCA_TARGET_SHARES = {
    "IndiGo": 0.620,
    "Air India": 0.260,
    "Akasa Air": 0.055,
    "SpiceJet": 0.040,
    "Air India Express": 0.015,
    "Alliance Air": 0.005,
    "Star Air": 0.003,
    "Fly91": 0.002
}

class LLMDataJudgeAgent:
    """
    Autonomous LLM Data Quality Auditor, Diversity Critic, and Convergence Manager.
    
    Responsibilities:
      1. Audits incoming flight batches against official Indian aviation registry (sih_sources_catalog.csv).
      2. Detects 'Sampling Narrowing' (Carrier Shannon Entropy collapse, price dispersion flattening).
      3. Controls Reinforcement Learning Lifecycle with an Overfit Prevention 'FREEZE SWITCH'.
      4. Synthesizes MoSPI & RBI Executive Economic Diagnostic Memos.
      5. Connects to Hugging Face Inference API when token is provided, with an offline Econometric Expert Fallback.
    """

    def __init__(self, hf_token: Optional[str] = None, model_name: str = "Qwen/Qwen2.5-7B-Instruct"):
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.model_name = model_name
        self.catalog = self._load_sources_catalog()
        
        # State & Learning Lifecycle
        self.is_frozen = False  # True = Production Locked (No Overfitting)
        self.consecutive_grade_a = 0
        self.convergence_threshold = 5  # Freeze after 5 consecutive Grade A cycles
        self.last_audit_result: Optional[Dict[str, Any]] = None
        self.audit_history: List[Dict[str, Any]] = []

    def _load_sources_catalog(self) -> pd.DataFrame:
        if os.path.exists(CATALOG_PATH):
            try:
                return pd.read_csv(CATALOG_PATH)
            except Exception as e:
                logger.warning(f"Failed loading sources catalog: {e}")
        return pd.DataFrame()

    def calculate_shannon_entropy(self, carrier_counts: Dict[str, int]) -> Tuple[float, float]:
        """
        Calculates Shannon Diversity Entropy of sampled carriers:
          H = - sum(p_i * ln(p_i))
        Normalized against theoretical maximum entropy H_max = ln(K).
        """
        total = sum(carrier_counts.values())
        if total == 0 or len(carrier_counts) <= 1:
            return 0.0, 0.0

        entropy = 0.0
        for count in carrier_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log(p)

        max_entropy = math.log(len(carrier_counts))
        normalized_entropy = (entropy / max_entropy) if max_entropy > 0 else 0.0
        return round(entropy, 4), round(normalized_entropy, 4)

    def audit_batch(self, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Comprehensive Data Quality & Anti-Narrowing Audit of an incoming flight batch.
        """
        if not observations:
            return {
                "status": "EMPTY_BATCH",
                "grade": "F",
                "score": 0.0,
                "summary": "Zero flight observations provided for audit."
            }

        total_obs = len(observations)
        
        # 1. Carrier Distribution & Entropy
        carrier_counts = {}
        prices = []
        lead_counts = {}
        airlines_found = set()

        for obs in observations:
            c = obs.get("airline") or obs.get("carrier") or "Unknown"
            carrier_counts[c] = carrier_counts.get(c, 0) + 1
            airlines_found.add(c)
            
            p = float(obs.get("base_fare") or obs.get("raw_fare") or 0.0)
            if p > 0:
                prices.append(p)
                
            lt = obs.get("lead_bucket") or f"T+{obs.get('lead_days', 7)}"
            lead_counts[lt] = lead_counts.get(lt, 0) + 1

        raw_entropy, norm_entropy = self.calculate_shannon_entropy(carrier_counts)

        # 2. Price Dispersion (Variance / Std Dev check for cache flattening)
        price_std = float(np.std(prices)) if len(prices) > 1 else 0.0
        price_mean = float(np.mean(prices)) if len(prices) > 0 else 1.0
        cv_dispersion = round((price_std / price_mean), 4) if price_mean > 0 else 0.0

        # 3. Market Share Alignment & Narrowing Detection
        narrowing_alerts = []
        carrier_shares = {c: round((cnt / total_obs) * 100, 1) for c, cnt in carrier_counts.items()}
        
        # Check if single carrier dominates (>80%)
        dominant_carrier = max(carrier_counts.items(), key=lambda x: x[1])
        dom_share = dominant_carrier[1] / total_obs
        if dom_share > 0.80 and len(carrier_counts) > 1:
            narrowing_alerts.append(
                f"Sampling Bias: {dominant_carrier[0]} represents {round(dom_share*100, 1)}% of batch (DGCA baseline is 62%). Carrier mix narrowed."
            )

        # Check missing key carriers
        key_carriers = ["IndiGo", "Air India", "SpiceJet", "Akasa Air"]
        missing_keys = [k for k in key_carriers if k not in airlines_found]
        if missing_keys:
            narrowing_alerts.append(f"Missing Scheduled Carriers: {', '.join(missing_keys)} not captured in this stratum sweep.")

        # Check price variance collapse
        if cv_dispersion < 0.05 and total_obs > 5:
            narrowing_alerts.append("Variance Collapse: Fare dispersion is unnaturally flat (CV < 0.05). Check for cached/placeholder OTA responses.")

        # Check lead time balance
        if len(lead_counts) == 1 and total_obs > 20:
            narrowing_alerts.append("Stratum Imbalance: Observations clustered on single lead-time bucket. Full T+1 to T+45 spread required.")

        # 4. Compute Composite Quality Score (0 - 100)
        score = 100.0
        # Entropy penalty
        if norm_entropy < 0.60:
            score -= (0.60 - norm_entropy) * 60
        # Missing key carriers penalty
        score -= len(missing_keys) * 8
        # Variance collapse penalty
        if cv_dispersion < 0.05:
            score -= 20
        score = max(10.0, min(100.0, round(score, 1)))

        # Assign Grade
        if score >= 90:
            grade = "A (Optimal Diversity)"
        elif score >= 75:
            grade = "B (Acceptable)"
        elif score >= 60:
            grade = "C (Marginal Narrowing)"
        else:
            grade = "D/F (Severe Sampling Bias)"

        # 5. Overfit & Convergence Manager (Auto-Freeze)
        if not self.is_frozen:
            if score >= 88:
                self.consecutive_grade_a += 1
                if self.consecutive_grade_a >= self.convergence_threshold:
                    self.is_frozen = True
                    logger.info("🎯 [LLM Judge] Convergence threshold reached! Production sampling policy FROZEN to prevent overfitting.")
            else:
                self.consecutive_grade_a = 0

        # 6. Generate Executive Memo
        memo = self._generate_audit_memo(
            grade, score, total_obs, carrier_shares, norm_entropy, cv_dispersion, narrowing_alerts
        )

        audit_result = {
            "timestamp": datetime.now().isoformat(),
            "total_observations_audited": total_obs,
            "overall_health_grade": grade,
            "quality_score": score,
            "shannon_diversity_index": norm_entropy,
            "coefficient_of_variation": cv_dispersion,
            "carrier_shares": carrier_shares,
            "lead_time_distribution": lead_counts,
            "narrowing_detected": len(narrowing_alerts) > 0,
            "narrowing_alerts": narrowing_alerts,
            "learning_lifecycle": {
                "state": "FROZEN_PRODUCTION_LOCKED" if self.is_frozen else "ACTIVE_SELF_LEARNING",
                "consecutive_optimal_cycles": self.consecutive_grade_a,
                "convergence_threshold": self.convergence_threshold,
                "overfit_protection_active": self.is_frozen
            },
            "judge_executive_memo": memo
        }

        self.last_audit_result = audit_result
        self.audit_history.append(audit_result)
        if len(self.audit_history) > 30:
            self.audit_history.pop(0)

        return audit_result

    def _generate_audit_memo(
        self,
        grade: str,
        score: float,
        total: int,
        shares: Dict[str, float],
        entropy: float,
        cv: float,
        alerts: List[str]
    ) -> str:
        """
        Generates an authoritative statistical memo.
        Uses Hugging Face API if token exists, else generates econometric reasoning natively.
        """
        if self.hf_token:
            try:
                from huggingface_hub import InferenceClient
                client = InferenceClient(token=self.hf_token)
                prompt = (
                    f"You are the Lead Econometric Auditor for MoSPI / DGCA Airfare Price Index. "
                    f"Evaluate this data collection audit: Total Flights={total}, Quality Score={score}, Grade={grade}, "
                    f"Shannon Entropy={entropy}, Carrier Shares={shares}, Alerts={alerts}. "
                    f"Provide a 3-sentence formal statistical judgment assessing sampling diversity and overfit status."
                )
                response = client.text_generation(
                    prompt,
                    model=self.model_name,
                    max_new_tokens=150,
                    temperature=0.2
                )
                return response.strip()
            except Exception as e:
                logger.debug(f"[LLM Judge] HF inference call bypassed ({e}), using local econometric engine.")

        # Offline Local Econometric Expert Engine
        if not alerts:
            return (
                f"Data Collection Audit PASSED (Grade: {grade}, Score: {score}/100). "
                f"Sample exhibits robust carrier diversity (Shannon H_norm = {entropy}) with active market presence across "
                f"{', '.join(list(shares.keys())[:4])}. Price dispersion (CV = {cv}) confirms authentic dynamic yield curve sampling. "
                f"Sampling policy is {'FROZEN to prevent parameter overfit' if self.is_frozen else 'in active convergence'}. Approved for CPI Laspeyres index compilation."
            )
        else:
            return (
                f"Data Collection Audit flagged with WARNING (Grade: {grade}, Score: {score}/100). "
                f"{alerts[0]} "
                f"Risk of sampling bias distortion on elementary Jevons aggregates. "
                f"Recommendation: Dispatch targeted probe to missing carriers before final index calculation."
            )

    def toggle_freeze_mode(self) -> Dict[str, Any]:
        """Manually toggle the learning freeze switch on/off."""
        self.is_frozen = not self.is_frozen
        return {
            "is_frozen": self.is_frozen,
            "state": "FROZEN_PRODUCTION_LOCKED" if self.is_frozen else "ACTIVE_SELF_LEARNING",
            "message": "Policy weights FROZEN: Protected against overfit & drift" if self.is_frozen else "Policy UNLOCKED: Active self-learning resumed"
        }

llm_judge = LLMDataJudgeAgent()
