from datetime import datetime
import traceback
import math

from .CalculationEngine import (
    calculate_chart_positions,
    ZODIAC_SIGNS,
    ENG_ZODIAC_SIGNS,
    calculate_current_positions,
    calculate_transit_aspects,
    calculate_aspect_lifecycle,
    check_retrograde_at_date,
    PLANET_IDS_FOR_TRANSIT
)
from .ChartDataLoaders import load_all_chart_data


class ChartAnalysis:
    """
    מבצע ניתוח מפת לידה מלא על בסיס נתוני משתמש, תוך שימוש ב-pyswisseph
    ומיישם את שיטת ניתוח "שזירת השליטים" (6 פרמטרים).
    """

    # מאגר הנתונים הטקסטואליים של הניתוח (נטען פעם אחת)
    chart_data = None

    # מפת שליטים מורחבת (מסורתי + מודרני)
    SIGN_RULERS = {
        'טלה': 'מאדים', 'שור': 'ונוס', 'תאומים': 'מרקורי', 'סרטן': 'ירח',
        'אריה': 'שמש', 'בתולה': 'מרקורי', 'מאזניים': 'ונוס',
        'עקרב': 'פלוטו', 'קשת': 'צדק', 'גדי': 'שבתאי', 'דלי': 'אורנוס', 'דגים': 'נפטון'
    }

    # מפת שמות באנגלית לשליפה ממאגר הנתונים
    PLANET_NAMES_ENG = {
        'שמש': 'Sun', 'ירח': 'Moon', 'מרקורי': 'Mercury',
        'ונוס': 'Venus', 'מאדים': 'Mars', 'צדק': 'Jupiter',
        'שבתאי': 'Saturn', 'אורנוס': 'Uranus', 'נפטון': 'Neptune',
        'פלוטו': 'Pluto', 'ראש דרקון': 'North Node', 'לילית': 'Lilith',
        'כירון': 'Chiron', 'אופק (AC)': 'AC', 'רום שמיים (MC)': 'MC',
        'פורטונה': 'Fortune', 'ורטקס': 'Vertex'
    }

    SIGN_NAMES_ENG = {
        'טלה': 'Aries', 'שור': 'Taurus', 'תאומים': 'Gemini',
        'סרטן': 'Cancer', 'אריה': 'Leo', 'בתולה': 'Virgo',
        'מאזניים': 'Libra', 'עקרב': 'Scorpio', 'קשת': 'Sagittarius',
        'גדי': 'Capricorn', 'דלי': 'Aquarius', 'דגים': 'Pisces'
    }

    HOUSES_NAMES_HEB = [
        'הבית הראשון', 'הבית השני', 'הבית השלישי', 'הבית הרביעי', 'הבית החמישי', 'הבית השישי', 'הבית השביעי',
        'הבית השמיני', 'הבית התשיעי', 'הבית העשירי', 'הבית האחד עשר', 'הבית השנים עשר'
    ]

    HOUSE_NAMES_ENG = [
        'first', 'second', 'third', '4th', '5th', '6th',
        '7th', '8th', '9th', '10th', '11th', '12th'
    ]

    HOUSE_NAMES_ENG_FULL = [
        'First house', 'Second house', 'Third house', 'Fourth house',
        'Fifth house', 'Sixth house', 'Seventh house', 'Eighth house',
        'Ninth house', 'Tenth house', 'Eleventh house', 'Twelfth house'
    ]

    ASPECTS_DICT_HEB = {
        'Conjunction': 'צמוד',
        'Opposition': 'מול',
        'Trine': 'משולש',
        'Square': 'ריבוע',
        'Sextile': 'משושה',
        'Inconjunct': 'קווינקונקס',
        'SemiSextile': 'חצי-משושה',
        'SemiSquare': 'חצי-ריבוע',
        'Sesquiquadrate': 'סקווירפיינד',
        'Quintile': 'קווינטייל',
        'Biquintile': 'ביקווינטייל'
    }

    def __init__(self, user: object):
        self.user = user

        # טעינת נתוני הניתוח האסטרולוגיים פעם אחת
        if ChartAnalysis.chart_data is None:
            ChartAnalysis.chart_data = load_all_chart_data()

    def get_raw_chart_data(self) -> dict:
        """מחזיר את נתוני המפה המלאים (ללא הניתוח הטקסטואלי)"""
        return self.chart_data

    def get_sign_from_degree(self, degree: float) -> str:
        """ ממיר מעלה לזיהוי מזל. """
        # וידוא שהערך הוא מספר
        if isinstance(degree, (list, tuple)):
            degree = float(degree[0])
        degree = float(degree) % 360
        return ZODIAC_SIGNS[int(degree // 30)]

    def get_eng_sign_from_degree(self, degree: float) -> str:
        """ ממיר מעלה לזיהוי מזל באנגלית. """
        # וידוא שהערך הוא מספר
        if isinstance(degree, (list, tuple)):
            degree = float(degree[0])
        degree = float(degree) % 360
        return ENG_ZODIAC_SIGNS[int(degree // 30)]

    def is_sign_intercepted(self, house_cusps: list, sign: str) -> bool:
        """
        בדיקה בסיסית של מזל כלוא: מזל כלוא הוא מזל שאין בו קו יתד של בית.
        """
        try:
            cusp_signs = []
            for i in range(1, 13):
                c = house_cusps[i]
                if isinstance(c, (list, tuple)):
                    c = float(c[0])
                else:
                    c = float(c)
                cusp_signs.append(self.get_sign_from_degree(c))

            return sign not in cusp_signs
        except Exception:
            return False


    def _format_positions_report(self, planets_data: dict, title: str, include_house: bool = True) -> list:
        """מעצבת דוח מיקומי כוכבים (נטאלי או טרנזיט)."""
        report = [
            f"\n{'=' * 80}",
            f"{title}",
            f"{'=' * 80}",
            "\n* מיקומי כוכבים ונקודות:\n"
        ]

        # הרשימה כוללת גופים רלוונטיים בלבד
        reportable_planets = [
            'שמש', 'ירח', 'מרקורי', 'ונוס', 'מאדים', 'צדק',
            'שבתאי', 'אורנוס', 'נפטון', 'פלוטו', 'ראש דרקון', 'לילית', 'כירון',
            'אופק (AC)', 'רום שמיים (MC)', 'פורטונה', 'ורטקס'
        ]

        for name in reportable_planets:
            if name in planets_data and 'lon_deg' in planets_data[name] and planets_data[name]['lon_deg'] is not None:
                pos = planets_data[name]

                # חישוב מעלה ודקה
                lon_deg = pos['lon_deg']
                degree = math.floor(lon_deg) % 30
                minute = int((lon_deg % 1) * 60)

                sign_heb = pos['sign']

                # ✅ תיקון: הצג (R) גם כשאין בתים (טרנזיט)
                retro_str = " (R)" if pos.get('is_retrograde') else ""

                formatted_position = f"{degree:02d}°{minute:02d}' ב{sign_heb}{retro_str}"

                line = f"    - {name:<10}: {formatted_position}"

                # רק במפות נטאליות יש בתים
                if include_house and pos.get('house') is not None:
                    line += f" (בית {pos['house']})"

                report.append(line)

        report.append("\n")
        return report

    def _format_aspects_report(self, aspects_list: list, title: str, is_interpreted=False,
                               is_natal_only: bool = False) -> list:
        """מעצבת דוח היבטים (נטאל-נטאל או נטאל-טרנזיט)."""
        report = [
            f"\n{'=' * 80}",
            f"{title}",
            f"{'=' * 80}",
            "\n"
        ]

        if not aspects_list:
            report.append("אין היבטים משמעותיים שנמצאו.")
            return report

        # ✅ עבור טרנזיטים - השתמש ב-lifecycle שכבר קיים!
        if not is_natal_only:
            from datetime import datetime

            # ✅ ללא חישוב מחדש - רק מיון וסינון
            aspects_with_lifecycle = []

            for aspect in aspects_list:
                # 🎯 קבל את ה-lifecycle שכבר חושב
                lifecycle = aspect.get('lifecycle')

                # אם אין lifecycle (fallback למקרים ישנים)
                if lifecycle is None:
                    # רק במקרה זה - חשב (fallback)
                    try:
                        p1_heb = aspect['planet1']
                        p2_heb = aspect['planet2']

                        natal_planets = aspect.get('natal_planets_data')
                        if natal_planets:
                            p1_natal_lon = natal_planets[p1_heb]['lon_deg']
                            transit_planet_id = PLANET_IDS_FOR_TRANSIT.get(p2_heb)

                            if transit_planet_id is not None:
                                lifecycle = calculate_aspect_lifecycle(
                                    p1_natal_lon,
                                    transit_planet_id,
                                    aspect['exact_angle'],
                                    aspect.get('max_orb', 0.5),
                                    datetime.now()
                                )
                    except Exception as e:
                        print(f"⚠️ שגיאה בחישוב lifecycle fallback: {e}")
                        lifecycle = None

                # המרת lifecycle מISO strings ל-datetime אם נדרש
                if lifecycle and isinstance(lifecycle.get('start'), str):
                    lifecycle = {
                        'start': datetime.fromisoformat(lifecycle['start']),
                        'end': datetime.fromisoformat(lifecycle['end']),
                        'exact_dates': [
                            {
                                'date': datetime.fromisoformat(ex['date']),
                                'is_retrograde': ex['is_retrograde']
                            }
                            for ex in lifecycle['exact_dates']
                        ],
                        'num_passes': lifecycle['num_passes'],
                        'has_retrograde': lifecycle['has_retrograde']
                    }

                # חישוב משך זמן
                lifecycle_seconds = float('inf')
                if lifecycle and lifecycle.get('start') and lifecycle.get('end'):
                    lifecycle_seconds = (lifecycle['end'] - lifecycle['start']).total_seconds()

                aspects_with_lifecycle.append({
                    'aspect': aspect,
                    'lifecycle': lifecycle,
                    'duration_seconds': lifecycle_seconds
                })

            # ✅ הוסף כאן - סינון היבטים לא רלוונטיים
            current_time = datetime.now()

            # סנן רק היבטים שרלוונטיים עכשיו
            active_aspects = []
            for item in aspects_with_lifecycle:
                lifecycle = item['lifecycle']

                # אם אין lifecycle - השאר את ההיבט (fallback)
                if lifecycle is None:
                    active_aspects.append(item)
                    continue

                # אם יש lifecycle - בדוק אם ההיבט עדיין פעיל
                if lifecycle['start'] and lifecycle['end']:
                    # היבט פעיל אם אנחנו בטווח הזמן שלו
                    if lifecycle['start'] <= current_time <= lifecycle['end']:
                        active_aspects.append(item)
                    # או אם ההיבט עדיין לא התחיל (מקרה עתידי)
                    elif current_time < lifecycle['start']:
                        active_aspects.append(item)
                    # אחרת - ההיבט כבר נגמר, לא מוסיפים אותו
                else:
                    # אין תאריכים - השאר את ההיבט
                    active_aspects.append(item)

            # מיון לפי משך זמן (רק של ההיבטים הפעילים)
            active_aspects.sort(key=lambda x: x['duration_seconds'])

            # מיון לפי משך זמן
            aspects_with_lifecycle.sort(key=lambda x: x['duration_seconds'])

            # עכשיו עובדים עם הרשימה הממוינת והמסוננת
            for item in active_aspects:  # ← שינוי כאן!
                aspect = item['aspect']
                lifecycle = item['lifecycle']

                p1_heb = aspect['planet1']
                p2_heb = aspect['planet2']
                aspect_heb = self.ASPECTS_DICT_HEB.get(aspect['aspect_name_eng'], aspect['aspect_name_eng'])
                orb = aspect['orb']

                is_transit_aspect = True  # כי אנחנו בטרנזיטים

                max_orb_value = aspect.get('max_orb', 0.5)
                strength_indicator = self._calculate_aspect_strength(orb, max_orb_value)

                # חישוב progress (עם lifecycle שכבר קיים)
                progress_indicator = self._calculate_transit_progress(aspect, lifecycle)

                # בניית התצוגה
                lifecycle_str = ""
                exact_str = ""

                if lifecycle and lifecycle['start'] is not None:
                    duration_str = self._format_duration(lifecycle['start'], lifecycle['end'])

                    lifecycle_str = (
                        f"    - תקופת פעילות: {lifecycle['start']:%d.%m.%Y %H:%M} - "
                        f"{lifecycle['end']:%d.%m.%Y %H:%M} ({duration_str}"
                    )

                    if lifecycle['num_passes'] > 1:
                        lifecycle_str += f", {lifecycle['num_passes']} מעברים"
                    lifecycle_str += ")"

                    if lifecycle['exact_dates']:
                        exact_parts = []
                        for ex in lifecycle['exact_dates']:
                            retro_marker = " ⟲" if ex['is_retrograde'] else ""
                            exact_parts.append(f"{ex['date']:%d.%m.%Y %H:%M}{retro_marker}")

                        exact_str = f"    - שיא ההיבט: {', '.join(exact_parts)}"

                # הדפסה
                p1_type_str = " (לידה)"
                p2_type_str = " (מעבר)"

                report.append(f"{p1_heb}{p1_type_str} {aspect_heb} {p2_heb}{p2_type_str}")
                report.append(f"    - התקדמות: {progress_indicator}")
                report.append(f"    - עוצמה: {strength_indicator}")
                report.append(f"    - אורב נוכחי: {orb:.2f}° (מתוך: {max_orb_value:.2f}°)")

                if lifecycle_str:
                    report.append(lifecycle_str)
                if exact_str:
                    report.append(exact_str)

                if is_interpreted:
                    # לוגיקת הפרשנות
                    if is_natal_only:
                        # פרשנות נטאל-נטאל (ממאגר 'aspects')
                        aspects_data = self.chart_data.get('aspects', {})
                        p1_eng = self.PLANET_NAMES_ENG[p1_heb]
                        p2_eng = self.PLANET_NAMES_ENG[p2_heb]
                        aspect_name_eng = aspect['aspect_name_eng']

                        # לוגיקת שליפת מפתח מורכבת
                        aspect_name_normalized = aspect_name_eng.replace('-', '')
                        key_1 = f"{p1_eng} {aspect_name_normalized} {p2_eng}"
                        key_2 = f"{p2_eng} {aspect_name_normalized} {p1_eng}"
                        analysis = aspects_data.get(key_1)
                        if not analysis: analysis = aspects_data.get(key_2)
                        if not analysis and aspect_name_normalized != aspect_name_eng:
                            key_1_dashed = f"{p1_eng} {aspect_name_eng} {p2_eng}"
                            key_2_dashed = f"{p2_eng} {aspect_name_eng} {p1_eng}"
                            analysis = aspects_data.get(key_1_dashed)
                            if not analysis: analysis = aspects_data.get(key_2_dashed)
                        if not analysis:
                            analysis = f"❌ ניתוח היבט זה לא נמצא במאגר: {key_1} / {key_2}"

                    elif is_transit_aspect:
                        # פרשנות מעבר-לידה (ממאגר 'aspects_transit')
                        p1_eng = aspect.get('p1_eng_name') or self.PLANET_NAMES_ENG[p1_heb]
                        p2_eng = aspect.get('p2_eng_name') or self.PLANET_NAMES_ENG[p2_heb]
                        aspect_name = aspect['aspect_name_eng']
                        key = f"Natal {p1_eng} {aspect_name} Transit {p2_eng}"
                        aspects_data = self.chart_data.get('aspects_transit', {})
                        analysis = aspects_data.get(key)
                        if not analysis:
                            analysis = f"❌ ניתוח היבט זה לא נמצא במאגר: {key}"
                    else:
                        analysis = "❌ לא ניתן למצוא ניתוח - סוג ההיבט לא הוגדר כראוי."

                    report.append(f"\n{analysis}\n")
                    if aspect != aspects_list[-1]:
                        report.append("-" * 80)
                    report.append("")

                report.append("")

        else:
            # אם מחשבים עבור מפת לידה בלבד
            for aspect in aspects_list:
                p1_heb = aspect['planet1']
                p2_heb = aspect['planet2']
                # פרשנות נטאל-נטאל (ממאגר 'aspects')
                aspects_data = self.chart_data.get('aspects', {})
                p1_eng = self.PLANET_NAMES_ENG[p1_heb]
                p2_eng = self.PLANET_NAMES_ENG[p2_heb]
                aspect_name_eng = aspect['aspect_name_eng']
                # לוגיקת שליפת מפתח מורכבת
                aspect_name_normalized = aspect_name_eng.replace('-', '')
                key_1 = f"{p1_eng} {aspect_name_normalized} {p2_eng}"
                key_2 = f"{p2_eng} {aspect_name_normalized} {p1_eng}"
                report.append(key_1)
                if is_interpreted:
                    analysis = aspects_data.get(key_1)
                    if not analysis:
                        analysis = aspects_data.get(key_2)
                    if not analysis and aspect_name_normalized != aspect_name_eng:
                        key_1_dashed = f"{p1_eng} {aspect_name_eng} {p2_eng}"
                        key_2_dashed = f"{p2_eng} {aspect_name_eng} {p1_eng}"
                        analysis = aspects_data.get(key_1_dashed)
                        if not analysis: analysis = aspects_data.get(key_2_dashed)
                    if not analysis:
                        analysis = f"❌ ניתוח היבט זה לא נמצא במאגר: {key_1} / {key_2}"
                    report.append(f"\n{analysis}")
                    if aspect != aspects_list[-1]:
                        report.append("-" * 80)
                    report.append("")


        report.append("\n")
        return report

    def analyze_transits_and_aspects(self, current_location: tuple, is_interpreted=False) -> list:
        """
        מבצע השוואה בין מפת הלידה (נטאלית) למיקומי הכוכבים הנוכחיים (מעבר/טרנזיט).
        """
        current_lat, current_lon = current_location

        if not self.user.location or not self.user.birthtime:
            return [f"❌ אין מספיק נתונים לחישוב מדויק (חסרים שעה ו/או מיקום לידה)."]

        birth_datetime = datetime.combine(self.user.birthdate, self.user.birthtime)
        now = datetime.now()

        # 1. חישוב נתוני מפת הלידה (נטאלי)
        try:
            natal_chart_positions = calculate_chart_positions(
                birth_datetime,
                self.user.location[0],
                self.user.location[1]
            )
        except Exception as e:
            return [f"❌ שגיאה בחישוב המפה הלידתית: {e}"]

        # 2. חישוב מיקומי כוכבים נוכחיים (מעבר/טרנזיט)
        try:
            transit_chart_positions = calculate_current_positions(
                now,
                current_lat,
                current_lon
            )
        except Exception as e:
            return [f"❌ שגיאה בחישוב מיקומי המעבר הנוכחיים: {e}"]

        # 3. חישוב היבטים בין נטאל למעבר (Bi-wheel Aspects)
        try:
            transit_aspects_list = calculate_transit_aspects(
                natal_chart_positions['Planets'],
                transit_chart_positions['Planets'],
            )
            for aspect in transit_aspects_list:
                aspect['natal_planets_data'] = natal_chart_positions['Planets']

        except Exception as e:
            print(f"⚠️ אזהרה: שגיאה בחישוב היבטי מעבר: {e}. ממשיכים ללא היבטים.")
            transit_aspects_list = []

        report = [
            f"=== ניתוח מעברים (טרנזיטים) עבור {self.user.name} ({self.user.birthdate}) - נכון לתאריך: {now.strftime('%Y-%m-%d %H:%M')} ({current_lat:.2f}, {current_lon:.2f}) ==="]

        # 4. עיצוב הדוחות
        # דוח נטאל (כולל בתים)
        report.extend(self._format_positions_report(
            natal_chart_positions['Planets'],
            "1. מיקומי כוכבי הלידה (לידתי)",
            include_house=True
        ))

        # דוח טרנזיט (ללא בתים)
        report.extend(self._format_positions_report(
            transit_chart_positions['Planets'],
            "2. מיקומי כוכבים נוכחיים (מעבר / טרנזיט)",
            include_house=False
        ))

        # דוח היבטים
        report.extend(self._format_aspects_report(
            transit_aspects_list,
            "3. היבטים נוצרים בין כוכבי מעבר ללידה (טרנזיטים)",
            is_interpreted,
            is_natal_only=False
        ))

        return report

    def _fetch_analysis(self, category: str, key: str, default_message: str = "❌ ניתוח זה לא נמצא במאגר") -> str:
        """ פונקציית עזר לשליפת ניתוח מהמאגר הטקסטואלי """
        data_source = self.chart_data.get(category, {})
        analysis = data_source.get(key, default_message)
        return analysis

    def _normalize_key(self, key: str) -> str:
        """ מנרמל מפתח חיפוש אנגלי: מסיר רווחים מיותרים ומקפים. """
        # נירמול רווחים פנימיים והסרת רווחים חיצוניים
        normalized = " ".join(key.split()).strip()
        # הסרת מקפים (כפי שנעשה ב-DataLoaders)
        return normalized.replace('-', '')

    def _fetch_analysis(self, category: str, key: str, default_message: str = "❌ ניתוח זה לא נמצא במאגר") -> str:
        """ פונקציית עזר לשליפת ניתוח מהמאגר הטקסטואלי """
        # 🚀 FIX: נירמול המפתח לפני השליפה
        normalized_key = self._normalize_key(key)
        data_source = self.chart_data.get(category, {})
        analysis = data_source.get(normalized_key, default_message)
        return analysis

    def analyze_chart(self, is_interpreted: bool = True) -> list:
        """
        מבצע חישוב וניתוח מלא של מפת הלידה ומשלב את ניתוח השליטים.
        כאשר is_interpreted=False, הפלט יחזיר רק את מיקומי הפלנטות והיבטים ללא פרשנות טקסטואלית נרחבת.
        """

        # 1. ודא שיש מספיק נתונים
        if not self.user.location or not self.user.birthtime:
            return [f"❌ אין מספיק נתונים לחישוב מפת לידה מדויקת (חסרים שעה ו/או מיקום)."]

        # 2. חישוב מיקומי הכוכבים והבתים
        birth_datetime = datetime.combine(self.user.birthdate, self.user.birthtime)

        try:
            chart_positions = calculate_chart_positions(
                birth_datetime,
                self.user.location[0],  # Latitude
                self.user.location[1]  # Longitude
            )
        except Exception as e:
            print(f"❌ שגיאה בחישוב המפה האסטרולוגית: {e}")
            traceback.print_exc()
            return [f"❌ שגיאה בחישוב המפה האסטרולוגית: {e}"]

        report = [f"=== ניתוח מפת לידה עבור {self.user.name} ({self.user.birthdate}) ==="]

        # נתוני המפה המחושבים
        planets_data = chart_positions['Planets']
        cusps = chart_positions['HouseCusps']
        aspects_list = chart_positions['Aspects']

        # ----------------------------------------------------------------------
        # 1. דוח מיקומי כוכבים
        # ----------------------------------------------------------------------
        report.extend(self._format_positions_report(
            planets_data,
            "מיקומי כוכבי הלידה (נטאלי)",
            include_house=True
        ))

        if not is_interpreted:
            # ----------------------------------------------------------------------
            # דוח היבטים
            # ----------------------------------------------------------------------
            report.extend(self._format_aspects_report(
                aspects_list,
                "היבטים בין כוכבי הלידה (נטאליים)",
                is_interpreted=False,  # משתמש בדגל כדי לשלוט האם להדפיס פרשנות
                is_natal_only=True  # מורה על פורמט נקי ללא סוג המפה בסוגריים
            ))
            # אם is_interpreted=False, אנו מסיימים כאן.
            return report

        # ----------------------------------------------------------------------
        # הניתוח המלא (רק אם is_interpreted = True)
        # ----------------------------------------------------------------------

        # השמש הירח והאופק האסטרולוגי
        report.append("")
        report.append("\n" + "=" * 80)
        report.append("השמש הירח והאופק העולה")
        report.append("=" * 80)
        report.append("")

        ascendant_degree = cusps[1]
        heb_ascendant_sign = self.get_sign_from_degree(ascendant_degree)
        heb_sun_sign = planets_data["שמש"]['sign']
        heb_moon_sign = planets_data["ירח"]['sign']

        sun_moon_ascendant_key = f"Sun in {self.SIGN_NAMES_ENG[heb_sun_sign]} Moon in " \
                                 f"{self.SIGN_NAMES_ENG[heb_moon_sign]} " \
                                 f"and {self.SIGN_NAMES_ENG[heb_ascendant_sign]} ascendant"
        sun_moon_ascendant_title = f"שמש ב{heb_sun_sign} ירח ב{heb_moon_sign} ואופק ב{heb_ascendant_sign}"
        report.append(sun_moon_ascendant_title + "\n")
        sun_moon_ascendant_analysis = self._fetch_analysis('sun_moon_ascendant', sun_moon_ascendant_key,
                                                           f"ניתוח {sun_moon_ascendant_title} לא נמצא.")
        report.append(f"{sun_moon_ascendant_analysis}")

        # מיקומי הבתים והכוכבים במזלות
        report.append("")
        report.append("\n" + "=" * 80)
        report.append("מיקומי הבתים והכוכבים במזלות")
        report.append("=" * 80 + "\n")
        report.append("")

        for h in range(1, 13):
            cusp_degree = cusps[h]
            cusp_sign = self.get_sign_from_degree(cusp_degree)
            eng_cusp_sign = self.get_eng_sign_from_degree(cusp_degree)
            heb_house = self.HOUSES_NAMES_HEB[h - 1]
            ruler = self.SIGN_RULERS.get(cusp_sign)

            house_in_sign_key = f"{self.HOUSE_NAMES_ENG_FULL[h - 1]} in {eng_cusp_sign}"
            # ניתוח הבית
            house_analysis = self._fetch_analysis('houses', heb_house, f"ניתוח {heb_house[1:]} לא נמצא.")

            # ניתוח מזל הבית (הסגנון החיצוני)
            sign_analysis = self._fetch_analysis('signs', cusp_sign, f"ניתוח מזל {cusp_sign} לא נמצא.")

            # ניתוח מיקום הבית במזלות
            house_in_sign_analysis = self._fetch_analysis('house_in_sign', house_in_sign_key,
                                                          f"ניתוח {heb_house[1:]} ב{cusp_sign} לא נמצא.")

            # בדיקת מזל כלוא
            is_intercepted = self.is_sign_intercepted(cusps, cusp_sign)
            intercepted_str = " (מזל כלוא)" if is_intercepted else ""

            # house
            report.append(f"בית {h}\n")
            report.append(house_analysis + "\n")
            report.append("")
            # sign
            report.append(f"מזל {cusp_sign}\n")
            report.append(f"{sign_analysis}\n")
            report.append("")
            # house in sign
            report.append(f"{heb_house} ב{cusp_sign}{intercepted_str}\n")
            report.append(f"{house_in_sign_analysis}\n")
            report.append("")

            for planet, data in planets_data.items():
                if data['house'] != h:
                    continue
                if planet in ['אופק (AC)', 'רום שמיים (MC)']:
                    continue
                planet_sign = data['sign']
                is_retro = data['is_retrograde']
                is_inter = self.is_sign_intercepted(cusps, planet_sign)
                is_retro_str = " retrograde" if is_retro else ""
                is_inter_str = " intercepted" if is_inter else ""

                # מפתחות לניתוחים הפשוטים (כבר נקיים, אבל עדיין עברו דרך _normalize_key ב-_fetch_analysis)
                planet_in_house_key = f"{self.PLANET_NAMES_ENG[planet]} in {self.HOUSE_NAMES_ENG_FULL[h - 1]}"
                planet_in_sign_key = f"{self.PLANET_NAMES_ENG[planet]} in {self.SIGN_NAMES_ENG[planet_sign]}"

                # המפתח המורכב (שבו הייתה כנראה הבעיה הגדולה ביותר של רווחים)
                raw_planet_house_sign_key = (
                    f"{self.PLANET_NAMES_ENG[planet]}{is_retro_str} in "
                    f"{self.HOUSE_NAMES_ENG_FULL[h - 1]} in "
                    f"{self.SIGN_NAMES_ENG[planet_sign]}{is_inter_str}"
                )

                # 🚀 FIX: שימוש בפונקציית הנירמול כדי לוודא שאין רווחים מיותרים בין ה-"retrograde"/"intercepted" לשאר הטקסט
                planet_house_sign_key = self._normalize_key(raw_planet_house_sign_key)
                # planet
                planet_analysis = self._fetch_analysis('planets', planet, f"ניתוח {planet} לא נמצא.")
                report.append(f"{planet}\n")
                report.append(f"{planet_analysis}\n")
                report.append("")
                # planet in house
                planet_in_house_analysis = self._fetch_analysis('planet_in_house', planet_in_house_key,
                                                                f"ניתוח {planet} ב{heb_house[1:]} לא נמצא.")
                report.append(f"{planet} ב{heb_house[1:]}\n")
                report.append(f"{planet_in_house_analysis}\n")
                report.append("")
                # planet in sign
                planet_in_sign_analysis = self._fetch_analysis('planet_in_sign', planet_in_sign_key,
                                                               f"ניתוח {planet} ב{planet_sign} לא נמצא.")
                report.append(f"{planet} ב{planet_sign}\n")
                report.append(f"{planet_in_sign_analysis}\n")
                report.append("")
                # planet in house in sign
                planet_house_sign_analysis = self._fetch_analysis('planet_house_sign', planet_house_sign_key,
                                                                  f"ניתוח {planet} ב{heb_house[1:]} ב{planet_sign}{is_inter_str}{is_retro_str} לא נמצא.")
                report.append(f"{planet} ב{heb_house[1:]} ב{planet_sign}{is_inter_str}{is_retro_str}\n")
                report.append(f"{planet_house_sign_analysis}\n")
                report.append("")

            try:
                h2h_data = self.chart_data.get('house_to_house', {})
                # א+ב. בחירת הבית ומציאת המזל בו ממוקם הבית
                if ruler not in planets_data:
                    report.append(f"\n⚠️ אזהרה: השליט של בית {h} ({ruler}) אינו מחושב במפה.\n")
                    continue

                # ג. מציאת מיקום הכוכב השולט בבתים
                ruler_house = planets_data[ruler]['house']
                # ד. מציאת מיקום הכוכב הנ"ל במזלות
                ruler_sign = planets_data[ruler]['sign']
                # ה. האם המזל שבו ממוקם הכוכב השולט הוא כלוא?
                is_ruler_sign_intercepted = self.is_sign_intercepted(cusps, ruler_sign)
                # ו. האם הכוכב בנסיגה?
                is_ruler_retrograde = planets_data[ruler]['is_retrograde']

                # --- בניית מפתח שליפה מדויק ---
                is_retro_str = 'which is retrograde ' if is_ruler_retrograde else ''
                is_intercepted_str = ' which is intercepted' if is_ruler_sign_intercepted else ''
                is_intercepted_heb_str = 'הכלוא ' if is_ruler_sign_intercepted else ''
                house_name = self.HOUSE_NAMES_ENG[h - 1]
                ruler_eng = self.PLANET_NAMES_ENG.get(ruler, ruler)
                cusp_sign_eng = self.SIGN_NAMES_ENG.get(cusp_sign, cusp_sign)
                ruler_sign_eng = self.SIGN_NAMES_ENG.get(ruler_sign, ruler_sign)

                analysis_key = (
                    f"{house_name} house is in {cusp_sign_eng} "
                    f"when its ruler - {ruler_eng} {is_retro_str}- "
                    f"is in the {self.HOUSE_NAMES_ENG[ruler_house - 1]} house "
                    f"and in {ruler_sign_eng}{is_intercepted_str}"
                )

                ruler_analysis = h2h_data.get(analysis_key,
                                              f"❌ ניתוח מפתח זה לא נמצא במאגר")

                report.append(
                    f"{heb_house} ב{cusp_sign} ושליט הבית ({ruler}) ממוקם בבית {ruler_house} ובמזל {is_intercepted_heb_str}{ruler_sign}")
                report.append(f"{ruler_analysis}\n")
                # report.append("-" * 80)

            except Exception as e:
                report.append(f"\n⚠️ שגיאה בניתוח בית {h}: {e}\n")

            report.append("")
            if h != 12:
                report.append("-" * 80 + "\n")
                report.append("")

        # ----------------------------------------------------------------------
        # דוח היבטים
        # ----------------------------------------------------------------------
        report.extend(self._format_aspects_report(
            aspects_list,
            "היבטים בין כוכבי הלידה (נטאליים)",
            is_interpreted=True,  # משתמש בדגל כדי לשלוט האם להדפיס פרשנות
            is_natal_only=True  # מורה על פורמט נקי ללא סוג המפה בסוגריים
        ))

        return report

    # TODO: להוסיף תצוגת לוח שנה שבה מסומן כל היבט.
    def _calculate_transit_progress(self, aspect: dict, lifecycle: dict = None) -> str:
        """
        מחשב את מחוון ההתקדמות הלינארי של היבט מעבר בתוך האורב.
        תומך גם במחזורים מורכבים עם נסיגות.

        :param aspect: מילון ההיבט
        :param lifecycle: (אופציונלי) נתוני מחזור החיים שכבר חושבו
        :return: מחרוזת עם מחוון ויזואלי
        """
        import math
        from datetime import datetime

        p2_is_retrograde = aspect.get('p2_is_retrograde', False)

        # אם יש נתוני lifecycle - נשתמש בהם לחישוב מדויק יותר
        if lifecycle and lifecycle.get('has_retrograde') and lifecycle.get('exact_dates'):
            return self._calculate_complex_progress(lifecycle, datetime.now())

        # ✅ תיקון: חישוב לפי זמן בפועל במקום אורב
        if lifecycle and lifecycle.get('start') and lifecycle.get('end'):
            cycle_start = lifecycle['start']
            cycle_end = lifecycle['end']
            exact_dates = lifecycle.get('exact_dates', [])
            current_date = datetime.now()

            # חישוב התקדמות לפי זמן
            total_seconds = (cycle_end - cycle_start).total_seconds()
            elapsed_seconds = (current_date - cycle_start).total_seconds()

            if total_seconds > 0:
                percent = (elapsed_seconds / total_seconds) * 100
            else:
                percent = 50.0

            # קביעת סטטוס (מתחזק/נחלש) לפי מיקום ביחס ל-Exact
            if exact_dates and len(exact_dates) > 0:
                exact_date = exact_dates[0]['date']
                if current_date < exact_date:
                    status_text = "מתחזק"
                else:
                    status_text = "נחלש"
            else:
                # אם אין Exact - השתמש בלוגיקה הישנה
                is_approaching = aspect.get('is_approaching', True)
                status_text = "מתחזק" if is_approaching else "נחלש"

            percent = max(0.0, min(100.0, percent))
            num_blocks = math.floor(percent / 10)
            progress_bar = "█" * num_blocks + "░" * (10 - num_blocks)

            return f"[{progress_bar}] {percent:.1f}% ({status_text})"

        # Fallback: חישוב פשוט אם אין נתוני lifecycle
        current_orb = aspect['orb']
        max_orb = aspect.get('max_orb', 0.5)
        is_approaching = aspect.get('is_approaching', True)

        if max_orb <= 0.001:
            return "[██████████] 100.0% (מדויק)"

        # חישוב אחוז התקדמות לפי מחזור החיים השלם
        if is_approaching:
            status_text = "מתחזק"
            # מתקרב: מ-max_orb ל-0° = מ-0% ל-50%
            percent = ((max_orb - current_orb) / max_orb) * 50
        else:
            status_text = "נחלש"
            # מתרחק: מ-0° ל-max_orb = מ-50% ל-100%
            percent = 50 + (current_orb / max_orb) * 50

        percent = max(0.0, min(100.0, percent))
        num_blocks = math.floor(percent / 10)
        progress_bar = "█" * num_blocks + "░" * (10 - num_blocks)

        return f"[{progress_bar}] {percent:.1f}% ({status_text})"

    def _calculate_complex_progress(self, lifecycle: dict, current_date) -> str:
        """
        מחשב התקדמות עבור מחזור מורכב עם נסיגות (מספר Exacts).

        :param lifecycle: נתוני מחזור החיים
        :param current_date: התאריך הנוכחי
        :return: מחרוזת עם מחוון ויזואלי
        """
        import math
        from datetime import datetime

        cycle_start = lifecycle['start']
        cycle_end = lifecycle['end']
        exact_dates = lifecycle['exact_dates']

        # אם אין Exacts - fallback לחישוב פשוט
        if not exact_dates:
            total_seconds = (cycle_end - cycle_start).total_seconds()
            elapsed_seconds = (current_date - cycle_start).total_seconds()
            percent = (elapsed_seconds / total_seconds) * 100 if total_seconds > 0 else 50
            percent = max(0.0, min(100.0, percent))
            num_blocks = math.floor(percent / 10)
            progress_bar = "█" * num_blocks + "░" * (10 - num_blocks)
            return f"[{progress_bar}] {percent:.1f}% (במחזור)"

        # יש Exacts - חלק את המחזור לסגמנטים
        num_exacts = len(exact_dates)

        # בנה רשימת גבולות: [start, exact1, exact2, ..., exactN, end]
        boundaries = [cycle_start] + [ex['date'] for ex in exact_dates] + [cycle_end]

        # מצא באיזה סגמנט אנחנו נמצאים
        current_segment = 0
        for i in range(len(boundaries) - 1):
            if boundaries[i] <= current_date <= boundaries[i + 1]:
                current_segment = i
                break

        # חשב את האחוז בסגמנט הנוכחי
        seg_start = boundaries[current_segment]
        seg_end = boundaries[current_segment + 1]

        seg_total_seconds = (seg_end - seg_start).total_seconds()
        seg_elapsed_seconds = (current_date - seg_start).total_seconds()

        if seg_total_seconds > 0:
            seg_progress = seg_elapsed_seconds / seg_total_seconds
        else:
            seg_progress = 0.5

        # חשב את האחוז הכולל
        # כל סגמנט תופס חלק שווה מ-0 עד 100
        segment_size = 100.0 / (num_exacts + 1)  # +1 כי יש num_exacts+1 סגמנטים
        percent = (current_segment * segment_size) + (seg_progress * segment_size)

        # קבע את הכיוון (מתחזק/נחלש)
        # אם אנחנו לפני Exact - מתחזק, אחרי Exact - נחלש
        if current_segment < len(exact_dates):
            # יש Exact לפנינו
            next_exact = exact_dates[current_segment]['date']
            if current_date < next_exact:
                status = "מתחזק"
            else:
                status = "נחלש"
        else:
            # עברנו את כל ה-Exacts
            status = "נחלש"

        percent = max(0.0, min(100.0, percent))
        num_blocks = math.floor(percent / 10)
        progress_bar = "█" * num_blocks + "░" * (10 - num_blocks)

        return f"[{progress_bar}] {percent:.1f}% ({status}, מחזור מורכב)"

    def _calculate_aspect_strength(self, current_orb: float, max_orb: float) -> str:
        """
        מחשב עוצמה של היבט על בסיס האורב הנוכחי בלבד.
        0° = 100% עוצמה (מדויק), max_orb = 0% עוצמה (קצה הטווח)
        """
        import math

        if max_orb <= 0.001:
            return "[██████████] 100.0%"

        # חישוב אחוז העוצמה: ככל שהאורב קטן יותר, העוצמה גבוהה יותר
        strength_percent = ((max_orb - current_orb) / max_orb) * 100
        strength_percent = max(0.0, min(100.0, strength_percent))

        # בניית מחוון ויזואלי (10 בלוקים)
        num_blocks = math.floor(strength_percent / 10)
        strength_bar = "█" * num_blocks + "░" * (10 - num_blocks)

        return f"[{strength_bar}] {strength_percent:.1f}%"

    def _format_duration(self, start: datetime, end: datetime) -> str:
        """
        ממיר משך זמן לפורמט קריא (שנים/ימים/שעות).

        :param start: תאריך התחלה
        :param end: תאריך סיום
        :return: מחרוזת בפורמט "X שנים" / "Y ימים" / "Z שעות"
        """
        from datetime import datetime

        # אם start ו-end הם מחרוזות ISO - המר ל-datetime
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if isinstance(end, str):
            end = datetime.fromisoformat(end)

        # חישוב ההפרש
        total_seconds = (end - start).total_seconds()
        total_hours = total_seconds / 3600
        total_days = total_seconds / (3600 * 24)
        total_years = total_days / 365.25  # שנה ממוצעת כולל שנים מעוברות

        # החלטה לפי הזמן
        if total_years >= 1:
            # הצג שנים
            years = total_years
            if years >= 2:
                return f"{years:.1f} שנים"
            else:
                return f"{years:.1f} שנה"
        elif total_days >= 1:
            # הצג ימים
            days = int(total_days)
            if days == 1:
                return "יום אחד"
            elif days == 2:
                return "יומיים"
            else:
                return f"{days} ימים"
        else:
            # הצג שעות
            hours = int(total_hours)
            if hours == 0:
                minutes = int(total_seconds / 60)
                return f"{minutes} דקות"
            elif hours == 1:
                return "שעה אחת"
            elif hours == 2:
                return "שעתיים"
            else:
                return f"{hours} שעות"