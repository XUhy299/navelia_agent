# Navelia Agent

LangChain function-calling ReAct agents for patient intake.

## Architecture

- `FillingReActAgent`
  - Uses OpenAI-compatible function-calling tools through the model `tools` field.
  - Tools: `read_patient_record`, `update_patient_field`.
  - Asks the patient for missing information and writes fields into CSV.

- `ReviewReActAgent`
  - Uses OpenAI-compatible function-calling tools through the model `tools` field.
  - Tools: `read_patient_record`, `export_patient_pdf`.
  - Reviews required fields and exports PDF when complete.

Required fields:

- 姓名
- 年龄
- 性别
- 国家
- 症状
- 既往病史

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python main.py --reset
```

Outputs:

- `data/patient_case.csv`
- `data/patient_case.pdf`
