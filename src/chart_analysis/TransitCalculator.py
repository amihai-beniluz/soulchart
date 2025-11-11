"""
TransitCalculator - מחשבון טרנזיטים עתידיים (גרסה 3.4)
==========================================================
🔧 FIX v3.4: תיקון קריטי - דיוק start/end dates
- במקום להשתמש ב-start_date כנקודת ייחוס למציאת lifecycle של היבט קיים,
  מחפשים אחורה למצוא את cycle_start האמיתי
- משתמשים ב-find_next_aspect_cycle שמתוכנן למצוא cycle חדש קדימה
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
    PLANET_AVG_SPEEDS,
    calculate_orb_at_date
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
        # 🔧 FIX v3.4: חיפוש אחורה למציאת cycle_start האמיתי

        # חישוב מיקומי טרנזיט ב-start_date
        transit_chart = calculate_current_positions(
            start_date, location[0], location[1]
        )
        transit_positions = transit_chart['Planets']

        # חישוב היבטים נוכחיים
        current_aspects = calculate_transit_aspects(
            self.natal_planets, transit_positions
        )

        # עבור כל היבט נוכחי, מצא את ה-cycle המלא
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
            max_orb = aspect['max_orb']

            # יצירת מפתח ייחודי להיבט
            aspect_key = f"{natal_planet}_{transit_planet}_{aspect_name}"

            try:
                # 🔧 FIX v3.4: חפש אחורה למציאת ה-cycle_start האמיתי
                # חישוב מותאם לפי מהירות ממוצעת וזמן הקפה של כל פלנטה

                avg_speed = abs(PLANET_AVG_SPEEDS.get(transit_planet_id, 0.5))

                # חישוב זמן הקפה משוער (כמה ימים לוקח לעבור 360°)
                orbital_period_days = 360.0 / avg_speed if avg_speed > 0 else 365 * 100

                # חישוב טווח חיפוש אחורה - מותאם לפי סוג הפלנטה
                if avg_speed > 5:  # ירח - מהיר מאוד
                    # הירח עובר 360° ב-27 ימים, אז מספיק לחפש שבוע
                    lookback_days = 7

                elif avg_speed > 0.5:  # שמש, מרקורי, ונוס, מאדים
                    # פלנטות מהירות - חפש בהתאם ל-orb פי 2 (לכיסוי נסיגות)
                    lookback_days = (max_orb * 2) / avg_speed
                    lookback_days = min(lookback_days, 120)  # הגבלה: 4 חודשים

                elif avg_speed > 0.05:  # צדק (0.08°/day)
                    # צדק: 360° / 0.08 = ~4500 ימים (12 שנים)
                    # חפש עד 1/3 מזמן ההקפה או max_orb*3, הקטן מביניהם
                    lookback_days = min(
                        (max_orb * 3) / avg_speed,
                        orbital_period_days / 3
                    )
                    lookback_days = min(lookback_days, 365 * 1.5)  # הגבלה: שנה וחצי

                elif avg_speed > 0.01:  # שבתאי (0.03°/day)
                    # שבתאי: 360° / 0.03 = ~12000 ימים (29 שנים)
                    # אורב גדול + תנועה איטית = טווח ארוך
                    lookback_days = min(
                        (max_orb * 6) / avg_speed,
                        orbital_period_days / 4
                    )
                    lookback_days = min(lookback_days, 365 * 3)  # הגבלה: 3 שנים

                else:  # אורנוס, נפטון, פלוטו - איטיים מאוד
                    # אורנוס: 84 שנים, נפטון: 165 שנים, פלוטו: 248 שנים
                    # כאן צריך טווח ארוך כי הנסיגות יכולות ליצור מחזורים של שנים
                    lookback_days = min(
                        (max_orb * 4) / avg_speed,  # פי 4 בגלל נסיגות ארוכות
                        orbital_period_days / 5
                    )
                    lookback_days = min(lookback_days, 365 * 5)  # הגבלה: 5 שנים
                search_start = start_date - timedelta(days=lookback_days)

                # חפש את המחזור שמכיל את start_date
                # נשתמש ב-find_next_aspect_cycle שמתחיל מלפני start_date
                cycle = find_next_aspect_cycle(
                    natal_lon,
                    transit_planet_id,
                    aspect_angle,
                    max_orb,
                    search_start,
                    end_date
                )

                # אם מצאנו cycle, בדוק שהוא אכן מכיל את start_date
                if cycle is not None:
                    cycle_start_dt = datetime.fromisoformat(cycle['start']) if isinstance(cycle['start'], str) else cycle['start']
                    cycle_end_dt = datetime.fromisoformat(cycle['end']) if isinstance(cycle['end'], str) else cycle['end']

                    # ✅ בדיקת תקינות: האם ה-cycle שמצאנו אכן מכיל את start_date?
                    # אם cycle_start הרבה אחרי start_date - פספסנו את ה-cycle האמיתי
                    if cycle_start_dt > start_date + timedelta(days=1):
                        # ⚠️ נראה שפספסנו - ה-cycle מתחיל אחרי start_date
                        # זה יכול לקרות אם lookback_days לא היה מספיק
                        # במקרה כזה, נשתמש ב-calculate_aspect_lifecycle כגיבוי
                        try:
                            lifecycle = calculate_aspect_lifecycle(
                                natal_lon, transit_planet_id, aspect_angle,
                                max_orb, start_date
                            )

                            if lifecycle is not None:
                                cycle = {
                                    'start': lifecycle['start'],
                                    'end': lifecycle['end'],
                                    'exact_dates': lifecycle['exact_dates'],
                                    'num_passes': lifecycle['num_passes'],
                                    'has_retrograde': lifecycle['has_retrograde']
                                }
                        except:
                            pass  # אם גם זה נכשל, נשאר עם cycle המקורי

                    # ודא שה-cycle רלוונטי (מסתיים אחרי start_date)
                    if cycle_end_dt >= start_date:
                        # 🔍 בדיקה נוספת: האם המחזור חופף את הטווח המבוקש?
                        # (למנוע הוספת מחזורים שמסתיימים לפני start_date או מתחילים אחרי end_date)
                        if cycle_start_dt <= end_date:  # המחזור רלוונטי לטווח
                            # המחזור רלוונטי - הוסף אותו
                            all_aspects.append({
                                'natal_planet': natal_planet,
                                'transit_planet': transit_planet,
                                'aspect_type': aspect_name,
                                'max_orb': max_orb,
                                'lifecycle': {
                                    'start': cycle['start'] if isinstance(cycle['start'], str) else cycle['start'].isoformat(),
                                    'end': cycle['end'] if isinstance(cycle['end'], str) else cycle['end'].isoformat(),
                                    'exact_dates': [
                                        {
                                            'date': ex['date'] if isinstance(ex['date'], str) else ex['date'].isoformat(),
                                            'is_retrograde': ex['is_retrograde'],
                                            'actual_orb': ex['actual_orb']
                                        }
                                        for ex in cycle['exact_dates']
                                    ],
                                    'num_passes': cycle['num_passes'],
                                    'has_retrograde': cycle['has_retrograde']
                                }
                            })

                            # שמור שמצאנו את ההיבט הזה
                            existing_aspects_set.add(aspect_key)

            except Exception as e:
                import traceback
                print(f"   ⚠️  שגיאה בחישוב lifecycle ל-{aspect_key}")
                print(f"       פרטי ההיבט: natal_lon={natal_lon:.2f}°, aspect={aspect_name} ({aspect_angle}°)")
                print(f"       תאריך: {start_date.date()}")
                print(f"       שגיאה: {type(e).__name__}: {e}")
                traceback.print_exc()
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
                                    'start': cycle['start'] if isinstance(cycle['start'], str) else cycle['start'].isoformat(),
                                    'end': cycle['end'] if isinstance(cycle['end'], str) else cycle['end'].isoformat(),
                                    'exact_dates': [
                                        {
                                            'date': ex['date'] if isinstance(ex['date'], str) else ex['date'].isoformat(),
                                            'is_retrograde': ex['is_retrograde'],
                                            'actual_orb': ex['actual_orb']
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
