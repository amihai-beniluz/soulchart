from datetime import datetime
import traceback
import math

from .CalculationEngine import calculate_chart_positions, ZODIAC_SIGNS, ENG_ZODIAC_SIGNS, calculate_current_positions, calculate_transit_aspects
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

    def _format_positions_report(self, planets_data: dict, title: str) -> list:
        """מחלץ ומעצב את מיקומי הכוכבים כטקסט (נטאלי או מעבר)."""
        report = [
            f"\n{'=' * 80}",
            f"{title}",
            f"{'=' * 80}"
        ]

        # הרשימה מכילה רק גופים מרכזיים
        major_planets = [p for p in self.PLANET_NAMES_ENG.keys()
                         if p in planets_data and p not in ['פורטונה', 'ורטקס', 'לילית', 'כירון', 'ראש דרקון']]

        # הוספת נקודות רגישות מרכזיות
        points = ['אופק (AC)', 'רום שמיים (MC)']

        # כוכבים ונקודות
        report.append("\n* מיקומי כוכבים ונקודות:")
        for name in major_planets + points:
            if name in planets_data:
                pos = planets_data[name]
                # עיצוב הפורמט: 'מאדים: 23°55' בטלה'
                formatted_position = f"{pos['degree']:02d}°{pos['minute']:02d}' ב{pos['sign']}"
                report.append(f"    - {name:<10}: {formatted_position}")

        report.append("")
        return report

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
                retro_str = " (R)" if pos.get('is_retrograde') else ""

                formatted_position = f"{degree:02d}°{minute:02d}' ב{sign_heb}{retro_str}"

                line = f"    - {name:<10}: {formatted_position}"

                if include_house and pos.get('house') is not None:
                    line += f" (בית {pos['house']})"

                report.append(line)

        report.append("\n")
        return report

    def _format_aspects_report(self, aspects_list: list, title: str, is_interpreted = False) -> list:
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

        for aspect in aspects_list:
            p1_heb = aspect['planet1']
            p2_heb = aspect['planet2']
            aspect_heb = self.ASPECTS_DICT_HEB.get(aspect['aspect_name_eng'], aspect['aspect_name_eng'])
            orb = aspect['orb']

            # הוספת סוג המפה (נטאלי/מעבר)
            p1_type_str = f" ({'לידה' if aspect.get('p1_type') == 'natal' else 'מעבר'})"
            p2_type_str = f" ({'מעבר' if aspect.get('p2_type') == 'transit' else 'לידה'})"

            is_transit_aspect = (aspect.get('p1_type') != aspect.get('p2_type'))

            if is_transit_aspect:
                progress_indicator = self._calculate_transit_progress(aspect)
                max_orb_value = aspect.get('max_orb', 0.5)

                # עיצוב הפלט בהתאם לבקשה
                if progress_indicator == "not supported yet. coming soon!":
                    line_suffix = f" | {progress_indicator}"
                else:
                    line_suffix = f" | התקדמות: {progress_indicator}"

                report.append(f"{p1_heb}{p1_type_str} {aspect_heb} {p2_heb}{p2_type_str}{line_suffix}")
                # הוספת פירוט האורב בשורה נפרדת
                report.append(f"    - אורב נוכחי: {orb:.2f}° (מתוך: {max_orb_value:.2f}°)")
            else:
                # היבט נטאל-נטאל - הפורמט הישן
                report.append(f"{p1_heb}{p1_type_str} {aspect_heb} {p2_heb}{p2_type_str} | אורב: {orb:.2f}°")

            if is_interpreted:
                p1_eng = self.PLANET_NAMES_ENG[p1_heb]
                p2_eng = self.PLANET_NAMES_ENG[p2_heb]
                aspect_name = aspect['aspect_name_eng']

                key = f"Natal {p1_eng} {aspect_name} Transit {p2_eng}"
                aspects_data = self.chart_data.get('aspects_transit', {})
                analysis = aspects_data.get(key)

                # אם לא נמצא
                if not analysis:
                    analysis = f"❌ ניתוח היבט זה לא נמצא במאגר: {key}"
                report.append(f"\n{analysis}\n")
                if aspect != aspects_list[-1]:
                    report.append("-" * 80)
                report.append("")

        report.append("\n")
        return report

    def analyze_transits_and_aspects(self, current_location: tuple, is_interpreted = False) -> list:
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
            is_interpreted
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

    def analyze_chart(self, full_report: bool = True) -> list:
        """
        מבצע חישוב וניתוח מלא של מפת הלידה ומשלב את ניתוח השליטים.
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

        report = [f"=== ניתוח מפת לידה עבור {self.user.name} ({self.user.birthdate}) ===\n"]

        # נתוני המפה המחושבים
        planets_data = chart_positions['Planets']
        cusps = chart_positions['HouseCusps']
        aspects_list = chart_positions['Aspects']

        # ----------------------------------------------------------------------
        # השמש הירח והאופק האסטרולוגי
        # ----------------------------------------------------------------------
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

        # ----------------------------------------------------------------------
        # מיקומי הבתים והכוכבים במזלות
        # ----------------------------------------------------------------------
        report.append("")
        report.append("\n" + "=" * 80)
        report.append("מיקומי הבתים והכוכבים במזלות")
        report.append("=" * 80 + "\n")
        report.append("")

        for h in range(1, 13):
            cusp_degree = cusps[h]
            cusp_sign = self.get_sign_from_degree(cusp_degree)
            eng_cusp_sign = self.get_eng_sign_from_degree(cusp_degree)
            heb_house = self.HOUSES_NAMES_HEB[h-1]
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
                planet_in_house_analysis = self._fetch_analysis('planet_in_house', planet_in_house_key, f"ניתוח {planet} ב{heb_house[1:]} לא נמצא.")
                report.append(f"{planet} ב{heb_house[1:]}\n")
                report.append(f"{planet_in_house_analysis}\n")
                report.append("")
                # planet in sign
                planet_in_sign_analysis = self._fetch_analysis('planet_in_sign', planet_in_sign_key, f"ניתוח {planet} ב{planet_sign} לא נמצא.")
                report.append(f"{planet} ב{planet_sign}\n")
                report.append(f"{planet_in_sign_analysis}\n")
                report.append("")
                # planet in house in sign
                planet_house_sign_analysis = self._fetch_analysis('planet_house_sign', planet_house_sign_key, f"ניתוח {planet} ב{heb_house[1:]} ב{planet_sign}{is_inter_str}{is_retro_str} לא נמצא.")
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

                report.append(f"{heb_house} ב{cusp_sign} ושליט הבית ({ruler}) ממוקם בבית {ruler_house} ובמזל {is_intercepted_heb_str}{ruler_sign}")
                report.append(f"{ruler_analysis}\n")
                # report.append("-" * 80)

            except Exception as e:
                report.append(f"\n⚠️ שגיאה בניתוח בית {h}: {e}\n")

            report.append("")
            if h != 12:
                report.append("-" * 80 + "\n")
                report.append("")

        # ----------------------------------------------------------------------
        # ההיבטים (הקשרים והדינמיקה)
        # ----------------------------------------------------------------------
        report.append("")
        report.append("=" * 80)
        report.append("ההיבטים (הקשרים והדינמיקה)")
        report.append("=" * 80)
        report.append(
            "\nההיבטים מראים כיצד הכוחות (הכוכבים) והתחומים (הבתים) מנהלים אינטראקציה – האם הם משתפים פעולה או מתנגשים.\n")
        report.append("")

        aspects_data = self.chart_data.get('aspects', {})

        for aspect in aspects_list:
            p1 = aspect['planet1']
            p2 = aspect['planet2']
            aspect_name = self.ASPECTS_DICT_HEB[aspect['aspect_name_heb']]

            # נרמול שם ההיבט - הסרת מקפים לצורך חיפוש
            aspect_name_normalized = aspect['aspect_name_eng'].replace('-', '')

            # בניית מפתח שליפה: "Planet1 AspectName Planet2"
            key_1 = f"{self.PLANET_NAMES_ENG[p1]} {aspect_name_normalized} {self.PLANET_NAMES_ENG[p2]}"
            key_2 = f"{self.PLANET_NAMES_ENG[p2]} {aspect_name_normalized} {self.PLANET_NAMES_ENG[p1]}"

            # חיפוש ראשון - ללא מקפים
            analysis = aspects_data.get(key_1)
            if not analysis:
                analysis = aspects_data.get(key_2)

            # חיפוש שני - עם מקפים (אם המפתח המקורי שונה)
            if not analysis and aspect_name_normalized != aspect['aspect_name_eng']:
                key_1_dashed = f"{self.PLANET_NAMES_ENG[p1]} {aspect['aspect_name_eng']} {self.PLANET_NAMES_ENG[p2]}"
                key_2_dashed = f"{self.PLANET_NAMES_ENG[p2]} {aspect['aspect_name_eng']} {self.PLANET_NAMES_ENG[p1]}"
                analysis = aspects_data.get(key_1_dashed)
                if not analysis:
                    analysis = aspects_data.get(key_2_dashed)

            # אם עדיין לא נמצא
            if not analysis:
                analysis = f"❌ ניתוח היבט זה לא נמצא במאגר: {key_1} / {key_2}"

            report.append(f"\n{p1} {aspect_name} {p2} (orb: {aspect['orb']:.2f}°)")
            report.append(f"\n{analysis}\n")
            if aspect != aspects_list[-1]:
                report.append("-" * 80)

        return report

    def _calculate_transit_progress(self, aspect: dict) -> str:
        """
        מחשב את מחוון ההתקדמות הלינארי של היבט מעבר בתוך האורב.
        """
        import math

        p2_is_retrograde = aspect.get('p2_is_retrograde', False)

        # 1. טיפול במקרה של נסיגה
        if p2_is_retrograde:
            return "not supported yet. coming soon!"

        # 2. חישוב נתונים
        current_orb = aspect['orb']
        max_orb = aspect.get('max_orb', 0.5)
        is_approaching = aspect.get('is_approaching', True)

        if max_orb <= 0.001:
            return "[██████████] 100.0% (מדויק)"

        # 3. קביעת אחוז ההצגה והכיוון
        if is_approaching:
            status_text = "מתחזק"
            # כשמתקרב: אורב קטן = אחוז גבוה
            percent = ((max_orb - current_orb) / max_orb) * 100
        else:
            status_text = "נחלש"
            # כשמתרחק: אורב גדול = אחוז נמוך
            percent = ((max_orb - current_orb) / max_orb) * 100

        # 4. בניית המחוון (10 תווים)
        percent = max(0.0, min(100.0, percent))
        num_blocks = math.floor(percent / 10)
        progress_bar = "█" * num_blocks + "░" * (10 - num_blocks)

        return f"[{progress_bar}] {percent:.1f}% ({status_text})"
