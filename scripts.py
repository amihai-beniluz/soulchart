# הרץ את זה בפייתון כדי לבדוק אם יש בעיה בייבוא
import sys
sys.path.insert(0, r'C:\Users\Amihai\MyCode\PycharmProjects\SoulChart\src')

try:
    from bot.handlers.transit_handler import transit_start
    print("✅ ייבוא הצליח")
except Exception as e:
    print(f"❌ שגיאה בייבוא: {e}")