import argparse
import json
import re

from agents import FillingReActAgent, ReviewReActAgent
from config import CSV_PATH, MAX_INTAKE_TURNS, PATIENT_FIELDS
from tools import read_patient_record_raw, write_patient_record_raw


EXIT_COMMANDS = {"exit", "quit", "q"}
STATUS_COMMANDS = {"status", "\u72b6\u6001"}
HELP_COMMANDS = {"help", "?"}


def divider(title: str = "") -> None:
    if title:
        print(f"\n--- {title} " + "-" * max(8, 54 - len(title)))
    else:
        print("-" * 64)


def format_payload(payload: object, limit: int = 260) -> str:
    text = json.dumps(payload, ensure_ascii=False, indent=2) if isinstance(payload, (dict, list)) else str(payload)
    text = text.replace("\n", "\n    ")
    if len(text) > limit:
        text = text[:limit] + "..."
    return text


def trace_printer(event: str, payload: dict) -> None:
    agent = payload.get("agent", "Agent")
    if event == "llm_request":
        print(f"  [{agent}] -> LLM step {payload.get('step')} with tools")
    elif event == "tool_call":
        print(f"  [{agent}] tool_call: {payload.get('name')}")
        print(f"    args: {format_payload(payload.get('args', {}))}")
    elif event == "tool_result":
        print(f"  [{agent}] tool_result: {payload.get('name')}")
        print(f"    result: {format_payload(payload.get('result', ''))}")


def fallback_question() -> str:
    record = read_patient_record_raw()
    missing = [field for field, value in record.items() if not value]
    if not missing:
        return "\u4fe1\u606f\u5df2\u7ecf\u5b8c\u6574\uff0c\u63a5\u4e0b\u6765\u8fdb\u5165\u5ba1\u6838\u3002"
    if len(missing) == 1:
        return f"\u8bf7\u95ee\u60a8\u7684{missing[0]}\u662f\u4ec0\u4e48\uff1f"
    return f"\u8bf7\u95ee\u60a8\u7684{missing[0]}\u548c{missing[1]}\u662f\u4ec0\u4e48\uff1f"


def print_help() -> None:
    print("\n可用命令：")
    print("  status / 状态  查看当前病例表")
    print("  help / ?       查看帮助")
    print("  exit / quit / q 退出")
    print("提示：直接回车不会发送给 LLM；单字输入会被视为可能误触。")


def print_record_status() -> None:
    record = read_patient_record_raw()
    missing = []
    divider("\u5f53\u524d\u75c5\u4f8b\u8868")
    for field, value in record.items():
        mark = "OK" if value else ".."
        print(f"  [{mark}] {field:<6} {value or '[未填写]'}")
        if not value:
            missing.append(field)
    print(f"  缺失：{', '.join(missing) if missing else '无'}")


def looks_like_accidental_input(message: str) -> bool:
    if len(message) != 1:
        return False
    return not message.isdigit() and message.lower() not in {"男", "女"}


def read_patient_message(question: str) -> str | None:
    while True:
        try:
            print()
            print(f"问诊助手：{question}")
            message = input("患者> ").strip()
        except EOFError:
            print("\n输入已结束，当前填写进度已保存在 CSV。")
            return None

        lowered = message.lower()
        if lowered in EXIT_COMMANDS:
            return message
        if lowered in HELP_COMMANDS:
            print_help()
            continue
        if lowered in STATUS_COMMANDS:
            print_record_status()
            continue
        if not message:
            print("未检测到输入，本轮不会发送给 LLM。请重新输入，或输入 exit 退出。")
            continue
        if looks_like_accidental_input(message):
            print(f"检测到可能误触的单字输入“{message}”，本轮不会发送给 LLM。")
            print("请重新输入完整回答，例如：我叫李明，35岁。")
            continue

        return message


def missing_field_count() -> int:
    record = read_patient_record_raw()
    return sum(1 for value in record.values() if not value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Navelia function-calling ReAct intake agents.")
    parser.add_argument("--reset", action="store_true", help="Clear the current CSV before starting.")
    parser.add_argument("--quiet-tools", action="store_true", help="Hide LLM tool-call trace output.")
    args = parser.parse_args()

    if args.reset:
        write_patient_record_raw({field: "" for field in PATIENT_FIELDS})

    trace = None if args.quiet_tools else trace_printer
    filling_agent = FillingReActAgent(trace_callback=trace)
    review_agent = ReviewReActAgent(trace_callback=trace)

    divider("\u667a\u80fd\u95ee\u8bca")
    print("输入 exit 可退出；输入 status 查看病例表；输入 help 查看帮助。")
    print(f"CSV 将保存到：{CSV_PATH}")

    divider("Filling Agent")
    question = filling_agent.invoke("\u5f00\u59cb\u65b0\u7684\u60a3\u8005\u95ee\u8bca\uff0c\u8bf7\u5148\u67e5\u770b\u75c5\u4f8b\u8868\u5e76\u8be2\u95ee\u7f3a\u5931\u4fe1\u606f\u3002")
    if not question:
        question = fallback_question()

    previous_missing = missing_field_count()
    for _ in range(MAX_INTAKE_TURNS):
        user_message = read_patient_message(question)
        if user_message is None:
            return
        if user_message.lower() in EXIT_COMMANDS:
            print("已退出，当前填写进度已保存在 CSV。")
            return

        divider("Filling Agent")
        question = filling_agent.invoke(user_message)
        if not question:
            question = fallback_question()

        current_missing = missing_field_count()
        print_record_status()
        if current_missing == previous_missing:
            print("本轮没有新增字段。可以换一种更完整的说法，或输入 status 查看当前进度。")
        previous_missing = current_missing

        if current_missing == 0:
            break

    if missing_field_count() > 0:
        print("\n达到最大问诊轮数，但仍有字段缺失，暂不进入 PDF 生成。")
        print_record_status()
        return

    divider("Review Agent")
    review_result = review_agent.invoke("\u8bf7\u5ba1\u6838\u5f53\u524d\u75c5\u4f8b\u8868\uff0c\u5b8c\u6574\u5219\u751f\u6210 PDF\u3002")
    print(f"\n审核结果：{re.sub(r'\\s+', ' ', review_result).strip()}")


if __name__ == "__main__":
    main()
