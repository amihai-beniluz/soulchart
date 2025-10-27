"""
TransitCalculator.py
מנוע לחישוב טרנזיטים עתידיים וזיהוי אירועים אסטרולוגיים.
מחזיר נתונים מובנים (JSON-compatible) ללא תלות בממשק.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import uuid

from .CalculationEngine import (
    calculate_aspect_lifecycle,
    calculate_transit_aspects,
    calculate_chart_positions,
    calculate_current_positions,
    PLANET_IDS_FOR_TRANSIT,
    ASPECTS_DICT,
    ASPECT_ORBS
)


class TransitCalculator:
    """מחשב ומנתח טרנזיטים בטווח זמן נתון."""

    def __init__(self, user):
        """
        :param user: אובייקט User עם נתוני לידה
        """
        self.user = user

        # חישוב מפת הלידה פעם אחת
        birth_datetime = datetime.combine(user.birthdate, user.birthtime)
        self.natal_chart = calculate_chart_positions(
            birth_datetime,
            user.location[0],
            user.location[1]
        )

    def calculate_aspects_in_range(
            self,
            start_date: datetime,
            end_date: datetime,
            current_location: Tuple[float, float] = None,
            aspects_filter: List[str] = None
    ) -> Dict:
        """
        מחשב את כל ההיבטים בטווח זמן נתון.

        :param start_date: תאריך התחלה
        :param end_date: תאריך סיום
        :param current_location: מיקום נוכחי (lat, lon), אם None ישתמש במיקום הלידה
        :param aspects_filter: רשימת שמות היבטים לכלול (None = הכל)
        :return: מילון עם כל ההיבטים והמטא-דאטה
        """
        if current_location is None:
            current_location = self.user.location

        # אוסף את כל ההיבטים הייחודיים שקיימים בטווח
        aspects_collection = {}

        # סריקה יומית של הטווח
        current_scan_date = start_date
        scan_interval = timedelta(days=1)

        print(f"🔍 סורק טרנזיטים מ-{start_date:%Y-%m-%d} עד {end_date:%Y-%m-%d}...")

        while current_scan_date <= end_date:
            # חישוב טרנזיט ליום הנוכחי
            transit_positions = calculate_current_positions(
                current_scan_date,
                current_location[0],
                current_location[1]
            )

            # חישוב היבטים
            daily_aspects = calculate_transit_aspects(
                self.natal_chart['Planets'],
                transit_positions['Planets']
            )

            # מיון לפי היבטים ייחודיים
            for aspect in daily_aspects:
                # יצירת מזהה ייחודי להיבט
                aspect_key = (
                    aspect['planet1'],
                    aspect['planet2'],
                    aspect['aspect_name_eng'],
                    aspect['exact_angle']
                )

                # סינון לפי aspects_filter
                if aspects_filter and aspect['aspect_name_eng'] not in aspects_filter:
                    continue

                # אם זה היבט חדש - חשב את מחזור החיים המלא שלו
                if aspect_key not in aspects_collection:
                    aspect_id = str(uuid.uuid4())

                    try:
                        # חישוב lifecycle מלא
                        natal_lon = self.natal_chart['Planets'][aspect['planet1']]['lon_deg']
                        transit_planet_id = PLANET_IDS_FOR_TRANSIT.get(aspect['planet2'])

                        if transit_planet_id is not None:
                            lifecycle = calculate_aspect_lifecycle(
                                natal_lon,
                                transit_planet_id,
                                aspect['exact_angle'],
                                aspect['max_orb'],
                                current_scan_date
                            )

                            # שמירת ההיבט
                            aspects_collection[aspect_key] = {
                                'id': aspect_id,
                                'natal_planet': aspect['planet1'],
                                'transit_planet': aspect['planet2'],
                                'aspect_type': aspect['aspect_name_eng'],
                                'aspect_angle': aspect['exact_angle'],
                                'max_orb': aspect['max_orb'],
                                'lifecycle': self._format_lifecycle(lifecycle)
                            }
                    except Exception as e:
                        print(f"⚠️ שגיאה בחישוב lifecycle עבור {aspect_key}: {e}")
                        continue

            current_scan_date += scan_interval

        # המרה לרשימה
        aspects_list = list(aspects_collection.values())

        print(f"✅ נמצאו {len(aspects_list)} היבטים ייחודיים")

        return {
            'aspects': aspects_list,
            'metadata': {
                'user_name': self.user.name,
                'birth_date': self.user.birthdate.isoformat(),
                'calculated_at': datetime.now().isoformat(),
                'range': [start_date.isoformat(), end_date.isoformat()],
                'total_aspects': len(aspects_list)
            }
        }

    def _format_lifecycle(self, lifecycle: Dict) -> Dict:
        """
        ממיר נתוני lifecycle לפורמט JSON-serializable.
        """
        return {
            'start': lifecycle['start'].isoformat() if lifecycle.get('start') else None,
            'end': lifecycle['end'].isoformat() if lifecycle.get('end') else None,
            'exact_dates': [
                {
                    'date': ex['date'].isoformat(),
                    'is_retrograde': ex['is_retrograde']
                }
                for ex in lifecycle.get('exact_dates', [])
            ],
            'has_retrograde': lifecycle.get('has_retrograde', False),
            'num_passes': lifecycle.get('num_passes', 1),
            'total_days': lifecycle.get('total_days', 0)
        }

    def get_active_aspects(self, date: datetime) -> List[Dict]:
        """
        מחזיר רשימת היבטים פעילים בתאריך מסוים.
        """
        # חישוב חלון סביב התאריך (±30 ימים)
        buffer_days = 30
        aspects_data = self.calculate_aspects_in_range(
            date - timedelta(days=buffer_days),
            date + timedelta(days=buffer_days)
        )

        active = []
        for aspect in aspects_data['aspects']:
            lifecycle = aspect['lifecycle']
            if lifecycle['start'] and lifecycle['end']:
                start = datetime.fromisoformat(lifecycle['start'])
                end = datetime.fromisoformat(lifecycle['end'])

                if start <= date <= end:
                    active.append(aspect)

        return active

    def get_next_events(
            self,
            from_date: datetime,
            days_ahead: int = 90,
            limit: int = 20
    ) -> List[Dict]:
        """
        מחזיר את N האירועים הבאים (כניסות, Exacts, יציאות).

        :param from_date: תאריך התחלה
        :param days_ahead: כמה ימים קדימה לסרוק
        :param limit: מספר אירועים מקסימלי להחזיר
        :return: רשימת אירועים ממוינת לפי תאריך
        """
        end_date = from_date + timedelta(days=days_ahead)
        aspects_data = self.calculate_aspects_in_range(from_date, end_date)

        events = []

        for aspect in aspects_data['aspects']:
            lifecycle = aspect['lifecycle']

            # אירוע כניסה
            if lifecycle['start']:
                start = datetime.fromisoformat(lifecycle['start'])
                if start >= from_date:
                    events.append({
                        'event_type': 'aspect_entry',
                        'date': lifecycle['start'],
                        'aspect_id': aspect['id'],
                        'aspect': aspect,
                        'description': f"כניסה: {aspect['natal_planet']} {aspect['aspect_type']} {aspect['transit_planet']}"
                    })

            # אירועי Exact
            for exact in lifecycle['exact_dates']:
                exact_date = datetime.fromisoformat(exact['date'])
                if exact_date >= from_date:
                    retro_marker = " ⟲" if exact['is_retrograde'] else ""
                    events.append({
                        'event_type': 'exact',
                        'date': exact['date'],
                        'aspect_id': aspect['id'],
                        'aspect': aspect,
                        'is_retrograde': exact['is_retrograde'],
                        'description': f"Exact: {aspect['natal_planet']} {aspect['aspect_type']} {aspect['transit_planet']}{retro_marker}"
                    })

            # אירוע יציאה
            if lifecycle['end']:
                end = datetime.fromisoformat(lifecycle['end'])
                if end >= from_date:
                    events.append({
                        'event_type': 'aspect_exit',
                        'date': lifecycle['end'],
                        'aspect_id': aspect['id'],
                        'aspect': aspect,
                        'description': f"יציאה: {aspect['natal_planet']} {aspect['aspect_type']} {aspect['transit_planet']}"
                    })

        # מיון לפי תאריך והגבלה
        events.sort(key=lambda e: e['date'])
        return events[:limit]

    def should_notify(
            self,
            aspect: Dict,
            current_date: datetime,
            notification_settings: Dict = None
    ) -> Dict:
        """
        קובע אם צריך לשלוח התראה למשתמש על היבט זה.

        :param aspect: מילון היבט
        :param current_date: התאריך הנוכחי
        :param notification_settings: הגדרות התראות (None = ברירת מחדל)
        :return: מילון עם פרטי ההתראה
        """
        if notification_settings is None:
            notification_settings = {
                'notify_on_entry': True,
                'notify_on_exact': True,
                'exact_warning_hours': 24,  # התראה 24 שעות לפני Exact
                'major_aspects_only': False
            }

        lifecycle = aspect['lifecycle']

        # בדיקת כניסה להיבט
        if notification_settings['notify_on_entry'] and lifecycle['start']:
            start = datetime.fromisoformat(lifecycle['start'])
            time_diff = (start - current_date).total_seconds()

            # אם נכנסנו להיבט בשעה האחרונה
            if 0 <= time_diff <= 3600:
                return {
                    'should_notify': True,
                    'notification_type': 'aspect_entry',
                    'message': f"נכנסת להיבט {aspect['natal_planet']} {aspect['aspect_type']} {aspect['transit_planet']}!",
                    'aspect_id': aspect['id'],
                    'priority': 'high' if aspect['aspect_type'] in ['Conjunction', 'Opposition', 'Square'] else 'medium'
                }

        # בדיקת Exact קרוב
        if notification_settings['notify_on_exact']:
            warning_seconds = notification_settings['exact_warning_hours'] * 3600

            for exact in lifecycle['exact_dates']:
                exact_date = datetime.fromisoformat(exact['date'])
                time_to_exact = (exact_date - current_date).total_seconds()

                # התראה לפני Exact
                if 0 <= time_to_exact <= warning_seconds:
                    hours_left = int(time_to_exact / 3600)
                    retro_marker = " ⟲" if exact['is_retrograde'] else ""
                    return {
                        'should_notify': True,
                        'notification_type': 'exact_soon',
                        'message': f"עוד {hours_left} שעות ל-Exact: {aspect['natal_planet']} {aspect['aspect_type']} {aspect['transit_planet']}{retro_marker}",
                        'aspect_id': aspect['id'],
                        'priority': 'high'
                    }

                # התראה ב-Exact עצמו (בשעה הקרובה)
                if abs(time_to_exact) <= 3600:
                    return {
                        'should_notify': True,
                        'notification_type': 'exact_now',
                        'message': f"⚡ Exact עכשיו: {aspect['natal_planet']} {aspect['aspect_type']} {aspect['transit_planet']}!",
                        'aspect_id': aspect['id'],
                        'priority': 'critical'
                    }

        return {
            'should_notify': False
        }

    def format_future_transits_report(result: dict) -> list:
        """
        ממיר את תוצאות ה-JSON לדוח טקסט קריא בפורמט דומה לטרנזיטים נוכחיים.

        :param result: מילון התוצאות מ-calculate_aspects_in_range
        :return: רשימת שורות לכתיבה לקובץ
        """
        report = []

        # כותרת
        metadata = result['metadata']
        report.append(f"=== טרנזיטים עתידיים עבור {metadata['user_name']} ===")
        report.append(f"תאריך לידה: {metadata['birth_date']}")
        report.append(f"נוצר ב: {metadata['calculated_at'][:19]}")
        report.append(f"טווח: {metadata['range'][0][:10]} - {metadata['range'][1][:10]}")
        report.append(f"סה\"כ היבטים: {metadata['total_aspects']}")
        report.append("")

        # מיון ההיבטים לפי תאריך התחלה
        aspects = sorted(result['aspects'],
                         key=lambda x: x['lifecycle']['start'] if x['lifecycle']['start'] else '9999-99-99')

        report.append("=" * 80)
        report.append("רשימת כל ההיבטים העתידיים")
        report.append("=" * 80)
        report.append("")

        for i, aspect in enumerate(aspects, 1):
            lifecycle = aspect['lifecycle']

            # שורת כותרת ההיבט
            aspect_line = f"{aspect['natal_planet']} {aspect['aspect_type']} {aspect['transit_planet']}"
            report.append(aspect_line)

            # תקופת פעילות
            if lifecycle['start'] and lifecycle['end']:
                start_date = lifecycle['start'][:10]
                end_date = lifecycle['end'][:10]
                passes_suffix = ""
                if lifecycle['num_passes'] > 1:
                    passes_suffix = f", {lifecycle['num_passes']} מעברים"

                report.append(
                    f"    - תקופת פעילות: {start_date} - {end_date} ({lifecycle['total_days']} ימים{passes_suffix})")

            # תאריכי Exact
            if lifecycle['exact_dates']:
                exact_parts = []
                for ex in lifecycle['exact_dates']:
                    exact_date = ex['date'][:10]
                    retro_marker = " ⟲" if ex['is_retrograde'] else ""
                    exact_parts.append(f"{exact_date}{retro_marker}")

                report.append(f"    - Exact: {', '.join(exact_parts)}")

            # אורב מקסימלי
            report.append(f"    - אורב מקסימלי: {aspect['max_orb']:.2f}°")

            report.append("")

            # מפריד כל 10 היבטים לקריאות
            if i % 10 == 0 and i < len(aspects):
                report.append("-" * 80)
                report.append("")

        return report