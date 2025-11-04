// ודא שהכתובת היא בדיוק http://localhost:8000
const API_BASE_URL = 'http://localhost:8000';

async function analyzeName() {
    const name = document.getElementById('nameInput').value;
    const resultsElement = document.getElementById('results');
    resultsElement.textContent = '...מעבד בקשה...';

    // יצירת גוף הבקשה (Payload)
    const requestBody = {
        name: name,
        nikud_dict: {}
    };

    try {
        // ניסיון שליחת הבקשה ל-API הרץ בדוקר
        const response = await fetch(`${API_BASE_URL}/api/name-analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        // בדיקה שהתשובה היא תקינה (סטטוס 200)
        if (!response.ok) {
            // אם השרת החזיר שגיאת HTTP
            throw new Error(`שגיאת HTTP: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            // אם הצליח: הצגת לינק ההורדה
            resultsElement.textContent = `ניתוח הושלם. לינק להורדה: ${API_BASE_URL}${data.download_url}`;
        } else {
            // אם ה-API החזיר תשובה, אבל עם שגיאה פנימית
            resultsElement.textContent = `שגיאת API: ${data.message}`;
        }

    } catch (error) {
        // אם נכשל בחיבור או ב-fetch (כאן כנראה נופלת הבעיה שלך)
        resultsElement.textContent = `שגיאת חיבור ל-API: ${error.message}. ודא שהקונטיינר רץ ב-http://localhost:8000.`;
    }
}