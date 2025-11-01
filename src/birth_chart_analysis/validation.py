#!/usr/bin/env python3
"""
Improved Verification script for exact transit dates
====================================================
Improvements:
- Better parsing of aspect headers
- Handles both "שיא ההיבט" and "שיאים נוספים"
- More accurate planet and aspect name detection
- Better error categorization
"""

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
    'ראש דרקון': 'NorthNode',
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
    'טריגון': 'Trine',
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


def get_planet_position(planet_id, dt):
    """Get planet longitude at given datetime"""
    if planet_id is None:
        return None

    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60)

    if planet_id == 10:  # North Node
        planet_id = swe.MEAN_NODE
    elif planet_id == 12:  # Lilith
        planet_id = swe.MEAN_APOG
    elif planet_id == 15:  # Chiron
        planet_id = swe.CHIRON

    result = swe.calc_ut(jd, planet_id)
    return result[0][0]


def calculate_orb(natal_lon, transit_lon, aspect_angle):
    """Calculate orb for given positions and aspect"""
    diff = abs(transit_lon - natal_lon)
    diff = min(diff, 360 - diff)
    orb = abs(diff - aspect_angle)
    return orb


def parse_text_file_improved(file_path):
    """
    Improved parsing of Hebrew text format transit file
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

            # If we successfully parsed the header, look for exact dates
            if natal_planet and transit_planet and aspect_name:
                aspect_data = {
                    'natal_planet': natal_planet,
                    'aspect_type': aspect_name,
                    'transit_planet': transit_planet,
                    'exact_dates': []
                }

                # Look ahead for exact dates
                j = i + 1
                while j < len(lines) and j < i + 20:  # Look ahead max 20 lines
                    next_line = lines[j].strip()

                    # Stop if we hit another aspect header or separator
                    if ('(לידה)' in next_line and '(מעבר)' in next_line) or \
                            next_line.startswith('---'):
                        break

                    # Look for "שיא ההיבט:" or dates in "שיאים נוספים:"
                    date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2})', next_line)
                    if date_match:
                        day, month, year, hour, minute = date_match.groups()
                        date_str = f"{year}-{month}-{day} {hour}:{minute}:00"
                        is_retro = '⟲' in next_line

                        aspect_data['exact_dates'].append({
                            'date': date_str,
                            'is_retrograde': is_retro
                        })

                    j += 1

                if aspect_data['exact_dates']:
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
    print(f"VALIDATION RESULTS")
    print(f"{'=' * 70}")
    print(f"Total aspects found: {len(aspects)}")
    print(f"Total exact dates verified: {verified}")
    print(f"Skipped (AC/MC/PartOfFortune): {skipped}")

    print(f"\n📊 ACCURACY BREAKDOWN:")
    print(f"  ⭐ Perfect (< 0.1°):     {len(perfect):4d} ({100 * len(perfect) / verified:.1f}%)")
    print(f"  ✓  Good (0.1° - 0.5°):   {len(good):4d} ({100 * len(good) / verified:.1f}%)")
    print(f"  ⚠️  Minor (0.5° - 2°):    {len(minor_errors):4d} ({100 * len(minor_errors) / verified:.1f}%)")
    print(f"  ⚠️  Moderate (2° - 10°):  {len(moderate_errors):4d} ({100 * len(moderate_errors) / verified:.1f}%)")
    print(f"  ❌ Major (10° - 30°):    {len(major_errors):4d} ({100 * len(major_errors) / verified:.1f}%)")
    print(f"  ❌ Wrong aspect (>30°):  {len(wrong_aspect_errors):4d} ({100 * len(wrong_aspect_errors) / verified:.1f}%)")

    acceptable = len(perfect) + len(good)
    print(f"\n✅ Acceptable accuracy (< 0.5°): {100 * acceptable / verified:.1f}%")
    print(f"❌ Needs improvement (≥ 0.5°): {100 * len(errors) / verified:.1f}%")

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


if __name__ == "__main__":
    birth_date = datetime(2001, 11, 23, 18, 31)

    natal_positions = {}
    for planet_name, planet_id in PLANET_IDS.items():
        if planet_id is None:
            natal_positions[planet_name] = None
        else:
            natal_positions[planet_name] = get_planet_position(planet_id, birth_date)

    file_path = os.path.join(FILE_DIR, 'future_transits_עמיחי_20251101_1747.txt')
    results = verify_exact_dates(file_path, natal_positions)