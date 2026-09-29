"""配套服务输出分级与敏感查询参数脱敏，不改变媒体处理逻辑。"""

import re

_LINE = re.compile(
    r"^\[(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\]\s+"
    r"\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}\s+(.*)$"
)
_SECRET = re.compile(
    r"(?i)([?&](?:api_key|apikey|token|access_token|password|secret)=)[^&\s\"'<>]+"
)
_ROUTINE = re.compile(
    r"^(?:tv_routes\.go:\d+: API 请求:|"
    r"splitter\.go:\d+: (?:分季依据尝试:|剧集结构一致，无需构建:)|"
    r"tv_service\.go:\d+: 季 \d+ 总集数=|"
    r"tvdb\.go:\d+: .* 季 \d+，集数:)"
)


def classify_service_line(line: str) -> tuple[str, str] | None:
    """对已知正常明细降级，保留未知输出及异常，并隐藏 URL 凭据。"""
    text = line.strip()
    if not text:
        return None
    match = _LINE.match(text)
    if match:
        level, text = match.groups()
        level = {"WARN": "warning", "FATAL": "critical"}.get(level, level.lower())
        if level == "info" and _ROUTINE.match(text):
            level = "debug"
    elif text.startswith("[GIN]"):
        # Gin 访问日志保留失败请求；无法解析的行不静默丢弃。
        status = re.search(r"\|\s*(\d{3})\s*\|", text)
        level = "debug" if status and int(status[1]) < 400 else "warning"
    else:
        # 包括 panic 堆栈续行，保留全文而非只保留最后一个字段。
        level = "warning"
    return level, _SECRET.sub(r"\1[REDACTED]", text)
