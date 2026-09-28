import numpy as np
from typing import List, Dict, Any, Tuple

def hampel_filter(values: List[float], threshold: float = 3.5) -> Tuple[List[bool], float, float]:
    """
    Hampel Identifier (Median Absolute Deviation based robust outlier filter).
    Specification: Chapter 4.3 of APIx Technical Build Specification.
    
    Formula:
      MAD = median(|x_i - median(x)|)
      Flag x_i as outlier if |x_i - median(x)| / (1.4826 * MAD) > threshold (3.5)
      
    Returns:
      (is_outlier_list, median_val, mad_val)
    """
    if len(values) < 3:
        return [False] * len(values), float(np.mean(values) if values else 0.0), 0.0

    arr = np.array(values, dtype=float)
    med = float(np.median(arr))
    abs_dev = np.abs(arr - med)
    mad = float(np.median(abs_dev))

    # Guard against zero MAD (e.g. all values identical)
    scale = 1.4826 * mad
    if scale == 0.0:
        return [False] * len(values), med, mad

    z_scores = abs_dev / scale
    is_outlier = (z_scores > threshold).tolist()
    return is_outlier, med, mad

def clean_flight_observations(observations: List[Dict[str, Any]], price_key: str = "base_fare") -> List[Dict[str, Any]]:
    """
    Filters outliers out of a list of raw observations using Hampel identifier.
    Logs flagged records and returns cleaned list.
    """
    if not observations:
        return []

    fares = [float(o.get(price_key, 0.0)) for o in observations]
    outlier_flags, med, mad = hampel_filter(fares)

    clean_records = []
    for obs, is_out in zip(observations, outlier_flags):
        if not is_out:
            clean_records.append(obs)
        else:
            # Mark or omit outlier
            obs["is_outlier"] = True

    return clean_records
