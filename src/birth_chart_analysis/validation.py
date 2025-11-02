#!/usr/bin/env python3
"""
Improved Verification script for exact transit dates
====================================================
Improvements:
- Better parsing of aspect headers
- Handles both "שין הדייקט" and "שיאיין נוספיי"
- More accurate planet and aspect name detection
- Better error categorization
- NEW: Validates start/end dates against maximum orbs
"""

# TODO להבין למה מספר ההיבטים שנמצאים קטן בהרבה ממה שמופיע בדוח
# TODO לטפל בשגיאה של נפטון חצי ריבוע ירח במעבר

import re
import os
from datetime import datetime
import swisseph as swe

# Setup Swiss Ephemeris - use /home/claude/ephe
MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))
EPHE_DIR = os.path.join(PROJECT_DIR, 'data', 'ephe')
FILE_DIR = os.path.join(PROJECT_DIR, 'output', 'transits')
if os.path.exists(EPHE_DIR):
    swe.set_ephe_path(EPHE_DIR)

# Planet IDs
PLANET_IDS = {
    'Sun': 0, 'Moon': 1, 'Mercury': 2, 'Venus': 3, 'Mars': 4,
    'Jupiter': 5, 'Saturn': 6, 'Uranus': 7, 'Neptune': 8, 'Pluto': 9,
    'NorthNode': 10, 'Chiron': 15, 'Lilith': 12,
    'AC': None, 'MC': None, 'PartOfFortune': None
}

# Hebrew to English planet names - COMPLETE MAPPING
PLANET_NAMES_HE = {
    'שמש': 'Sun',
    'ירח': 'Moon',
    'מרקורי': 'Mercury',
    'ונוס': 'Venus',
    'מאדים': 'Mars',
    'צדק': 'Jupiter',
    'שבתאי': 'Saturn',
    'אורנוס': 'Uranus',
    'נפטון': 'Neptune',
    'פלוטו': 'Pluto',
    'ראש הרקון': 'NorthNode',
    'כירון': 'Chiron',
    'לילית': 'Lilith',
    'AC': 'AC',
    'MC': 'MC',
    'נקודת מזל': 'PartOfFortune'
}

# Hebrew to English aspect names - ALL VARIANTS
ASPECT_NAMES_HE = {
    # Major aspects
    'צמוד': 'Conjunction',
    'משושה': 'Sextile',
    'סקסטייל': 'Sextile',
    'ריבוע': 'Square',
    'משולש': 'Trine',
    'טריבון': 'Trine',
    'מול': 'Opposition',
    'אופוזיציה': 'Opposition',

    # Minor aspects - WITH ALL VARIANTS
    'קווינקונקס': 'Inconjunct',
    'חצי-משושה': 'SemiSextile',
    'חצי משושה': 'SemiSextile',
    'חצי-ריבוע': 'SemiSquare',
    'חצי ריבוע': 'SemiSquare',
    'סקווי-ריבוע': 'Sesquiquadrate',
    'סקווי ריבוע': 'Sesquiquadrate',
    'סקווירפיינד': 'Sesquiquadrate',
    'קווינטייל': 'Quintile',
    'ביקווינטייל': 'Biquintile'
}

# Aspect angles
ASPECTS = {
    'Conjunction': 0,
    'Sextile': 60,
    'Square': 90,
    'Trine': 120,
    'Opposition': 180,
    'Inconjunct': 150,
    'SemiSextile': 30,
    'SemiSquare': 45,
    'Sesquiquadrate': 135,
    'Quintile': 72,
    'Biquintile': 144
}

# Maximum allowed orbs for each aspect
ASPECT_ORBS = {
    # היבטים מז'וריים - חזקים:
    'Conjunction': 10.0,  # היצמדות
    'Opposition': 10.0,  # ניגוד
    'Square': 9.0,  # ריבוע
    'Trine': 8.0,  # טרין
    'Sextile': 6.0,  # סקסטייל

    # היבטים משניים - חלשים:
    'Inconjunct': 2.5,  # קווינקונקס
    'SemiSquare': 2.0,  # סמי-ריבוע
    'Sesquiquadrate': 2.0,  # סקווירפיינד
    'SemiSextile': 1.5,  # סמי-סקסטייל
    'Quintile': 1.0,  # קווינטייל
    'Biquintile': 1.0  # ביקווינטייל
}


def get_planet_position(planet_id, dt):
    """Get planet longitude at given datetime"""
    if planet_id is None:
        return None

    # 🔧 FIX: אם dt כבר UTC - השתמש בו ישירות, אחרת המר
    if dt.tzinfo is not None:
        # DateTime עם timezone - השתמש בו כמו שהוא
        jd = swe.julday(dt.year, dt.month, dt.day,
                        dt.hour + dt.minute / 60.0 + dt.second / 3600.0)
    else:
        # DateTime ללא timezone - נניח שזה UTC (התנהגות ישנה)
        jd = swe.julday(dt.year, dt.month, dt.day,
                        dt.hour + dt.minute / 60.0)

    if planet_id == 10:  # North Node
        planet_id = swe.MEAN_NODE
    elif planet_id == 12:  # Lilith
        planet_id = swe.MEAN_APOG
    elif planet_id == 15:  # Chiron
        planet_id = swe.CHIRON

    xx, _ = swe.calc_ut(jd, planet_id)
    result = xx[0]
    return result


def calculate_orb(natal_lon, transit_lon, aspect_angle):
    """Calculate orb for given positions and aspect"""
    diff = abs(transit_lon - natal_lon)
    diff = min(diff, 360 - diff)
    orb = abs(diff - aspect_angle)
    return orb


def parse_text_file_improved(file_path):
    """
    Improved parsing of Hebrew text format transit file
    Extracts both exact dates AND start/end dates
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    aspects = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for aspect header line (contains both (לידה) and (מעבר))
        if '(לידה)' in line and '(מעבר)' in line:
            # Parse the aspect line
            natal_planet = None
            transit_planet = None
            aspect_name = None

            # Split by (לידה) and (מעבר)
            parts = line.split('(לידה)')
            if len(parts) >= 2:
                # Get natal planet (before לידה)
                before_natal = parts[0].strip()
                for he_name in sorted(PLANET_NAMES_HE.keys(), key=len, reverse=True):
                    if before_natal.endswith(he_name):
                        natal_planet = PLANET_NAMES_HE[he_name]
                        break

                # Split second part by (מעבר)
                after_natal = parts[1]
                parts2 = after_natal.split('(מעבר)')
                if len(parts2) >= 2:
                    middle = parts2[0].strip()

                    # Find aspect in middle part
                    for he_aspect in sorted(ASPECT_NAMES_HE.keys(), key=len, reverse=True):
                        if he_aspect in middle:
                            aspect_name = ASPECT_NAMES_HE[he_aspect]
                            # Remove aspect name to find transit planet
                            middle = middle.replace(he_aspect, '').strip()
                            break

                    # Find transit planet in what's left of middle
                    for he_name in sorted(PLANET_NAMES_HE.keys(), key=len, reverse=True):
                        if he_name in middle:
                            transit_planet = PLANET_NAMES_HE[he_name]
                            break

            # If we successfully parsed the header, look for dates
            if natal_planet and transit_planet and aspect_name:
                aspect_data = {
                    'natal_planet': natal_planet,
                    'aspect_type': aspect_name,
                    'transit_planet': transit_planet,
                    'exact_dates': [],
                    'start_date': None,
                    'end_date': None
                }

                # Look ahead for dates
                j = i + 1
                while j < len(lines) and j < i + 20:  # Look ahead max 20 lines
                    next_line = lines[j].strip()

                    # Stop if we hit another aspect header or separator
                    if ('(לידה)' in next_line and '(מעבר)' in next_line) or \
                            next_line.startswith('---'):
                        break

                    # Look for activity period: "תקופת פעילות: DD.MM.YYYY HH:MM - DD.MM.YYYY HH:MM"
                    period_match = re.search(
                        r'תקופת פעילות:\s*(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2})\s*-\s*(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2})',
                        next_line)
                    if period_match:
                        # Start date
                        day1, month1, year1, hour1, minute1 = period_match.groups()[:5]
                        aspect_data['start_date'] = f"{year1}-{month1}-{day1} {hour1}:{minute1}:00"
                        # End date
                        day2, month2, year2, hour2, minute2 = period_match.groups()[5:]
                        aspect_data['end_date'] = f"{year2}-{month2}-{day2} {hour2}:{minute2}:00"

                    # Look for exact date: "שיא ההיבט: DD.MM.YYYY HH:MM"
                    exact_match = re.search(r'שיא ההיבט:\s*(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2})', next_line)
                    if exact_match:
                        day, month, year, hour, minute = exact_match.groups()
                        date_str = f"{year}-{month}-{day} {hour}:{minute}:00"
                        is_retro = '⟲' in next_line

                        aspect_data['exact_dates'].append({
                            'date': date_str,
                            'is_retrograde': is_retro
                        })

                    j += 1

                # Only add if we found any dates
                if aspect_data['exact_dates'] or aspect_data['start_date'] or aspect_data['end_date']:
                    aspects.append(aspect_data)

        i += 1

    return aspects


def verify_exact_dates(file_path, natal_positions):
    """Verify all exact dates with improved error reporting"""

    aspects = parse_text_file_improved(file_path)

    print(f"✓ Total aspects found: {len(aspects)}")

    total_exact = sum(len(a['exact_dates']) for a in aspects)
    print(f"✓ Total exact dates found: {total_exact}\n")

    errors = []
    verified = 0
    skipped = 0

    # Categorize errors by type
    perfect = []  # orb < 0.1°
    good = []  # 0.1° < orb < 0.5°
    minor_errors = []  # 0.5° < orb < 2°
    moderate_errors = []  # 2° < orb < 10°
    major_errors = []  # 10° < orb < 30°
    wrong_aspect_errors = []  # orb > 30° (probably wrong aspect detection)

    for aspect in aspects:
        natal_planet = aspect['natal_planet']
        transit_planet = aspect['transit_planet']
        aspect_type = aspect['aspect_type']

        transit_id = PLANET_IDS.get(transit_planet)
        aspect_angle = ASPECTS.get(aspect_type)
        natal_lon = natal_positions.get(natal_planet)

        if not all([natal_lon is not None, transit_id is not None, aspect_angle is not None]):
            skipped += len(aspect['exact_dates'])
            continue

        for exact in aspect['exact_dates']:
            exact_dt = datetime.strptime(exact['date'], '%Y-%m-%d %H:%M:%S')
            transit_lon = get_planet_position(transit_id, exact_dt)

            orb = calculate_orb(natal_lon, transit_lon, aspect_angle)
            verified += 1

            error_info = {
                'aspect': f"{natal_planet} {aspect_type} {transit_planet}",
                'date': exact['date'],
                'orb': orb,
                'is_retro': exact['is_retrograde']
            }

            # Categorize by orb size
            if orb < 0.1:
                perfect.append(error_info)
            elif orb < 0.5:
                good.append(error_info)
            elif orb < 2:
                minor_errors.append(error_info)
                errors.append(error_info)
            elif orb < 10:
                moderate_errors.append(error_info)
                errors.append(error_info)
            elif orb < 30:
                major_errors.append(error_info)
                errors.append(error_info)
            else:
                wrong_aspect_errors.append(error_info)
                errors.append(error_info)

    # Print summary
    print(f"\n{'=' * 70}")
    print(f"VALIDATION RESULTS - EXACT DATES")
    print(f"{'=' * 70}")
    print(f"Total aspects found: {len(aspects)}")
    print(f"Total exact dates verified: {verified}")
    print(f"Skipped (AC/MC/PartOfFortune): {skipped}")

    if verified > 0:
        print(f"\n📊 ACCURACY BREAKDOWN:")
        print(f"  ⭐ Perfect (< 0.1°):     {len(perfect):4d} ({100 * len(perfect) / verified:.1f}%)")
        print(f"  ✓  Good (0.1° - 0.5°):   {len(good):4d} ({100 * len(good) / verified:.1f}%)")
        print(f"  ⚠️  Minor (0.5° - 2°):    {len(minor_errors):4d} ({100 * len(minor_errors) / verified:.1f}%)")
        print(f"  ⚠️  Moderate (2° - 10°):  {len(moderate_errors):4d} ({100 * len(moderate_errors) / verified:.1f}%)")
        print(f"  ❌ Major (10° - 30°):    {len(major_errors):4d} ({100 * len(major_errors) / verified:.1f}%)")
        print(
            f"  ❌ Wrong aspect (>30°):  {len(wrong_aspect_errors):4d} ({100 * len(wrong_aspect_errors) / verified:.1f}%)")

        acceptable = len(perfect) + len(good)
        print(f"\n✅ Acceptable accuracy (< 0.5°): {100 * acceptable / verified:.1f}%")
        print(f"❌ Needs improvement (≥ 0.5°): {100 * len(errors) / verified:.1f}%")
    else:
        print("\n⚠️ No exact dates found to verify!")

    # Show worst errors
    if wrong_aspect_errors:
        print(f"\n❌ LIKELY WRONG ASPECT DETECTIONS (showing first 10):")
        for err in sorted(wrong_aspect_errors, key=lambda x: -x['orb'])[:10]:
            retro = " ⟲" if err['is_retro'] else ""
            print(f"   {err['aspect']}{retro}")
            print(f"      Date: {err['date'][:16]} | Orb: {err['orb']:.1f}°")

    if moderate_errors:
        print(f"\n⚠️  MODERATE ERRORS (showing first 10):")
        for err in sorted(moderate_errors, key=lambda x: -x['orb'])[:10]:
            retro = " ⟲" if err['is_retro'] else ""
            print(f"   {err['aspect']}{retro}")
            print(f"      Date: {err['date'][:16]} | Orb: {err['orb']:.2f}°")

    if minor_errors:
        print(f"\n⚠️  MINOR ERRORS (showing first 10):")
        for err in sorted(minor_errors, key=lambda x: -x['orb'])[:10]:
            retro = " ⟲" if err['is_retro'] else ""
            print(f"   {err['aspect']}{retro}")
            print(f"      Date: {err['date'][:16]} | Orb: {err['orb']:.2f}°")

    return {
        'total': verified,
        'perfect': len(perfect),
        'good': len(good),
        'errors': len(errors),
        'by_category': {
            'minor': len(minor_errors),
            'moderate': len(moderate_errors),
            'major': len(major_errors),
            'wrong': len(wrong_aspect_errors)
        }
    }


def verify_start_end_dates(file_path, natal_positions):
    """
    Verify that start and end dates match exactly the maximum allowed orb
    Start date: orb should equal max_orb (entering the aspect)
    End date: orb should equal max_orb (leaving the aspect)
    """
    aspects = parse_text_file_improved(file_path)

    # Count aspects with boundaries
    aspects_with_boundaries = [a for a in aspects if a['start_date'] or a['end_date']]
    print(f"✓ Total aspects with start/end dates: {len(aspects_with_boundaries)}\n")

    verified_start = 0
    verified_end = 0
    skipped = 0

    # Track errors by tolerance
    perfect_start = []  # |orb - max_orb| < 0.1°
    good_start = []  # 0.1° < |orb - max_orb| < 0.5°
    minor_start = []  # 0.5° < |orb - max_orb| < 1°
    major_start = []  # |orb - max_orb| >= 1°

    perfect_end = []
    good_end = []
    minor_end = []
    major_end = []

    for aspect in aspects:
        natal_planet = aspect['natal_planet']
        transit_planet = aspect['transit_planet']
        aspect_type = aspect['aspect_type']

        transit_id = PLANET_IDS.get(transit_planet)
        aspect_angle = ASPECTS.get(aspect_type)
        max_orb = ASPECT_ORBS.get(aspect_type)
        natal_lon = natal_positions.get(natal_planet)

        # Skip if we don't have all required data
        if not all([natal_lon is not None, transit_id is not None,
                    aspect_angle is not None, max_orb is not None]):
            if aspect['start_date']:
                skipped += 1
            if aspect['end_date']:
                skipped += 1
            continue

        # Check start date
        if aspect['start_date']:
            start_dt = datetime.strptime(aspect['start_date'], '%Y-%m-%d %H:%M:%S')
            transit_lon = get_planet_position(transit_id, start_dt)

            if transit_lon is not None:
                orb = calculate_orb(natal_lon, transit_lon, aspect_angle)
                diff_from_max = abs(orb - max_orb)
                verified_start += 1

                error_info = {
                    'aspect': f"{natal_planet} {aspect_type} {transit_planet}",
                    'date': aspect['start_date'],
                    'actual_orb': orb,
                    'expected_orb': max_orb,
                    'difference': diff_from_max
                }

                if diff_from_max < 0.1:
                    perfect_start.append(error_info)
                elif diff_from_max < 0.5:
                    good_start.append(error_info)
                elif diff_from_max < 1.0:
                    minor_start.append(error_info)
                else:
                    major_start.append(error_info)

        # Check end date
        if aspect['end_date']:
            end_dt = datetime.strptime(aspect['end_date'], '%Y-%m-%d %H:%M:%S')
            transit_lon = get_planet_position(transit_id, end_dt)

            if transit_lon is not None:
                orb = calculate_orb(natal_lon, transit_lon, aspect_angle)
                diff_from_max = abs(orb - max_orb)
                verified_end += 1

                error_info = {
                    'aspect': f"{natal_planet} {aspect_type} {transit_planet}",
                    'date': aspect['end_date'],
                    'actual_orb': orb,
                    'expected_orb': max_orb,
                    'difference': diff_from_max
                }

                if diff_from_max < 0.1:
                    perfect_end.append(error_info)
                elif diff_from_max < 0.5:
                    good_end.append(error_info)
                elif diff_from_max < 1.0:
                    minor_end.append(error_info)
                else:
                    major_end.append(error_info)

    total_verified = verified_start + verified_end

    # Print results
    print(f"Total boundary dates verified: {total_verified}")
    print(f"  - Start dates: {verified_start}")
    print(f"  - End dates: {verified_end}")
    print(f"Skipped (AC/MC/PartOfFortune): {skipped}\n")

    # Calculate totals
    total_perfect = len(perfect_start) + len(perfect_end)
    total_good = len(good_start) + len(good_end)
    acceptable = total_perfect + total_good

    if total_verified > 0:
        print("📊 START DATES ACCURACY:")
        if verified_start > 0:
            print(
                f"  ⭐ Perfect (< 0.1°):    {len(perfect_start):4d} ({100 * len(perfect_start) / verified_start:.1f}%)")
            print(f"  ✓  Good (0.1° - 0.5°):  {len(good_start):4d} ({100 * len(good_start) / verified_start:.1f}%)")
            print(f"  ⚠️  Minor (0.5° - 1°):   {len(minor_start):4d} ({100 * len(minor_start) / verified_start:.1f}%)")
            print(f"  ❌ Major (≥ 1°):        {len(major_start):4d} ({100 * len(major_start) / verified_start:.1f}%)")
        else:
            print(f"  No start dates to verify")

        print("\n📊 END DATES ACCURACY:")
        if verified_end > 0:
            print(f"  ⭐ Perfect (< 0.1°):    {len(perfect_end):4d} ({100 * len(perfect_end) / verified_end:.1f}%)")
            print(f"  ✓  Good (0.1° - 0.5°):  {len(good_end):4d} ({100 * len(good_end) / verified_end:.1f}%)")
            print(f"  ⚠️  Minor (0.5° - 1°):   {len(minor_end):4d} ({100 * len(minor_end) / verified_end:.1f}%)")
            print(f"  ❌ Major (≥ 1°):        {len(major_end):4d} ({100 * len(major_end) / verified_end:.1f}%)")
        else:
            print(f"  No end dates to verify")

        # Overall accuracy
        print(f"\n✅ Overall acceptable accuracy (< 0.5°): {100 * acceptable / total_verified:.1f}%")

        # Show worst errors for start dates
        if major_start:
            print(f"\n❌ MAJOR START DATE ERRORS (showing first 5):")
            for err in sorted(major_start, key=lambda x: -x['difference'])[:5]:
                print(f"   {err['aspect']}")
                print(f"      Date: {err['date'][:16]}")
                print(
                    f"      Expected orb: {err['expected_orb']:.2f}° | Actual: {err['actual_orb']:.2f}° | Diff: {err['difference']:.2f}°")

        # Show worst errors for end dates
        if major_end:
            print(f"\n❌ MAJOR END DATE ERRORS (showing first 5):")
            for err in sorted(major_end, key=lambda x: -x['difference'])[:5]:
                print(f"   {err['aspect']}")
                print(f"      Date: {err['date'][:16]}")
                print(
                    f"      Expected orb: {err['expected_orb']:.2f}° | Actual: {err['actual_orb']:.2f}° | Diff: {err['difference']:.2f}°")
    else:
        print("\n⚠️ No boundary dates found to verify!")

    return {
        'total': total_verified,
        'perfect': total_perfect,
        'good': total_good,
        'start_dates': {
            'total': verified_start,
            'perfect': len(perfect_start),
            'good': len(good_start),
            'minor': len(minor_start),
            'major': len(major_start)
        },
        'end_dates': {
            'total': verified_end,
            'perfect': len(perfect_end),
            'good': len(good_end),
            'minor': len(minor_end),
            'major': len(major_end)
        }
    }


if __name__ == "__main__":
    import pytz  # 🔧 FIX: הוסף import

    birth_date = datetime(2001, 11, 23, 18, 31)

    # 🔧 FIX: המר לאיזור זמן ישראלי ואז ל-UTC (כמו ב-CalculationEngine)
    local_tz = pytz.timezone('Asia/Jerusalem')
    local_dt = local_tz.localize(birth_date)
    utc_dt = local_dt.astimezone(pytz.utc)

    natal_positions = {}
    for planet_name, planet_id in PLANET_IDS.items():
        if planet_id is None:
            natal_positions[planet_name] = None
        else:
            # 🔧 FIX: השתמש ב-UTC datetime במקום ב-naive datetime
            natal_positions[planet_name] = get_planet_position(planet_id, utc_dt)

    file_path = os.path.join(FILE_DIR, 'future_transits_עמיחי_20251102_0326_positions.txt')

    # Verify exact dates
    print("=" * 70)
    print("PART 1: VERIFYING EXACT DATES")
    print("=" * 70)

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File not found: {file_path}")
        print(f"Looking in directory: {FILE_DIR}")
        if os.path.exists(FILE_DIR):
            print("\nFiles in directory:")
            for f in os.listdir(FILE_DIR):
                print(f"  - {f}")
        exit(1)

    exact_results = verify_exact_dates(file_path, natal_positions)

    # Verify start/end dates
    print("\n\n" + "=" * 70)
    print("PART 2: VERIFYING START/END DATES (ORB ACCURACY)")
    print("=" * 70)
    boundary_results = verify_start_end_dates(file_path, natal_positions)

    # Combined summary
    print("\n\n" + "=" * 70)
    print("COMBINED VALIDATION SUMMARY")
    print("=" * 70)
    if exact_results['total'] > 0:
        print(
            f"Exact dates - Acceptable accuracy: {100 * (exact_results['perfect'] + exact_results['good']) / exact_results['total']:.1f}%")
    else:
        print(f"Exact dates - No data to validate")

    if boundary_results['total'] > 0:
        print(
            f"Start/End dates - Acceptable accuracy: {100 * (boundary_results['perfect'] + boundary_results['good']) / boundary_results['total']:.1f}%")
    else:
        print(f"Start/End dates - No data to validate")