"""NÉN HỘI THOẠI (ai-CR-136, phase 14 của doc/agent-hub/15) — dùng chung cho Trợ lý AI trên web và bot Telegram / Zalo.

Trước đây chỉ có cửa sổ trượt (web 20 lượt; Telegram / Zalo 8 lượt, 2 giờ, 6.000 ký tự): quá thì CẮT, nên việc dài nhiều
bước quên mất đầu câu chuyện. Nay mỗi lượt gọi model gửi: luật + lõi nhớ + BẢN TÓM TẮT phần đầu cuộc + các lượt gần nhất +
câu mới. Ba mức theo ước lượng token so với một ngân sách cấu hình được (`ai_context_budget_tokens`):

  ≥ CLEAR %   lược kết quả công cụ cũ (câu trả lời rút từ tra ERP / tra mạng / đọc tệp), chỉ giữ nguyên KEEP_TURNS lượt gần;
  ≥ SUMMARY % tóm các lượt cũ bằng MỘT lượt model rẻ, lưu bản tóm tắt + mốc «đã tóm tới tin nào» theo TỪNG cuộc
              (`tab_agent_conv_summary`); lần sau tóm NỐI TIẾP từ mốc, không tóm lại từ đầu;
  ≥ DROP %    mới bỏ lượt cũ nhất.

Đơn vị nén là TỪNG cuộc — (scope, scope_key) — không bao giờ gộp hay đọc chéo giữa hai người / hai nhóm.

An toàn: lượt tóm hỏng / quá giờ thì quay về cửa sổ trượt cũ (do người gọi đưa vào), KHÔNG chặn câu trả lời. Token của lượt
tóm ghi vào sổ chi phí (`tab_agent_run`, bước «Tóm tắt hội thoại»).
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.config import settings

log = logging.getLogger("app.assistant.compaction")

#  Tiếng Việt có dấu ra token dày hơn tiếng Anh: ~3 ký tự / token là ước lượng an toàn (đếm dư còn hơn thiếu).
CHARS_PER_TOKEN = 3
#  Ảnh / PDF nạp lại (web, CR-204) — ước lượng thô một khối.
BLOCK_TOKENS = 1500
TOOL_STUB_CHARS = 240
SUMMARY_MAX_CHARS = 1500
TURN_CHARS_FOR_SUMMARY = 2500

LEVEL_NONE = 0
LEVEL_CLEAR = 1
LEVEL_SUMMARY = 2
LEVEL_DROP = 3
LEVEL_FALLBACK = -1

SUMMARY_SYSTEM = (
    "Bạn tóm tắt một cuộc hội thoại giữa NGƯỜI DÙNG và TRỢ LÝ ERP để trợ lý nhớ tiếp ở các lượt sau. Viết tiếng Việt, gạch "
    "đầu dòng, tối đa 1.200 ký tự, chỉ dựa vào nội dung được đưa, không bịa. BẮT BUỘC giữ: (1) điều người dùng đã CHỐT / "
    "quyết định / dặn; (2) ĐỐI TƯỢNG đang bàn: nhà cung cấp, pháp nhân, phòng ban, người, mã chứng từ (YCMH, YCBG, ĐMH, "
    "YCTT, AI-xxxx…), số tiền, ngày; (3) việc CÒN DỞ, câu hỏi chưa trả lời, bước tiếp theo đã hẹn. Bỏ lời chào, lời cảm ơn, "
    "chi tiết đã hết giá trị. Có bản tóm tắt cũ thì GỘP phần mới vào, giữ nguyên các ý cũ còn giá trị."
)


@dataclass
class Turn:
    role: str                       # "user" | "assistant"
    content: str | list             # chữ, hoặc danh sách khối (web nạp lại tệp)
    msg_id: int = 0                 # id dòng sổ — dùng làm mốc «đã tóm tới»
    tool: bool = False              # câu trả lời rút từ kết quả công cụ

    def as_message(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class Plan:
    summary: str = ""
    turns: list[dict] = field(default_factory=list)
    level: int = LEVEL_NONE
    tokens: int = 0


def enabled() -> bool:
    try:
        return bool(app_settings.get("ai_compact_enabled"))
    except Exception:  # noqa: BLE001 — chưa có bảng cấu hình (bài kiểm / dịch vụ mới dựng) → theo .env
        return bool(settings.AI_COMPACT_ENABLED)


def _setting(key: str, env_attr: str) -> int:
    try:
        value = int(app_settings.get(key) or 0)
    except Exception:  # noqa: BLE001
        value = 0
    return value if value > 0 else int(getattr(settings, env_attr))


def limits() -> dict:
    budget = _setting("ai_context_budget_tokens", "AI_CONTEXT_BUDGET_TOKENS")
    return {
        "budget": budget,
        "clear": budget * _setting("ai_compact_clear_pct", "AI_COMPACT_CLEAR_PCT") // 100,
        "summary": budget * _setting("ai_compact_summary_pct", "AI_COMPACT_SUMMARY_PCT") // 100,
        "drop": budget * _setting("ai_compact_drop_pct", "AI_COMPACT_DROP_PCT") // 100,
        "keep": max(1, _setting("ai_compact_keep_turns", "AI_COMPACT_KEEP_TURNS")),
    }


def estimate(content) -> int:
    if isinstance(content, str):
        return len(content) // CHARS_PER_TOKEN + 4
    total = 4
    for block in content or []:
        if isinstance(block, dict) and block.get("type") == "text":
            total += len(str(block.get("text") or "")) // CHARS_PER_TOKEN
        else:
            total += BLOCK_TOKENS
    return total


def _total(summary: str, turns: list[Turn], question: str) -> int:
    return estimate(summary) + sum(estimate(t.content) for t in turns) + estimate(question)


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    return " ".join(str(b.get("text") or "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text")


def _stub(content) -> str:
    text = " ".join(_text_of(content).split())
    head = text[:TOOL_STUB_CHARS] + ("…" if len(text) > TOOL_STUB_CHARS else "")
    return f"[Kết quả tra cứu cũ đã lược — ý chính: {head}]"


def load(db: Session, scope: int, key: str):
    from app.modules.agent_hub.model import AgentConvSummary

    return db.scalar(select(AgentConvSummary).where(AgentConvSummary.scope == int(scope),
                                                    AgentConvSummary.scope_key == str(key)))


def summary_block(summary: str) -> str:
    """Khối đưa vào phần luật (system) của lượt gọi model."""
    if not summary.strip():
        return ""
    return ("TÓM TẮT PHẦN ĐẦU CUỘC TRÒ CHUYỆN NÀY (các lượt cũ đã được tóm; dùng để nhớ điều đã chốt, đối tượng đang bàn, "
            "việc còn dở — không nhắc lại nguyên văn cho người dùng):\n" + summary.strip())


def _summary_prompt(old: str, turns: list[Turn]) -> str:
    lines = []
    for t in turns:
        who = "Người dùng" if t.role == "user" else "Trợ lý"
        text = " ".join(_text_of(t.content).split())
        lines.append(f"{who}: {text[:TURN_CHARS_FOR_SUMMARY]}")
    head = f"TÓM TẮT CŨ:\n{old.strip()}\n\n" if old.strip() else ""
    return head + "CÁC LƯỢT MỚI CẦN GỘP VÀO:\n" + "\n".join(lines)


def _run_with_timeout(fn: Callable[[], object], seconds: int):
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        return pool.submit(fn).result(timeout=max(1, int(seconds)))
    finally:
        #  Không chờ lượt quá giờ chạy nốt — câu trả lời đi tiếp ngay; lượt kia xong thì bị bỏ.
        pool.shutdown(wait=False, cancel_futures=True)


def compact(db: Session, *, scope: int, key: str, user_id: int, turns: list[Turn], question: str,
            summarize: Callable[[str, str], object] | None,
            fallback: Callable[[], list[dict]], on_cost: Callable[[object], None] | None = None) -> Plan:
    """Dựng phần hội thoại cho một lượt gọi model. `turns` cũ → mới, đã bỏ phần trước mốc tóm (người gọi lấy SAU `upto_id`
    nếu muốn đỡ đọc; ở đây lọc lại cho chắc). `summarize(system, prompt)` trả ChatResult; `fallback()` = cửa sổ trượt cũ."""
    if not enabled():
        return Plan(turns=fallback(), level=LEVEL_FALLBACK)
    lim = limits()
    row = load(db, scope, key)
    summary = (row.summary if row is not None else "") or ""
    upto = int(row.upto_id or 0) if row is not None else 0
    turns = [t for t in turns if not (t.msg_id and t.msg_id <= upto)]
    keep_n = lim["keep"] * 2
    level = LEVEL_NONE

    total = _total(summary, turns, question)
    if total >= lim["clear"]:
        level = LEVEL_CLEAR
        cut = max(0, len(turns) - keep_n)
        turns = [Turn(t.role, _stub(t.content), t.msg_id, False) if (i < cut and t.tool) else t
                 for i, t in enumerate(turns)]
        total = _total(summary, turns, question)

    if total >= lim["summary"] and len(turns) > keep_n:
        old, recent = turns[:-keep_n], turns[-keep_n:]
        if summarize is None or not any(t.msg_id for t in old):
            return Plan(summary=summary, turns=fallback(), level=LEVEL_FALLBACK)
        prompt = _summary_prompt(summary, old)
        try:
            result = _run_with_timeout(lambda: summarize(SUMMARY_SYSTEM, prompt), settings.AI_COMPACT_TIMEOUT_SEC)
            new_summary = str(getattr(result, "text", "") or "").strip()[:SUMMARY_MAX_CHARS * 2]
            if not new_summary:
                raise ValueError("model trả bản tóm tắt rỗng")
        except (FutureTimeout, Exception) as e:  # noqa: BLE001 — tóm hỏng không được chặn câu trả lời
            log.warning("compaction: tóm tắt %s:%s hỏng (%s) — quay về cửa sổ trượt", scope, key, e)
            return Plan(summary=summary, turns=fallback(), level=LEVEL_FALLBACK)
        if on_cost is not None:
            try:
                on_cost(result)
            except Exception:  # noqa: BLE001 — ghi sổ chi phí hỏng thì thôi, bản tóm tắt vẫn dùng
                log.warning("compaction: ghi sổ chi phí lượt tóm hỏng", exc_info=True)
        save(db, scope=scope, key=key, user_id=user_id, summary=new_summary,
             upto_id=max(t.msg_id for t in old if t.msg_id), folded=len(old))
        summary, turns, level = new_summary, recent, LEVEL_SUMMARY
        total = _total(summary, turns, question)

    while total >= lim["drop"] and len(turns) > 2:
        level = LEVEL_DROP
        turns = turns[2:] if turns[0].role == "user" else turns[1:]
        total = _total(summary, turns, question)

    #  Lượt đầu gửi model phải là của người dùng (nhiều hãng từ chối hội thoại mở đầu bằng trợ lý).
    while turns and turns[0].role != "user":
        turns = turns[1:]
    return Plan(summary=summary, turns=[t.as_message() for t in turns], level=level, tokens=total)


def save(db: Session, *, scope: int, key: str, user_id: int, summary: str, upto_id: int, folded: int) -> None:
    from app.modules.agent_hub.model import AgentConvSummary

    row = load(db, scope, key)
    if row is None:
        row = AgentConvSummary(scope=int(scope), scope_key=str(key)[:80], user_id=int(user_id or 0),
                               created_by=int(user_id or 0))
        db.add(row)
    row.summary = summary
    row.upto_id = max(int(row.upto_id or 0), int(upto_id or 0))
    row.folded_turns = int(row.folded_turns or 0) + int(folded or 0)
    row.updated_by = int(user_id or 0)
    db.commit()


def forget(db: Session, scope: int, key: str) -> None:
    """Bỏ bản tóm tắt của một cuộc (xóa hội thoại web, cuộc chat mới sau quá lâu)."""
    row = load(db, scope, key)
    if row is not None:
        db.delete(row)
        db.flush()


def record_cost(db: Session, result, *, channel: str) -> None:
    """Token của lượt tóm vào sổ chi phí chung (`tab_agent_run`, bước «Tóm tắt hội thoại»), cùng phiên DB của lượt hỏi."""
    from app.modules.agent_hub import service as agent_service
    from app.modules.agent_hub.constants import STAGE_COMPACT

    run = agent_service.start_run(db, 0, STAGE_COMPACT)
    run.provider = str(getattr(result, "provider", "") or run.provider)[:30]
    run.model = str(getattr(result, "model", "") or run.model)[:80]
    agent_service.finish_run(db, run, result=result)
    run.artifact = {**(run.artifact or {}), "channel": channel}
