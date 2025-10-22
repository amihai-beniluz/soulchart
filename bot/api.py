from src.name_analysis.NameAnalysis import NameAnalysis

def analyze_name(name: str, nikud_dict: dict) -> str:
    analyzer = NameAnalysis(name, nikud_dict)
    result_lines = analyzer.analyze_name()
    # מסיר קודי ANSI של צבע (כדי שהפלט יתאים לטלגרם)
    clean_lines = [line.replace("\033[97m", "").replace("\033[36m", "").replace("\033[35m", "")
                   .replace("\033[93m", "").replace("\033[31m", "").replace("\033[94m", "")
                   .replace("\033[30m", "").replace("\033[91m", "").replace("\033[0m", "")
                   for line in result_lines]
    return "\n".join(clean_lines)
