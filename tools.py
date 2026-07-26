import csv
from pathlib import Path

from langchain_core.tools import tool

from config import CSV_PATH, FIELD_ALIASES, PATIENT_FIELDS, PDF_PATH
from pdf_exporter import export_patient_record_to_pdf


def normalize_field_name(field_name: str) -> str:
    cleaned = field_name.strip()
    if cleaned in FIELD_ALIASES:
        return FIELD_ALIASES[cleaned]

    lower = cleaned.lower()
    if lower in FIELD_ALIASES:
        return FIELD_ALIASES[lower]

    allowed = ", ".join(PATIENT_FIELDS)
    raise ValueError(f"Unsupported field: {field_name}. Allowed fields: {allowed}")


def ensure_record_file(csv_path: Path = CSV_PATH) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if csv_path.exists():
        return

    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=PATIENT_FIELDS)
        writer.writeheader()
        writer.writerow({field: "" for field in PATIENT_FIELDS})


def read_patient_record_raw(csv_path: Path = CSV_PATH) -> dict[str, str]:
    ensure_record_file(csv_path)
    with csv_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        row = next(reader, None)

    if row is None:
        row = {field: "" for field in PATIENT_FIELDS}

    return {field: (row.get(field) or "").strip() for field in PATIENT_FIELDS}


def write_patient_record_raw(record: dict[str, str], csv_path: Path = CSV_PATH) -> None:
    ensure_record_file(csv_path)
    normalized = {field: (record.get(field) or "").strip() for field in PATIENT_FIELDS}
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=PATIENT_FIELDS)
        writer.writeheader()
        writer.writerow(normalized)


def update_patient_field_raw(field_name: str, field_value: str, csv_path: Path = CSV_PATH) -> str:
    field = normalize_field_name(field_name)
    value = str(field_value).strip()
    record = read_patient_record_raw(csv_path)
    record[field] = value
    write_patient_record_raw(record, csv_path)
    return f"Updated {field} = {value}"


def missing_fields(record: dict[str, str]) -> list[str]:
    return [field for field in PATIENT_FIELDS if not record.get(field, "").strip()]


@tool
def read_patient_record() -> dict[str, str]:
    """Read the current patient case table as a JSON object."""
    return read_patient_record_raw()


@tool
def update_patient_field(field_name: str, field_value: str) -> str:
    """Write one patient case field to the CSV table."""
    return update_patient_field_raw(field_name, field_value)


@tool
def export_patient_pdf() -> str:
    """Export the current patient case table to PDF and return the PDF path."""
    record = read_patient_record_raw()
    return str(export_patient_record_to_pdf(record, PDF_PATH))
