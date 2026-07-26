from pathlib import Path


BASE_URL = "https://api.kukuit.com/v1"
API_KEY = "sk-oDIdFcfsc8CqPo71hAhUdALzyvrajqOfyttr43LkNV55RKNE"
MODEL = "qwen3.7-plus"

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
CSV_PATH = DATA_DIR / "patient_case.csv"
PDF_PATH = DATA_DIR / "patient_case.pdf"

PATIENT_FIELDS = [
    "\u59d3\u540d",
    "\u5e74\u9f84",
    "\u6027\u522b",
    "\u56fd\u5bb6",
    "\u75c7\u72b6",
    "\u65e2\u5f80\u75c5\u53f2",
]

FIELD_ALIASES = {
    "name": "\u59d3\u540d",
    "\u59d3\u540d": "\u59d3\u540d",
    "age": "\u5e74\u9f84",
    "\u5e74\u9f84": "\u5e74\u9f84",
    "gender": "\u6027\u522b",
    "\u6027\u522b": "\u6027\u522b",
    "country": "\u56fd\u5bb6",
    "\u56fd\u5bb6": "\u56fd\u5bb6",
    "symptom": "\u75c7\u72b6",
    "symptoms": "\u75c7\u72b6",
    "\u75c7\u72b6": "\u75c7\u72b6",
    "medical_history": "\u65e2\u5f80\u75c5\u53f2",
    "past_medical_history": "\u65e2\u5f80\u75c5\u53f2",
    "\u75c5\u53f2": "\u65e2\u5f80\u75c5\u53f2",
    "\u65e2\u5f80\u75c5\u53f2": "\u65e2\u5f80\u75c5\u53f2",
}

MAX_INTAKE_TURNS = 12
MAX_AGENT_STEPS = 12
