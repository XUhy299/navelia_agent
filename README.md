# Navelia Agent

LangChain function-calling ReAct agents for patient intake, CSV writing, review, and PDF export.

## Architecture

- `FillingReActAgent`
  - Sends tools through the OpenAI-compatible `tools` request field via LangChain `bind_tools(...)`.
  - Tools: `read_patient_record`, `update_patient_field`.
  - Asks the patient for missing information and writes fields into CSV.

- `ReviewReActAgent`
  - Sends tools through the OpenAI-compatible `tools` request field via LangChain `bind_tools(...)`.
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

Start a new patient intake and show tool-call traces:

```powershell
python main.py --reset
```

Run without tool-call trace output:

```powershell
python main.py --reset --quiet-tools
```

During the CLI session:

- `status` or `状态`: show current case table
- `help` or `?`: show help
- `exit`, `quit`, or `q`: exit

Outputs:

- `data/patient_case.csv`
- `data/patient_case.pdf`
