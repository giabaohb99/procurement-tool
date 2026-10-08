"""Bảng thuộc DỊCH VỤ AI (ai-CR-119, phase S): khi tách, chúng nằm ở database `agent_hub`, không ở DB ERP.

Một chỗ khai duy nhất — alembic của dịch vụ AI (`migrations_agent/env.py`) lọc theo đây, script chép dữ liệu
(`scripts/agent_split/copy_agent_tables.sh`) và bài kiểm cũng đọc từ đây.
"""
from __future__ import annotations

AGENT_TABLE_PREFIXES = ("tab_agent_",)
AGENT_TABLE_NAMES = frozenset({
    "tab_ai_key",                     # sổ khóa AI (công ty + cá nhân) — ai-CR-098
    "tab_assistant_conversation",     # hội thoại Trợ lý AI trên web — đi theo dịch vụ AI (S-3)
    "tab_assistant_message",
})


def is_agent_table(name: str) -> bool:
    return name in AGENT_TABLE_NAMES or name.startswith(AGENT_TABLE_PREFIXES)


def agent_tables(metadata) -> list:
    """Các Table của metadata thuộc dịch vụ AI, theo thứ tự tạo (phụ thuộc khóa ngoại)."""
    return [t for t in metadata.sorted_tables if is_agent_table(t.name)]
