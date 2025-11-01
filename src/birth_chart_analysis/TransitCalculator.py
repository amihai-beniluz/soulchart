"""
TransitCalculator - מחשבון טרנזיטים עתידיים (גרסה 3.3)
==========================================================
🔧 FIX v3.3: מניעת דיווח על היבטים שגויים
- אם lifecycle מחזיר None (היבט לא תקין), דלג עליו
"""

from datetime import datetime, timedelta
from .CalculationEngine import (
    calculate_chart_positions,
    calculate_current_positions,
    calculate_transit_aspects,
    calculate_aspect_lifecycle,
    find_next_aspect_cycle,
    PLANET_IDS_FOR_TRANSIT,
    ASPECTS_DICT,
    ASPECT_ORBS,
    PLANET_AVG_SPEEDS
)


class TransitCalculator:
    """
    מחשב טרנזיטים עתידיים בטווח זמן נתון.
    """

    def __init__(self, user):
        """
        :param user: אובייקט User עם נתוני לידה
        """
        self.user = user

        # חישוב מפת הלידה פעם אחת
        birth_datetime = datetime.combine(user.birthdate, user.birthtime)
        natal_chart_data = calculate_chart_positions(
            birth_datetime,
            user.location[0],
            user.location[1]
        )

        self.natal_planets = natal_chart_data['Planets']

    def calculate_aspects_in_range(self, start_date: datetime, end_date: datetime,
                                   location: tuple) -> dict:
        """
        מחשב את כל ההיבטים שיתרחשו בטווח הזמן.
        כולל גם היבטים שמתחילים לפני הטווח אבל עדיין פעילים.

        :param start_date: תאריך התחלה
        :param end_date: תאריך סיום
        :param location: (latitude, longitude) מיקום נוכחי
        :return: dict עם metadata ורשימת היבטים
        """
        # בדיקות תקינות נתונים
        if not self.natal_planets:
            raise ValueError("natal_planets is empty - לא ניתן לחשב טרנזיטים")

        if start_date >= end_date:
            raise ValueError(f"start_date ({start_date}) חייב להיות לפני end_date ({end_date})")

        days = (end_date - start_date).days

        # אזהרה על טווח זמן גדול מדי
        if days > 365 * 5:
            import warnings
            warnings.warn(
                f"⚠️ טווח זמן גדול מאוד: {days} ימים ({days/365:.1f} שנים). "
                f"החישוב עלול לקחת זמן רב.",
                UserWarning
            )

        all_aspects = []

        # ========================================
        # שלב 1: מצא היבטים שכבר קיימים ב-start_date
        # ========================================
        # הלוגיקה:
        # 1. מחשבים את כל ההיבטים הפעילים ב-start_date
        # 2. לכל היבט, מחפשים את מחזור החיים המלא שלו
        # 3. אם המחזור חופף את הטווח שלנו - מוסיפים אותו
        # זה חשוב כדי לתפוס היבטים שהתחילו לפני start_date אבל עדיין פעילים

        # חישוב מיקומי טרנזיט ב-start_date
        transit_chart = calculate_current_positions(
            start_date, location[0], location[1]
        )
        transit_positions = transit_chart['Planets']

        # חישוב היבטים נוכחיים
        current_aspects = calculate_transit_aspects(
            self.natal_planets, transit_positions
        )

        # עבור כל היבט נוכחי, חשב את ה-lifecycle המלא
        existing_aspects_set = set()

        for aspect in current_aspects:
            natal_planet = aspect['planet1']
            transit_planet = aspect['planet2']
            aspect_name = aspect['aspect_name_eng']

            # קבל את המידע הנדרש
            natal_lon = self.natal_planets[natal_planet]['lon_deg']
            transit_planet_id = PLANET_IDS_FOR_TRANSIT.get(transit_planet)

            if transit_planet_id is None:
                continue

            aspect_angle = aspect['exact_angle']
            current_orb = aspect['orb']
            max_orb = aspect['max_orb']

            # יצירת מפתח ייחודי להיבט
            aspect_key = f"{natal_planet}_{transit_planet}_{aspect_name}"

            try:
                # חשב lifecycle - משתמש ב-start_date כנקודת התחלה
                # הפונקציה calculate_aspect_lifecycle תמצא את המחזור המלא סביב תאריך זה
                lifecycle = calculate_aspect_lifecycle(
                    natal_lon,
                    transit_planet_id,
                    aspect_angle,
                    max_orb,
                    start_date
                )

                # 🔧 FIX v3.3: אם lifecycle הוא None - ההיבט לא תקין, דלג
                if lifecycle is None:
                    continue

                # בדוק אם ההיבט חופף את הטווח
                # (התחיל לפני אבל עדיין פעיל, או מתחיל בטווח)
                if lifecycle['end'] >= start_date and lifecycle['start'] <= end_date:
                    all_aspects.append({
                        'natal_planet': natal_planet,
                        'transit_planet': transit_planet,
                        'aspect_type': aspect_name,
                        'max_orb': max_orb,
                        'lifecycle': {
                            'start': lifecycle['start'].isoformat(),
                            'end': lifecycle['end'].isoformat(),
                            'exact_dates': [
                                {
                                    'date': ex['date'].isoformat(),
                                    'is_retrograde': ex['is_retrograde']
                                }
                                for ex in lifecycle['exact_dates']
                            ],
                            'num_passes': lifecycle['num_passes'],
                            'has_retrograde': lifecycle['has_retrograde']
                        }
                    })

                    # שמור שמצאנו את ההיבט הזה
                    existing_aspects_set.add(aspect_key)

            except Exception as e:
                import traceback
                print(f"   ⚠️  שגיאה בחישוב lifecycle ל-{aspect_key}")
                print(f"       פרטי ההיבט: natal_lon={natal_lon:.2f}°, aspect={aspect_name} ({aspect_angle}°)")
                print(f"       אורב: {current_orb:.3f}° / {max_orb}°, תאריך: {start_date.date()}")
                print(f"       שגיאה: {type(e).__name__}: {e}")
                # אם רוצים traceback מלא, ניתן להוסיף:
                # traceback.print_exc()
                continue

        # ========================================
        # שלב 2: מצא היבטים חדשים שמתחילים בטווח
        # ========================================

        # עבור כל פלנטה נטאלית
        for natal_planet_name, natal_data in self.natal_planets.items():
            natal_lon = natal_data['lon_deg']

            # עבור כל פלנטה טרנזיטית
            for transit_planet_name, transit_planet_id in PLANET_IDS_FOR_TRANSIT.items():

                # חישוב מהירות ממוצעת ותנועה מקסימלית
                avg_speed = abs(PLANET_AVG_SPEEDS.get(transit_planet_id, 0.5))
                max_movement = avg_speed * days * 1.3

                # האם הפלנטה תעבור דרך כל המעגל?
                if max_movement >= 360:
                    check_all_aspects = True
                    min_possible_distance = 0
                    max_possible_distance = 180
                else:
                    check_all_aspects = False

                    # מיקום בתחילת הטווח
                    if transit_planet_name not in transit_positions:
                        continue

                    transit_lon = transit_positions[transit_planet_name]['lon_deg']
                    current_distance = abs(transit_lon - natal_lon)
                    current_distance = min(current_distance, 360 - current_distance)

                    min_possible_distance = max(0, current_distance - max_movement)
                    max_possible_distance = min(180, current_distance + max_movement)

                # בדוק כל זווית היבט אפשרית
                for aspect_angle, aspect_name in ASPECTS_DICT.items():
                    max_orb = ASPECT_ORBS[aspect_name]

                    # בדוק אם כבר מצאנו את ההיבט הזה בשלב 1
                    aspect_key = f"{natal_planet_name}_{transit_planet_name}_{aspect_name}"
                    if aspect_key in existing_aspects_set:
                        continue  # דלג - כבר מצאנו אותו

                    # סינון: האם ההיבט יכול להתרחש?
                    if not check_all_aspects:
                        aspect_min = aspect_angle - max_orb
                        aspect_max = aspect_angle + max_orb

                        if max_possible_distance < aspect_min or min_possible_distance > aspect_max:
                            continue

                    # 🎯 חפש את המחזור הבא של ההיבט
                    try:
                        cycle = find_next_aspect_cycle(
                            natal_lon,
                            transit_planet_id,
                            aspect_angle,
                            max_orb,
                            start_date,
                            end_date
                        )

                        # אם נמצא מחזור - הוסף אותו
                        if cycle is not None:
                            all_aspects.append({
                                'natal_planet': natal_planet_name,
                                'transit_planet': transit_planet_name,
                                'aspect_type': aspect_name,
                                'max_orb': max_orb,
                                'lifecycle': {
                                    'start': cycle['start'].isoformat(),
                                    'end': cycle['end'].isoformat(),
                                    'exact_dates': [
                                        {
                                            'date': ex['date'].isoformat(),
                                            'is_retrograde': ex['is_retrograde']
                                        }
                                        for ex in cycle['exact_dates']
                                    ],
                                    'num_passes': cycle['num_passes'],
                                    'has_retrograde': cycle['has_retrograde']
                                }
                            })

                    except Exception as e:
                        continue

        # מיון לפי תאריך התחלה
        all_aspects.sort(key=lambda x: x['lifecycle']['start'])

        # יצירת תוצאה
        result = {
            'metadata': {
                'user_name': self.user.name,
                'birth_date': self.user.birthdate.isoformat(),
                'range': [start_date.isoformat(), end_date.isoformat()],
                'calculated_at': datetime.now().isoformat(),
                'total_aspects': len(all_aspects)
            },
            'aspects': all_aspects
        }

        return result

    def get_next_events(self, from_date: datetime, days_ahead: int = 30,
                       limit: int = 10) -> list:
        """
        מחזיר את N האירועים הקרובים ביותר.

        :param from_date: תאריך התחלה
        :param days_ahead: כמה ימים קדימה לחפש
        :param limit: מקסימום אירועים להחזיר
        :return: רשימת אירועים ממוינת
        """
        end_date = from_date + timedelta(days=days_ahead)
        result = self.calculate_aspects_in_range(
            from_date, end_date, self.user.location
        )

        events = []

        # איסוף כל האירועים
        for aspect in result['aspects']:
            lifecycle = aspect['lifecycle']

            # אירוע: כניסה לטווח
            if from_date <= datetime.fromisoformat(lifecycle['start']) <= end_date:
                events.append({
                    'date': lifecycle['start'],
                    'event_type': 'ENTERING',
                    'description': f"{aspect['natal_planet']} {aspect['aspect_type']} {aspect['transit_planet']} - כניסה לטווח"
                })

            # אירועים: Exact dates
            for exact in lifecycle['exact_dates']:
                exact_date = datetime.fromisoformat(exact['date'])
                if from_date <= exact_date <= end_date:
                    retro_str = " (R)" if exact['is_retrograde'] else ""
                    events.append({
                        'date': exact['date'],
                        'event_type': 'EXACT',
                        'description': f"{aspect['natal_planet']} {aspect['aspect_type']} {aspect['transit_planet']} - EXACT{retro_str}"
                    })

            # אירוע: יציאה מהטווח
            if from_date <= datetime.fromisoformat(lifecycle['end']) <= end_date:
                events.append({
                    'date': lifecycle['end'],
                    'event_type': 'LEAVING',
                    'description': f"{aspect['natal_planet']} {aspect['aspect_type']} {aspect['transit_planet']} - יציאה מהטווח"
                })

        # מיון לפי תאריך
        events.sort(key=lambda x: x['date'])

        # החזרת limit הראשונים
        return events[:limit]