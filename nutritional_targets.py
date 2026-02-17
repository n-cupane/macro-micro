import csv
from pathlib import Path

LARN_DICT: dict[str, dict[str, float]] = {}


def _parse_larn_value(raw_value: str) -> float:
    cleaned = str(raw_value or "").strip().replace("'", "").replace('"', "")
    cleaned = cleaned.replace(",", ".")
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def load_larn_data() -> None:
    csv_path = Path(__file__).resolve().parent / "larn.csv"
    parsed: dict[str, dict[str, float]] = {}

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) < 3:
                continue
            nutriente = str(row[0]).strip()
            if not nutriente:
                continue
            parsed[nutriente] = {
                "M": _parse_larn_value(row[1]),
                "F": _parse_larn_value(row[2]),
            }

    LARN_DICT.clear()
    LARN_DICT.update(parsed)
