# src/birth_chart_analysis/ChartAnalysis.py

from datetime import datetime
import textwrap
import traceback

# ייבוא מהמודולים השכנים
from .CalculationEngine import calculate_chart_positions, ZODIAC_SIGNS, ENG_ZODIAC_SIGNS
from .DataLoaders import load_all_chart_data


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
        'עקרב': 'פלוטו',  # מודרני
        'קשת': 'צדק', 'גדי': 'שבתאי',
        'דלי': 'אורנוס',  # מודרני
        'דגים': 'נפטון'  # מודרני
    }

    # מפת שמות באנגלית לשליפה ממאגר הנתונים
    PLANET_NAMES_ENG = {
        'שמש': 'Sun', 'ירח': 'Moon', 'מרקורי': 'Mercury',
        'ונוס': 'Venus', 'מאדים': 'Mars', 'צדק': 'Jupiter',
        'שבתאי': 'Saturn', 'אורנוס': 'Uranus', 'נפטון': 'Neptune',
        'פלוטו': 'Pluto', 'ראש דרקון': 'North Node', 'לילית': 'Lilith',
        'כירון': 'Chiron', 'אופק (AC)': 'AC', 'רום שמיים (MC)': 'MC'
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

    def __init__(self, user: object):
        self.user = user

        # טעינת נתוני הניתוח האסטרולוגיים פעם אחת
        if ChartAnalysis.chart_data is None:
            ChartAnalysis.chart_data = load_all_chart_data()

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

    def _fetch_analysis(self, category: str, key: str, default_message: str = "❌ ניתוח זה לא נמצא במאגר") -> str:
        """ פונקציית עזר לשליפת ניתוח מהמאגר הטקסטואלי """
        data_source = self.chart_data.get(category, {})
        # לא מוסיפים נקודותיים - המפתחות נטענים כמו שהם
        analysis = data_source.get(key, default_message)
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

        report.append("")

        # ----------------------------------------------------------------------
        # השמש הירח והאופק האסטרולוגי
        # ----------------------------------------------------------------------
        report.append("\n" + "=" * 80)
        report.append("השמש הירח והאופק העולה")
        report.append("=" * 80 + "\n")

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
        report.append("")

        # ----------------------------------------------------------------------
        # מיקומי הבתים והכוכבים במזלות
        # ----------------------------------------------------------------------
        report.append("\n" + "=" * 80)
        report.append("מיקומי הבתים והכוכבים במזלות")
        report.append("=" * 80 + "\n")

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

            report.append(f"בית {h}\n")
            report.append(house_analysis + "\n")
            report.append("")
            report.append(f"מזל {cusp_sign}\n")
            report.append(f"{sign_analysis}\n")
            report.append("")
            report.append(f"{heb_house} ב{cusp_sign}{intercepted_str}\n")
            report.append(f"{house_in_sign_analysis}\n")
            report.append("")

            # התייחסות לכוכבים הנמצאים בבית
            for planet, data in planets_data.items():
                if data['house'] != h:
                    continue
                planet_sign = data['sign']
                is_retro = data['is_retrograde']
                planet_in_house_key = f"{self.PLANET_NAMES_ENG[planet]} in {self.HOUSE_NAMES_ENG_FULL[h - 1]}"
                planet_in_sign_key = f"{self.PLANET_NAMES_ENG[planet]} in {self.SIGN_NAMES_ENG[planet_sign]}"
                # TODO להוסיף ניתוח כוכב בנסיגה
                planet_analysis = self._fetch_analysis('planets', planet, f"ניתוח {planet} לא נמצא.")
                report.append(f"{planet}\n")
                report.append(f"{planet_analysis}\n")
                report.append("")
                # TODO להוסיף ניתוח כוכב בבית בנסיגה
                planet_in_house_analysis = self._fetch_analysis('planet_in_house', planet_in_house_key, f"ניתוח {planet} ב{heb_house[1:]} לא נמצא.")
                report.append(f"{planet} ב{heb_house[1:]}\n")
                report.append(f"{planet_in_house_analysis}\n")
                report.append("")
                # TODO להוסיף ניתוח כוכב במזל בנסיגה ובמזל כלוא
                planet_in_sign_analysis = self._fetch_analysis('planet_in_sign', planet_in_sign_key,
                                                                f"ניתוח {planet} ב{planet_sign} לא נמצא.")
                report.append(f"{planet} ב{planet_sign}\n")
                report.append(f"{planet_in_sign_analysis}\n")
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

                report.append(f"{heb_house} ב{cusp_sign} ושליט הבית ({ruler}) ממוקם בבית {ruler_house} ובמזל {ruler_sign}")
                report.append(f"{ruler_analysis}\n")
                # report.append("-" * 80)

            except Exception as e:
                report.append(f"\n⚠️ שגיאה בניתוח בית {h}: {e}\n")

            report.append("")
            report.append("-" * 80 + "\n")

        # ----------------------------------------------------------------------
        # ההיבטים (הקשרים והדינמיקה)
        # ----------------------------------------------------------------------
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
            aspect_name = aspect['aspect_name_heb']

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

            report.append(f"\n{p1} {aspect_name} {p2} (אורב: {aspect['orb']:.2f}°)")
            report.append(f"\n{analysis}\n")
            report.append("-" * 80)

        return report
