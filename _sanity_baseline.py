"""
重構 query_engine.py 之前先抓一份基準輸出，重構後比對用。
跑完會產生 _sanity_baseline.pkl。重構驗證完即可刪。
"""
import pickle
from query_engine import zone1_analysis, zone1_dual_combined, zone2_analysis, ROLLING

CASES = {
    "z1_single":    lambda: zone1_analysis([5], ROLLING, lag=1),
    "z1_multi":     lambda: zone1_analysis([3, 12, 23, 31], ROLLING, lag=1),
    "z1_lag2":      lambda: zone1_analysis([7, 18], ROLLING, lag=2),
    "z1_dual":      lambda: zone1_dual_combined([5, 12, 23], [8, 19, 30], ROLLING, w1=0.6, w2=0.4),
    "z2_single":    lambda: zone2_analysis(3, ROLLING),
    "z2_seven":     lambda: zone2_analysis(7, ROLLING),
}

baseline = {name: fn() for name, fn in CASES.items()}
with open("_sanity_baseline.pkl", "wb") as f:
    pickle.dump(baseline, f)

print("Baseline saved:")
for name, val in baseline.items():
    df = val[0] if isinstance(val, tuple) else val
    print(f"  {name}: shape={df.shape}, top號碼={df['號碼'].head(3).tolist()}")
