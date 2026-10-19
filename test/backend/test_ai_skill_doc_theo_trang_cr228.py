"""ai-CR-228 — đại ca nối ChatGPT vào dev 19/10/2026: hỏi «đọc chi tiết skill nha-may-he-thong-cong-viec + tệp đính kèm» thì
ChatGPT bảo «lần gọi công cụ không trả về nội dung», chỉ nhắc lại phần tóm tắt, không gọi read_skill_file (Claude gọi cùng
skill ra đủ ~35k ký tự). Hai nghi phạm, vá cả hai:
  - kết quả quá dài → read_skill / read_skill_file chia TRANG ~10k ký tự, cắt ở ranh giới tiêu đề / đoạn / dòng, có
    next_offset + total_chars; ghép các trang lại = NGUYÊN VĂN; offset vượt / âm / sai kiểu không vỡ;
  - câu dặn «đừng đọc lại nguyên văn… tài sản công ty» làm AI tưởng không được dùng → câu mới nói rõ ĐƯỢC dùng.
Kèm: nhật ký cổng ghi số ký tự kết quả mỗi lượt tools/call.
"""
import json

import pytest

from app.modules.ai_skill import handbook_seed, mcp_read
from app.modules.ai_skill.model import AiSkill, AiSkillVersion
from app.modules.user.model import User


def _doc(n_sections=14, size=2_800):
    parts = []
    for i in range(n_sections):
        body = "\n".join(f"Dòng {i}.{j}: " + "nội dung quy định " * 8 for j in range(size // 160))
        parts.append(f"## Mục {i}\n\n{body}\n")
    return "# Cẩm nang dài\n\n" + "\n".join(parts)


def test_ghep_cac_trang_bang_nguyen_van_va_cat_o_ranh_gioi():
    text = _doc()
    assert len(text) > 3 * mcp_read.PAGE_CHARS
    pages, offset = [], 0
    while offset is not None:
        page = mcp_read.page_of(text, offset)
        assert len(page["content"]) <= mcp_read.PAGE_CHARS and page["total_chars"] == len(text)
        pages.append(page)
        offset = page["next_offset"]
    assert "".join(p["content"] for p in pages) == text
    for p in pages[1:]:
        assert p["content"].startswith(("#", "Dòng")), p["content"][:30]     # trang sau mở bằng dòng mới, không giữa dòng
    assert all("offset=" in p["page_note"] for p in pages[:-1]) and "page_note" not in pages[-1]


def test_dong_dai_khong_co_cho_ngat_thi_cat_cung():
    text = "x" * (mcp_read.PAGE_CHARS * 2 + 7)
    a = mcp_read.page_of(text)
    b = mcp_read.page_of(text, a["next_offset"])
    c = mcp_read.page_of(text, b["next_offset"])
    assert a["content"] + b["content"] + c["content"] == text and c["next_offset"] is None


@pytest.mark.parametrize("offset", [10 ** 9, -5, "abc", None, 3.7])
def test_offset_la_khong_vo(offset):
    text = _doc(2)
    page = mcp_read.page_of(text, offset)
    assert isinstance(page["content"], str) and page["total_chars"] == len(text)
    if offset == 10 ** 9:
        assert page["content"] == "" and page["next_offset"] is None and "offset=0" in page["page_note"]


def test_noi_dung_ngan_mot_trang_va_rong():
    assert mcp_read.page_of("ngắn")["next_offset"] is None
    assert mcp_read.page_of("") == {"content": "", "offset": 0, "next_offset": None, "total_chars": 0, "page_note": ""}


@pytest.fixture
def factory_skill(db, seed):
    handbook_seed.ensure_system_handbook(db)
    skill = db.query(AiSkill).filter(AiSkill.slug == handbook_seed.FACTORY_SLUG).one()
    version = db.get(AiSkillVersion, skill.current_version_id)
    version.body_md = _doc()                                # dài như skill nhà máy thật (~35k ký tự)
    db.commit()
    return db.get(User, seed.u_req_id), version.body_md


def test_read_skill_qua_cong_mcp_doc_tiep_duoc_va_cau_dan_moi(db, factory_skill):
    from app.modules.agent_hub import mcp, mcp_keys

    user, body = factory_skill
    got, offset = "", 0
    for _ in range(10):
        out = mcp.call_tool(db, user, mcp_keys.SCOPE_READ, "read_skill", {"name": handbook_seed.FACTORY_SLUG, "offset": offset})
        got += out["content"]
        offset = out["next_offset"]
        if offset is None:
            break
    assert got == body and out["files"]
    assert "Dùng nội dung này" in out["note"] and "read_skill_file" in out["note"] and "tài sản" not in out["note"]
    defs = {d["name"]: d for d in mcp.SKILL_TOOL_DEFS}
    assert "offset" in defs["read_skill"]["inputSchema"]["properties"] and "next_offset" in defs["read_skill"]["description"]
    assert "không đọc lại nguyên văn cho người dùng" not in defs["read_skill"]["description"]
    path = out["files"][0]["path"]
    f = mcp.call_tool(db, user, mcp_keys.SCOPE_READ, "read_skill_file",
                      {"name": handbook_seed.FACTORY_SLUG, "path": path, "offset": "sai"})
    assert f["offset"] == 0 and f["content"] and f["total_chars"] >= len(f["content"])


def test_cong_cu_noi_bo_cung_chia_trang(db, factory_skill):
    from app.modules.assistant.tools import run_tool

    user, body = factory_skill
    first = run_tool(db, user, "read_skill", {"name": handbook_seed.FACTORY_SLUG})
    second = run_tool(db, user, "read_skill", {"name": handbook_seed.FACTORY_SLUG, "offset": first["next_offset"]})
    assert body.startswith(first["content"] + second["content"])


def test_nhat_ky_ghi_so_ky_tu_ket_qua(db, factory_skill, monkeypatch):
    from fastapi.testclient import TestClient

    from app.core.config import settings
    from app.core.database import get_db
    from app.main import app
    from app.modules.agent_hub import mcp_keys, mcp_log
    from app.modules.agent_hub.model import AgentMcpCall

    monkeypatch.setattr(settings, "AGENT_ERP_URL", "https://deverp.degoholding.vn")
    monkeypatch.setattr(mcp_log, "_redis", lambda: (_ for _ in ()).throw(ConnectionError("không Redis")))
    monkeypatch.setattr(mcp_log, "_mem", {})
    user, _ = factory_skill
    _row, raw = mcp_keys.create(db, user.id, name="ChatGPT")
    app.dependency_overrides[get_db] = lambda: db
    try:
        res = TestClient(app).post("/api/mcp", headers={"Authorization": f"Bearer {raw}", "Content-Type": "application/json"},
                                   content=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
                                       "name": "read_skill", "arguments": {"name": handbook_seed.FACTORY_SLUG}}}))
    finally:
        app.dependency_overrides.pop(get_db, None)
    text = res.json()["result"]["content"][0]["text"]
    row = db.query(AgentMcpCall).filter(AgentMcpCall.tool == "read_skill").order_by(AgentMcpCall.id.desc()).first()
    assert row.result_chars == len(text) and 0 < row.result_chars < mcp_read.PAGE_CHARS + 3_000
    assert mcp_log.serialize(row)["result_chars"] == row.result_chars
