from datetime import datetime

class User:
    def __init__(self, name, birthdate, birthtime=None, location=None):
        self.name = name
        self.birthdate = birthdate
        self.birthtime = birthtime
        self.location = location

    def __str__(self):
        return f"User(name={self.name}, birthdate={self.birthdate}, birthtime={self.birthtime}, location={self.location})"

    def get_birth_info(self):
        # אם יש שעת לידה, נציג אותה. אחרת, נציג 'N/A' או לא נציג בכלל.
        birthtime_display = self.birthtime if self.birthtime else None
        return f"Name: {self.name}, Birthdate: {self.birthdate.strftime('%Y-%m-%d')}, Birthtime: {birthtime_display if birthtime_display else 'N/A'}, Location: {self.location if self.location else 'N/A'}"
