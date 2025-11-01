import swisseph as swe
from datetime import datetime
import pytz

# ==============================
# בדיקה 1: validation.py
# ==============================
birth_date = datetime(2001, 11, 23, 18, 31)
jd = swe.julday(birth_date.year, birth_date.month, birth_date.day,
                birth_date.hour + birth_date.minute / 60.0)
moon_validation, _ = swe.calc_ut(jd, swe.MOON)
print(f"Validation.py Moon: {moon_validation[0]:.4f}°")

# ==============================
# בדיקה 2: CalculationEngine.py
# ==============================
local_tz = pytz.timezone('Asia/Jerusalem')
local_dt = local_tz.localize(birth_date)
utc_dt = local_dt.astimezone(pytz.utc)
jd_ce = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                   utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0)
moon_ce, _ = swe.calc_ut(jd_ce, swe.MOON)
print(f"CalculationEngine Moon: {moon_ce[0]:.4f}°")

print(f"\nDifference: {abs(moon_validation[0] - moon_ce[0]):.4f}°")