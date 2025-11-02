#!/usr/bin/env python3
"""
Script to analyze why validation finds fewer aspects than in the report
Run this to find out why 322 aspects in report but only 232 found by validation
"""
import re
import os

MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(MODULE_DIR)
FILE_DIR = os.path.join(PROJECT_DIR, 'output', 'transits')


def count_aspects_in_file(file_path):
    """Count total aspects mentioned in the file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    total_aspects = 0
    aspects_with_dates = 0
    aspects_without_dates = 0
    aspects_with_exact = 0
    aspects_with_period = 0

    aspects_no_dates = []  # Store aspects without dates

    for i, line in enumerate(lines):
        # Look for aspect headers
        if '(לידה)' in line and '(מעבר)' in line:
            total_aspects += 1

            # Check next 20 lines for dates
            has_period = False
            has_exact = False

            for j in range(i + 1, min(i + 20, len(lines))):
                next_line = lines[j]

                # Stop at next aspect or separator
                if ('(לידה)' in next_line and '(מעבר)' in next_line) or next_line.startswith('---'):
                    break

                # Check for period
                if 'תקופת פעילות:' in next_line:
                    has_period = True

                # Check for exact date
                if 'שיא ההיבט:' in next_line or 'שיאים נוספים:' in next_line:
                    has_exact = True

            if has_period or has_exact:
                aspects_with_dates += 1
                if has_period:
                    aspects_with_period += 1
                if has_exact:
                    aspects_with_exact += 1
            else:
                aspects_without_dates += 1
                aspects_no_dates.append({
                    'line_num': i + 1,
                    'text': line.strip()
                })

    return {
        'total': total_aspects,
        'with_dates': aspects_with_dates,
        'without_dates': aspects_without_dates,
        'with_period': aspects_with_period,
        'with_exact': aspects_with_exact,
        'no_dates_list': aspects_no_dates
    }


def main():
    # Try to find the file
    possible_paths = ['future_transits_עמיחי_20251102_1520_positions.txt']

    # Also check in current directory
    import glob
    txt_files = glob.glob('*.txt') + glob.glob('**/future_transits*.txt', recursive=True)
    possible_paths.extend(txt_files)

    file_path = os.path.join(FILE_DIR, 'future_transits_עמיחי_20251102_1520_positions.txt')

    if not file_path:
        print("❌ ERROR: Could not find the transit report file!")
        print("\nPlease run this script from the directory containing your transit report,")
        print("or modify the file_path variable in the script.")
        print("\nLooking for file like: future_transits_*_positions.txt")
        return

    print("=" * 70)
    print("ANALYZING TRANSIT REPORT FOR MISSING ASPECTS")
    print("=" * 70)
    print(f"\nFile: {file_path}\n")

    stats = count_aspects_in_file(file_path)

    print("=" * 70)
    print("ASPECT COUNT ANALYSIS")
    print("=" * 70)
    print(f"Total aspects in file:            {stats['total']}")
    print(f"Aspects WITH dates:               {stats['with_dates']}")
    print(f"Aspects WITHOUT dates:            {stats['without_dates']}")
    print(f"  - With period (תקופת פעילות):  {stats['with_period']}")
    print(f"  - With exact date (שיא ההיבט):  {stats['with_exact']}")
    print("=" * 70)

    if stats['without_dates'] > 0:
        print(f"\n⚠️  FOUND {stats['without_dates']} ASPECTS WITHOUT DATES!")
        print("=" * 70)
        print("These are likely why validation finds fewer aspects.\n")

        print("List of aspects without dates (first 20):")
        print("-" * 70)
        for aspect in stats['no_dates_list'][:20]:
            print(f"Line {aspect['line_num']}: {aspect['text']}")

        if len(stats['no_dates_list']) > 20:
            print(f"\n... and {len(stats['no_dates_list']) - 20} more")

        print("\n" + "=" * 70)
        print("WHY DO THESE ASPECTS HAVE NO DATES?")
        print("=" * 70)
        print("Possible reasons:")
        print("1. These aspects are outside the date range requested")
        print("2. The calculation failed to find exact dates for them")
        print("3. The orb threshold rejected them (actual_orb > max_acceptable_orb)")
        print("\nTo investigate further:")
        print("- Open the report and search for one of these aspects")
        print("- Check if it has any date information below the header")
        print("- If not, check why the calculation didn't find dates")
    else:
        print("\n✅ All aspects have dates!")
        print("The difference between 322 and 232 must be from parsing issues.")
        print("\nPossible reasons:")
        print("1. Planet or aspect names not recognized by validation")
        print("2. Formatting issues preventing date extraction")
        print("3. Some aspects counted twice in the report")


if __name__ == '__main__':
    main()
