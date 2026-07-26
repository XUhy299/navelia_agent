from __future__ import annotations

from collections.abc import Callable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from config import API_KEY, BASE_URL, MAX_AGENT_STEPS, MODEL, PATIENT_FIELDS
from tools import export_patient_pdf, missing_fields, read_patient_record, read_patient_record_raw, update_patient_field


def build_llm(temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(
        model=MODEL,
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=temperature,
        max_tokens=1024,
    )


def message_text(message: AIMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            else:
                parts.append(str(item))
        return "".join(parts).strip()
    return str(content).strip()


TraceCallback = Callable[[str, dict], None]


class FunctionCallingReActAgent:
    """Small ReAct loop that sends LangChain tools through OpenAI tools/function-calling."""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: list[BaseTool],
        temperature: float = 0.2,
        trace_callback: TraceCallback | None = None,
    ):
        self.name = name
        self.tools = tools
        self.tool_map = {item.name: item for item in tools}
        self.llm = build_llm(temperature=temperature).bind_tools(tools)
        self.messages = [SystemMessage(content=system_prompt)]
        self.trace_callback = trace_callback

    def trace(self, event: str, payload: dict) -> None:
        if self.trace_callback:
            self.trace_callback(event, {"agent": self.name, **payload})

    def invoke(self, user_message: str) -> str:
        self.messages.append(HumanMessage(content=user_message))
        self.trace("user_message", {"content": user_message})

        final_text = ""
        for step in range(1, MAX_AGENT_STEPS + 1):
            self.trace("llm_request", {"step": step})
            ai_message = self.llm.invoke(self.messages)
            self.messages.append(ai_message)

            tool_calls = getattr(ai_message, "tool_calls", None) or []
            if not tool_calls:
                final_text = message_text(ai_message)
                self.trace("assistant_message", {"content": final_text})
                break

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call.get("args") or {}
                self.trace("tool_call", {"name": tool_name, "args": tool_args})
                tool = self.tool_map[tool_name]
                try:
                    result = tool.invoke(tool_args)
                except Exception as exc:
                    result = f"Tool error: {exc}"
                self.trace("tool_result", {"name": tool_name, "result": str(result)})

                self.messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                    )
                )

        return final_text


FILLING_SYSTEM_PROMPT = f"""
You are FillingReActAgent, a patient-intake assistant.

You must use function-calling tools to read and update the patient CSV table.
The available required fields are: {", ".join(PATIENT_FIELDS)}.

Workflow:
1. Call read_patient_record before deciding what to ask or update.
2. Extract only information explicitly provided by the patient.
3. For every known field, call update_patient_field with field_name and field_value.
4. Ask the next short question in Chinese for missing fields.
5. Ask at most two fields per turn.
6. Do not diagnose, do not give treatment advice.
7. If all fields are complete, say in Chinese that the information is complete and ready for review.
8. Do not use emoji or markdown tables.
"""


REVIEW_SYSTEM_PROMPT = f"""
You are ReviewReActAgent, a case-table reviewer.

You must use function-calling tools to inspect and finalize the patient case.
Required fields: {", ".join(PATIENT_FIELDS)}.

Workflow:
1. Call read_patient_record.
2. If any required field is empty, respond in Chinese with NEED_MORE and the missing fields.
3. If age does not contain a number, respond in Chinese with NEED_MORE and explain the issue.
4. If the table is complete, call export_patient_pdf.
5. Call export_patient_pdf at most once.
6. After exporting, respond in Chinese with APPROVED and the generated PDF path.
7. Do not use emoji or markdown tables.
"""


class FillingReActAgent(FunctionCallingReActAgent):
    def __init__(self, trace_callback: TraceCallback | None = None):
        super().__init__(
            name="FillingReActAgent",
            system_prompt=FILLING_SYSTEM_PROMPT,
            tools=[read_patient_record, update_patient_field],
            temperature=0.2,
            trace_callback=trace_callback,
        )


class ReviewReActAgent(FunctionCallingReActAgent):
    def __init__(self, trace_callback: TraceCallback | None = None):
        super().__init__(
            name="ReviewReActAgent",
            system_prompt=REVIEW_SYSTEM_PROMPT,
            tools=[read_patient_record, export_patient_pdf],
            temperature=0,
            trace_callback=trace_callback,
        )

    def local_missing_fields(self) -> list[str]:
        return missing_fields(read_patient_record_raw())
