"""
test_calculator.py
סקריפט לבדיקת TransitCalculator - חישוב טרנזיטים עתידיים.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# הוספת נתיב הפרויקט
MODULE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(MODULE_DIR, os.pardir, os.pardir))
sys.path.insert(0, PROJECT_DIR)

from src.user import User
from src.birth_chart_analysis.TransitCalculator import TransitCalculator


def test_basic_calculation():
    """בדיקה בסיסית - חישוב טרנזיטים לחודש הבא"""
    print("=" * 80)
    print("🧪 בדיקה 1: חישוב טרנזיטים לחודש הבא")
    print("=" * 80)

    # יצירת משתמש דוגמה
    user = User(
        name="עמיחי",
        birthdate=datetime(2001, 11, 23).date(),
        birthtime=datetime.strptime("18:31", "%H:%M").time(),
        location=(32.34, 34.85)
    )

    # יצירת מחשבון
    calculator = TransitCalculator(user)

    # חישוב לחודש הבא
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)

    result = calculator.calculate_aspects_in_range(
        start_date,
        end_date,
        current_location=(31.69, 35.12)  # מיקום נוכחי
    )

    # הצגת תוצאות
    print(f"\n📊 נמצאו {result['metadata']['total_aspects']} היבטים\n")

    for i, aspect in enumerate(result['aspects'][:5], 1):  # 5 ראשונים
        print(f"{i}. {aspect['natal_planet']} {aspect['aspect_type']} {aspect['transit_planet']}")
        print(f"   📅 {aspect['lifecycle']['start'][:10]} - {aspect['lifecycle']['end'][:10]}")
        print(f"   ⚡ Exacts: {len(aspect['lifecycle']['exact_dates'])}")
        print()

    return result


def test_next_events():
    """בדיקה 2: האירועים הבאים"""
    print("\n" + "=" * 80)
    print("🧪 בדיקה 2: 10 האירועים הבאים")
    print("=" * 80)

    user = User(
        name="עמיחי",
        birthdate=datetime(2001, 11, 23).date(),
        birthtime=datetime.strptime("18:31", "%H:%M").time(),
        location=(32.34, 34.85)
    )

    calculator = TransitCalculator(user)

    events = calculator.get_next_events(
        from_date=datetime.now(),
        days_ahead=60,
        limit=10
    )

    print(f"\n📅 נמצאו {len(events)} אירועים:\n")

    for i, event in enumerate(events, 1):
        date_str = event['date'][:10]
        print(f"{i}. [{event['event_type']}] {date_str}: {event['description']}")

    return events


def test_notifications():
    """בדיקה 3: בדיקת התראות"""
    print("\n" + "=" * 80)
    print("🧪 בדיקה 3: סימולציה של התראות")
    print("=" * 80)

    user = User(
        name="עמיחי",
        birthdate=datetime(2001, 11, 23).date(),
        birthtime=datetime.strptime("18:31", "%H:%M").time(),
        location=(32.34, 34.85)
    )

    calculator = TransitCalculator(user)

    # קבל היבטים פעילים כרגע
    active = calculator.get_active_aspects(datetime.now())

    print(f"\n🔔 בודק התראות עבור {len(active)} היבטים פעילים:\n")

    notifications_count = 0
    for aspect in active:
        notification = calculator.should_notify(aspect, datetime.now())

        if notification['should_notify']:
            notifications_count += 1
            print(f"✅ [{notification['notification_type']}] {notification['message']}")
            print(f"   עדיפות: {notification['priority']}")
            print()

    if notifications_count == 0:
        print("❌ אין התראות לשלוח כרגע")
    else:
        print(f"\n📬 סה\"כ {notifications_count} התראות")


def test_save_to_json():
    """בדיקה 4: שמירה ל-JSON"""
    print("\n" + "=" * 80)
    print("🧪 בדיקה 4: שמירת נתונים ל-JSON")
    print("=" * 80)

    user = User(
        name="עמיחי",
        birthdate=datetime(2001, 11, 23).date(),
        birthtime=datetime.strptime("18:31", "%H:%M").time(),
        location=(32.34, 34.85)
    )

    calculator = TransitCalculator(user)

    # חישוב ל-3 חודשים
    result = calculator.calculate_aspects_in_range(
        datetime.now(),
        datetime.now() + timedelta(days=90)
    )

    # שמירה
    output_dir = os.path.join(PROJECT_DIR, 'output', 'transits')
    os.makedirs(output_dir, exist_ok=True)

    filename = f"transits_{user.name}_{datetime.now():%Y%m%d}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ נתונים נשמרו בהצלחה: {filepath}")
    print(f"📊 גודל קובץ: {os.path.getsize(filepath) / 1024:.1f} KB")


def main():
    """הרצת כל הבדיקות"""
    try:
        # בדיקה 1
        result = test_basic_calculation()

        # בדיקה 2
        events = test_next_events()

        # בדיקה 3
        test_notifications()

        # בדיקה 4
        test_save_to_json()

        print("\n" + "=" * 80)
        print("✅ כל הבדיקות הסתיימו בהצלחה!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()