"""
SoulChart Mobile API - Fast Backend for Mobile Printing
========================================================
מאפשר הזנת פרטים מהטלפון והורדת קבצי PDF/TXT/PNG
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple, Dict, List
import os
import sys
import uuid
import shutil

# הוספת נתיב לקוד הקיים שלך
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
# sys.path.insert(0, PROJECT_ROOT)

# ייבוא המודולים הקיימים שלך
try:
    from src.name_analysis.NameAnalysis import NameAnalysis
    from src.birth_chart_analysis.ChartAnalysis import ChartAnalysis
    from src.birth_chart_analysis.TransitCalculator import TransitCalculator
    from src.birth_chart_analysis.CalculationEngine import calculate_chart_positions, calculate_current_positions
    from src.birth_chart_analysis.BirthChartDrawer import draw_and_save_chart, draw_and_save_biwheel_chart
    from src.user import User
    from src.utils import write_results_to_file
except ImportError as e:
    print(f"⚠️ Warning: Could not import SoulChart modules: {e}")
    print("Make sure the API is running from the correct directory")

# יצירת תיקיות פלט
OUTPUT_DIR = os.path.join(CURRENT_DIR, 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(
    title="SoulChart Mobile API",
    description="API for generating astrological reports from mobile",
    version="1.0.0"
)

# CORS - אפשר גישה מכל מקום
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Models ============

class NameAnalysisRequest(BaseModel):
    name: str = Field(..., description="שם פרטי בעברית")
    nikud_dict: Dict[int, str] = Field(default_factory=dict, description="ניקוד לכל אות")


class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class NatalChartRequest(BaseModel):
    name: str
    birthdate: str = Field(..., description="YYYY-MM-DD")
    birthtime: str = Field(..., description="HH:MM")
    birth_location: Location
    include_interpretation: bool = Field(default=True)


class CurrentTransitRequest(BaseModel):
    name: str
    birthdate: str
    birthtime: str
    birth_location: Location
    current_location: Location
    include_interpretation: bool = Field(default=True)


class FutureTransitRequest(BaseModel):
    name: str
    birthdate: str
    birthtime: str
    birth_location: Location
    current_location: Location
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    include_interpretation: bool = Field(default=True)


# ============ Helper Functions ============

def parse_date(date_str: str) -> date:
    """המרת מחרוזת לתאריך"""
    return datetime.strptime(date_str, '%Y-%m-%d').date()


def parse_time(time_str: str) -> time:
    """המרת מחרוזת לשעה"""
    return datetime.strptime(time_str, '%H:%M').time()


def cleanup_old_files():
    """מחיקת קבצים ישנים (מעל 24 שעות)"""
    now = datetime.now()
    for filename in os.listdir(OUTPUT_DIR):
        filepath = os.path.join(OUTPUT_DIR, filename)
        file_age = now - datetime.fromtimestamp(os.path.getctime(filepath))
        if file_age > timedelta(hours=24):
            try:
                os.remove(filepath)
            except:
                pass


# ============ Endpoints ============

@app.get("/")
def root():
    return {
        "message": "SoulChart Mobile API",
        "status": "running",
        "endpoints": [
            "/api/name-analysis",
            "/api/natal-chart",
            "/api/current-transit",
            "/api/future-transit",
            "/download/{file_id}"
        ]
    }


@app.post("/api/name-analysis")
async def analyze_name(request: NameAnalysisRequest, background_tasks: BackgroundTasks):
    """ניתוח שם פרטי"""
    try:
        cleanup_old_files()
        file_id = str(uuid.uuid4())
        output_path = os.path.join(OUTPUT_DIR, f"{file_id}_name.txt")

        analysis = NameAnalysis(request.name, request.nikud_dict)
        result = analysis.analyze_name()

        with open(output_path, 'w', encoding='utf-8') as f:
            for line in result:
                f.write(line.rstrip('\n') + '\n')

        return {
            "success": True,
            "file_id": file_id,
            "filename": f"{request.name}_name.txt",
            "download_url": f"/download/{file_id}_name.txt",
            "message": "ניתוח השם הושלם בהצלחה"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"שגיאה: {str(e)}")


@app.post("/api/natal-chart")
async def natal_chart(request: NatalChartRequest, background_tasks: BackgroundTasks):
    """חישוב מפת לידה"""
    try:
        cleanup_old_files()
        birthdate = parse_date(request.birthdate)
        birthtime = parse_time(request.birthtime)
        location = (request.birth_location.latitude, request.birth_location.longitude)

        user = User(request.name, birthdate, birthtime, location)
        file_id = str(uuid.uuid4())
        txt_path = os.path.join(OUTPUT_DIR, f"{file_id}_chart.txt")
        png_path = os.path.join(OUTPUT_DIR, f"{file_id}_chart.png")

        chart_analysis = ChartAnalysis(user)
        birth_datetime = datetime.combine(birthdate, birthtime)
        chart_positions = calculate_chart_positions(birth_datetime, location[0], location[1])
        report = chart_analysis.analyze_chart(is_interpreted=request.include_interpretation)

        with open(txt_path, 'w', encoding='utf-8') as f:
            for line in report:
                f.write(line.rstrip('\n') + '\n')

        draw_and_save_chart(chart_positions, user, png_path)

        return {
            "success": True,
            "file_id": file_id,
            "files": {
                "report": {"filename": f"{request.name}_chart.txt", "download_url": f"/download/{file_id}_chart.txt"},
                "image": {"filename": f"{request.name}_chart.png", "download_url": f"/download/{file_id}_chart.png"}
            },
            "message": "מפת הלידה חושבה בהצלחה"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"שגיאה: {str(e)}")


@app.post("/api/current-transit")
async def current_transit(request: CurrentTransitRequest, background_tasks: BackgroundTasks):
    """טרנזיטים נוכחיים"""
    try:
        cleanup_old_files()
        birthdate = parse_date(request.birthdate)
        birthtime = parse_time(request.birthtime)
        birth_location = (request.birth_location.latitude, request.birth_location.longitude)
        current_location = (request.current_location.latitude, request.current_location.longitude)

        user = User(request.name, birthdate, birthtime, birth_location)
        file_id = str(uuid.uuid4())
        txt_path = os.path.join(OUTPUT_DIR, f"{file_id}_transit.txt")
        png_path = os.path.join(OUTPUT_DIR, f"{file_id}_transit.png")

        birth_datetime = datetime.combine(birthdate, birthtime)
        natal_chart_data = calculate_chart_positions(birth_datetime, birth_location[0], birth_location[1])
        current_datetime = datetime.now()
        transit_chart_data = calculate_current_positions(current_datetime, current_location[0], current_location[1])

        chart_analysis = ChartAnalysis(user)
        transit_result = chart_analysis.analyze_transits_and_aspects(current_location,
                                                                     is_interpreted=request.include_interpretation)

        with open(txt_path, 'w', encoding='utf-8') as f:
            for line in transit_result:
                f.write(line.rstrip('\n') + '\n')

        draw_and_save_biwheel_chart(natal_chart_data, transit_chart_data, user, current_datetime, png_path)

        return {
            "success": True,
            "file_id": file_id,
            "files": {
                "report": {"filename": f"{request.name}_transit.txt",
                           "download_url": f"/download/{file_id}_transit.txt"},
                "image": {"filename": f"{request.name}_transit.png", "download_url": f"/download/{file_id}_transit.png"}
            },
            "message": "טרנזיטים נוכחיים חושבו בהצלחה"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"שגיאה: {str(e)}")


@app.post("/api/future-transit")
async def future_transit(request: FutureTransitRequest, background_tasks: BackgroundTasks):
    """טרנזיטים עתידיים"""
    try:
        cleanup_old_files()
        birthdate = parse_date(request.birthdate)
        birthtime = parse_time(request.birthtime)
        birth_location = (request.birth_location.latitude, request.birth_location.longitude)
        current_location = (request.current_location.latitude, request.current_location.longitude)
        start_date = datetime.strptime(request.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(request.end_date, '%Y-%m-%d')

        user = User(request.name, birthdate, birthtime, birth_location)
        file_id = str(uuid.uuid4())
        txt_path = os.path.join(OUTPUT_DIR, f"{file_id}_future.txt")
        json_path = os.path.join(OUTPUT_DIR, f"{file_id}_future.json")

        calculator = TransitCalculator(user)
        aspects_data = calculator.calculate_aspects_in_range(start_date, end_date, current_location)

        report_lines = [f"טרנזיטים עתידיים - {request.name}", f"תקופה: {request.start_date} עד {request.end_date}",
                        "=" * 80, ""]

        for aspect in aspects_data.get('aspects', []):
            lifecycle = aspect.get('lifecycle', {})
            report_lines.append(f"🔮 {aspect['planet1']} {aspect.get('aspect_name_heb', '')} {aspect['planet2']}")
            if lifecycle.get('start'):
                report_lines.append(f"   🟢 התחלה: {lifecycle['start'].strftime('%Y-%m-%d %H:%M')}")
            for exact in lifecycle.get('exact_dates', []):
                report_lines.append(f"   ⭐ מדויק: {exact['date'].strftime('%Y-%m-%d %H:%M')}")
            if lifecycle.get('end'):
                report_lines.append(f"   🔴 סיום: {lifecycle['end'].strftime('%Y-%m-%d %H:%M')}")
            report_lines.append("")

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(aspects_data, f, ensure_ascii=False, indent=2,
                      default=lambda x: x.isoformat() if isinstance(x, datetime) else str(x))

        return {
            "success": True,
            "file_id": file_id,
            "files": {
                "report": {"filename": f"{request.name}_future.txt", "download_url": f"/download/{file_id}_future.txt"},
                "data": {"filename": f"{request.name}_future.json", "download_url": f"/download/{file_id}_future.json"}
            },
            "aspects_count": len(aspects_data.get('aspects', [])),
            "message": "טרנזיטים עתידיים חושבו בהצלחה"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"שגיאה: {str(e)}")


@app.get("/download/{filename}")
async def download_file(filename: str):
    """הורדת קובץ"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="הקובץ לא נמצא")

    media_type = "text/plain" if filename.endswith('.txt') else "image/png" if filename.endswith(
        '.png') else "application/json"
    return FileResponse(filepath, media_type=media_type,
                        filename=filename.split('_', 1)[1] if '_' in filename else filename)


@app.get("/health")
def health_check():
    """בדיקת תקינות"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    print("🌟 SoulChart Mobile API Starting...")
    uvicorn.run(app, host="0.0.0.0", port=8000)