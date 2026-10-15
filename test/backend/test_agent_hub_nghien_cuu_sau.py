"""ai-CR-178 (phase 23.1 + 23.2) — nghiên cứu sâu nhiều câu tìm con và tổng hợp nhiều tài liệu (`agent_hub/deep_research.py`).

Mọi bài có lưới chặn mạng: `web_search.requests.get/post` ném lỗi nếu lỡ ra Internet; máy tìm / đọc trang / model đều giả.
"""
from __future__ import annotations

import contextlib
import io
import json
import zipfile

import pytest

from app.modules.agent_hub import deep_research as dr
from app.modules.agent_hub import web_search
from app.modules.agent_hub.constants import ACT_ASKED, ACT_DOC_WAIT, DIR_IN
from app.modules.assistant.provider.base import ChatResult

CHAT = "12345"
REPORT_WEB = (
    "## TÓM TẮT\n- Giá thép **tăng 5%** trong quý 4 [1]\n- Nhu cầu xây dựng hồi phục [2]\n"
    "## PHÁT HIỆN CHÍNH\n### 1. Giá hiện tại\n- Thép phi 10 Hòa Phát **15.250 đ/kg** [1]\n### 2. Dự báo\n- Dự báo tăng nhẹ [2][3]\n"
    "## CHỖ MÂU THUẪN / CHƯA CHẮC\n- [1] nói tăng 5%, [3] nói tăng 3%\n"
    "## KẾT LUẬN VÀ KHUYẾN NGHỊ\n- Nên chốt giá sớm trong tháng 10 [1][2]\n- Theo dõi giá phôi [3]\n"
)
REPORT_DOCS = (
    "## ĐIỂM CHUNG\n- Cả hai cùng nói doanh thu tăng [1][2]\n"
    "## ĐIỂM KHÁC VÀ MÂU THUẪN\n- [1] ghi 10%, [2] ghi 12%\n"
    "## TÓM TẮT TỪNG TÀI LIỆU\n### [1] Báo cáo A\n- Doanh thu 10%\n### [2] Báo cáo B\n- Doanh thu 12%\n"
    "## KẾT LUẬN\n- Kiểm lại số doanh thu [1][2]\n"
)


class FakeProvider:
    """Model giả: `answer` là chuỗi hoặc hàm (system, content) → chuỗi; ghi lại từng lượt."""

    def __init__(self, answer, *, tokens=(1000, 500)):
        self.answer, self.tokens, self.calls = answer, tokens, []

    def ask(self, messages, *, system=None, max_tokens=1024, temperature=0.3, model=None, **kw):
        content = messages[0].content
        self.calls.append({"system": system or "", "content": content, "model": model})
        text = self.answer(system or "", content) if callable(self.answer) else self.answer
        return ChatResult(text=text, provider="deepseek", model="deepseek-v4.1-flash",
                          input_tokens=self.tokens[0], output_tokens=self.tokens[1])


@pytest.fixture(autouse=True)
def _chan_mang(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("bài kiểm không được ra mạng")

    monkeypatch.setattr(web_search.requests, "get", boom)
    monkeypatch.setattr(web_search.requests, "post", boom)
    monkeypatch.setattr(web_search, "public_url", lambda u: u.startswith("http") and not u.startswith(("http://10.", "http://127.")))


@pytest.fixture
def env(db, monkeypatch):
    """Cắm bot vào chỗ trống: tin gửi, tệp Word, lượt giao Celery đều ghi lại; không Drive; model rẻ."""
    from app.modules.agent_hub import service

    sent: list[str] = []
    files: list[tuple[str, bytes]] = []
    dispatched: list[int] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    monkeypatch.setattr(dr.telegram, "send_document", lambda chat_id, name, data, **kw: files.append((name, data)) or 1)
    monkeypatch.setattr(dr.telegram, "send_chat_action", lambda *a, **k: None)
    monkeypatch.setattr(dr, "dispatch", lambda job_id: dispatched.append(int(job_id)))
    monkeypatch.setattr(dr, "_google_link", lambda db, uid: None)
    monkeypatch.setattr(dr, "_author_of", lambda db, uid: "Người kiểm")
    monkeypatch.setattr(dr.user_keys, "for_chat", lambda db, chat_id: contextlib.nullcontext())
    monkeypatch.setattr(dr, "_model_name", lambda: "deepseek-v4.1-flash")
    return {"sent": sent, "files": files, "dispatched": dispatched}


def _use(monkeypatch, provider: FakeProvider) -> FakeProvider:
    monkeypatch.setattr(dr.manager, "get_provider", lambda: provider)
    return provider


def _web(monkeypatch, pages: dict[str, str] | None = None):
    """Máy tìm giả: mỗi câu ra 3 kết quả (một trùng URL giữa các câu, một địa chỉ nội bộ); đọc trang trả chữ."""
    pages = pages or {}

    def fake_search(q, limit=8):
        slug = q.split()[0].lower()
        return [{"title": f"Bài về {q}", "url": f"https://bao.vn/{slug}", "snippet": "..."},
                {"title": "Trang chung", "url": "https://chung.vn/thep/", "snippet": "..."},
                {"title": "Nội bộ", "url": "http://10.0.0.5/admin", "snippet": "..."},
                {"title": "Trang chung (trùng)", "url": "https://www.chung.vn/thep", "snippet": "..."}]

    def fake_article(url):
        return {"url": url, "title": f"Tiêu đề {url}", "description": "mô tả", "preview_only": False,
                "text": pages.get(url, "Giá thép phi 10 Hòa Phát 15.250 đ/kg, cập nhật 10/2026. " * 20)}

    monkeypatch.setattr(web_search, "search", fake_search)
    monkeypatch.setattr(web_search, "fetch_article", fake_article)


def _docx_xml(data: bytes) -> str:
    return zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml").decode("utf-8")


# ---------------------------------------------------------------------------
# Nhận lệnh
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text,kind,q", [
    ("nghiên cứu sâu: giá thép xây dựng quý 4", dr.KIND_WEB, "giá thép xây dựng quý 4"),
    ("Nghiên cứu kỹ giúp anh thuế nhập khẩu phân bón 2026", dr.KIND_WEB, "thuế nhập khẩu phân bón 2026"),
    ("báo cáo nghiên cứu về thị trường xi măng miền Tây", dr.KIND_WEB, "thị trường xi măng miền Tây"),
    ("em nghien cuu sau ve gia dong the gioi", dr.KIND_WEB, "gia dong the gioi"),
    ("deep research: lithium battery supply chain", dr.KIND_WEB, "lithium battery supply chain"),
    ("tổng hợp các tài liệu này https://a.vn/x.pdf https://b.vn/y.pdf", dr.KIND_DOCS, "tổng hợp các tài liệu này"),
    ("so sánh 2 báo cáo đính kèm giúp anh", dr.KIND_DOCS, "so sánh 2 báo cáo đính kèm giúp anh"),
])
def test_nhan_lenh_dung(text, kind, q):
    assert dr.parse_command(text) == (kind, q)


@pytest.mark.parametrize("text", [
    "nghiên cứu thị trường là gì", "anh đang nghiên cứu sâu về cái này", "giá thép hôm nay", "tổng hợp công nợ tháng 9",
    "/tim giá vàng", "nghiên cứu sinh là gì",
])
def test_cau_thuong_khong_phai_lenh(text):
    assert dr.parse_command(text) is None


def test_lenh_chat_di_dung_duong(db, env, monkeypatch):
    from app.modules.agent_hub import service

    started: list[tuple] = []
    monkeypatch.setattr(dr, "start", lambda db, chat_id, uid, kind, q, items=None: started.append((kind, q, items)))
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": type("U", (), {"id": 7})())
    monkeypatch.setattr(service.user_keys, "active_key", lambda: "k")

    def row(text, **kw):
        r = service.log_message(db, DIR_IN, CHAT, 1, text, **kw)
        db.commit()
        return r

    assert service._deep_research_by_text(db, CHAT, row("nghiên cứu sâu: giá thép"), "nghiên cứu sâu: giá thép")
    assert started[-1][:2] == (dr.KIND_WEB, "giá thép")
    assert not service._deep_research_by_text(db, CHAT, row("nghiên cứu thị trường là gì"), "nghiên cứu thị trường là gì")
    #  «tổng hợp các tài liệu này» mà không có tệp / link nào → không phải lệnh (để Trợ lý ERP trả lời).
    assert not service._deep_research_by_text(db, CHAT, row("tổng hợp các tài liệu này"), "tổng hợp các tài liệu này")
    #  Có hai tệp gửi trước (một đang chờ câu hỏi) + một link → gom cả ba; tệp đang chờ bị giành (không trả lời hai lần).
    f1 = row("[tệp a.pdf]", action=ACT_DOC_WAIT)
    f1.files = [{"kind": "doc", "file_id": "F1", "name": "a.pdf", "mime": "application/pdf"}]
    f2 = row("[tệp b.docx] tóm tắt", action=ACT_ASKED)
    f2.files = [{"kind": "doc", "file_id": "F2", "name": "b.docx", "mime": ""}]
    db.commit()
    text = "so sánh các tài liệu này https://bao.vn/c"
    assert service._deep_research_by_text(db, CHAT, row(text), text)
    kind, q, items = started[-1]
    assert kind == dr.KIND_DOCS and {i["type"] for i in items} == {"url", "tg"} and len(items) == 3
    db.refresh(f1)
    assert f1.action == ACT_ASKED
    #  Chưa đăng nhập ERP → câu hướng dẫn sẵn có, không khởi động.
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": None)
    n = len(started)
    assert service._deep_research_by_text(db, CHAT, row("nghiên cứu sâu: x y"), "nghiên cứu sâu: x y")
    assert len(started) == n and "đăng nhập" in env["sent"][-1]


# ---------------------------------------------------------------------------
# Lập câu con + ước chi phí + thẻ ok / thôi
# ---------------------------------------------------------------------------
def test_lap_cau_con_tu_json_model(db, env, monkeypatch):
    fake = _use(monkeypatch, FakeProvider('```json\n{"queries": ["giá thép quý 4 2026", "nguyên nhân giá thép tăng", '
                                          '"dự báo giá thép 2027", "giá thép quý 4 2026"], "english": ["steel price Q4 2026"]}\n```'))
    row = dr.create_job(db, CHAT, 7, dr.KIND_WEB, "giá thép xây dựng quý 4")
    qs = dr.plan_queries(db, row, "giá thép xây dựng quý 4")
    assert qs == ["giá thép quý 4 2026", "nguyên nhân giá thép tăng", "dự báo giá thép 2027", "steel price Q4 2026"]
    assert "JSON" in fake.calls[0]["system"]
    assert dr.job_runs(db, row.id) and dr.job_runs(db, row.id)[0].artifact["step"] == "plan"
    #  Model trả rác → vẫn đủ MIN_QUERIES câu, không hỏi lại.
    _use(monkeypatch, FakeProvider("em không hiểu"))
    assert len(dr.plan_queries(db, row, "giá thép")) == dr.MIN_QUERIES


def test_uoc_chi_phi_duoi_va_tren_nguong(monkeypatch):
    monkeypatch.setattr(dr, "_model_name", lambda: "deepseek-v4.1-flash")
    cheap = dr.estimate_web(5)
    assert 0 < cheap["usd"] < dr.meetings.COST_CONFIRM_USD and cheap["minutes"] >= 2
    monkeypatch.setattr(dr, "_model_name", lambda: "deepseek-v4-pro")
    dear = dr.estimate_web(5)
    assert dear["usd"] >= dr.meetings.COST_CONFIRM_USD
    assert dr.needs_ok({"ok": False}, dear) and not dr.needs_ok({"ok": True}, dear) and not dr.needs_ok({"ok": False}, cheap)
    assert dr.estimate_docs(200_000, 2)["usd"] > dr.estimate_docs(5_000, 2)["usd"]


def test_re_thi_chay_luon_dat_thi_hoi_ok_roi_moi_chay(db, env, monkeypatch):
    from app.modules.agent_hub import service

    _use(monkeypatch, FakeProvider('{"queries": ["a 1", "b 2", "c 3"]}'))
    out = dr.start(db, CHAT, 7, dr.KIND_WEB, "giá thép quý 4")
    assert out["status"] == dr.ST_QUEUED and env["dispatched"] == [out["job_id"]]
    assert "bắt đầu nghiên cứu" in env["sent"][-1] and "1. a 1" in env["sent"][-1] and "Ước tính" not in env["sent"][-1]
    #  Model đắt → thẻ hỏi, chưa giao chạy.
    monkeypatch.setattr(dr, "_model_name", lambda: "deepseek-v4-pro")
    out = dr.start(db, CHAT, 7, dr.KIND_WEB, "giá đồng thế giới")
    assert out["status"] == dr.ST_WAITING and len(env["dispatched"]) == 1
    assert "Ước tính chi phí" in env["sent"][-1] and "<code>ok</code>" in env["sent"][-1] and "thôi" in env["sent"][-1]
    msg = service.log_message(db, DIR_IN, CHAT, 5, "ok")
    db.commit()
    assert dr.cost_ok_by_text(db, CHAT, msg, "ok") and env["dispatched"][-1] == out["job_id"]
    job = dr._load(db.get(dr.AgentMessage, out["job_id"]))
    assert job["status"] == dr.ST_QUEUED and job["ok"] is True and "làm luôn" in env["sent"][-1]
    #  «ok» lần nữa khi không còn thẻ chờ → không nhận (để các đường khác xử).
    msg2 = service.log_message(db, DIR_IN, CHAT, 6, "ok")
    db.commit()
    assert not dr.cost_ok_by_text(db, CHAT, msg2, "ok")
    #  «thôi» trên thẻ khác → bỏ việc, không chạy.
    out2 = dr.start(db, CHAT, 7, dr.KIND_WEB, "giá nhôm")
    msg3 = service.log_message(db, DIR_IN, CHAT, 7, "thôi")
    db.commit()
    assert dr.cost_ok_by_text(db, CHAT, msg3, "thôi") and out2["job_id"] not in env["dispatched"]
    assert dr._load(db.get(dr.AgentMessage, out2["job_id"]))["status"] == dr.ST_DROPPED and "không làm" in env["sent"][-1]


# ---------------------------------------------------------------------------
# Gom nguồn, báo cáo, tin chat, Word
# ---------------------------------------------------------------------------
def test_gom_nguon_bo_trung_chi_public(monkeypatch):
    _web(monkeypatch)
    sources, blocks = dr.gather_sources(["giá thép", "dự báo thép"])
    urls = [s["url"] for s in sources]
    assert len(urls) == len(set(dr._norm_url(u) for u in urls)) and not any("10.0.0.5" in u for u in urls)
    assert "https://chung.vn/thep/" in urls and "https://www.chung.vn/thep" not in urls
    assert all(len(pages) <= dr.READ_PAGES for _q, pages in blocks) and [s["n"] for s in sources] == list(range(1, len(sources) + 1))
    assert sources[0]["fetched"] and sources[0]["site"] == "bao.vn"


def test_bao_cao_du_5_muc_trich_nguon_tin_chat_va_word(db, env, monkeypatch):
    _web(monkeypatch)
    #  Model bỏ mục «mâu thuẫn» → được chèn; báo cáo vẫn đủ các mục cố định.
    fake = _use(monkeypatch, FakeProvider(REPORT_WEB.replace("## CHỖ MÂU THUẪN / CHƯA CHẮC\n- [1] nói tăng 5%, [3] nói tăng 3%\n", "")))
    row = dr.create_job(db, CHAT, 7, dr.KIND_WEB, "giá thép xây dựng quý 4", queries=["giá thép quý 4", "dự báo thép 2027"])
    out = dr.run_job(db, row.id)
    assert out["status"] == dr.ST_DONE and out["sources"] >= 2
    job = dr._load(db.get(dr.AgentMessage, row.id))
    for h in dr.HEADINGS[dr.KIND_WEB]:
        assert f"## {h}" in job["report"]
    assert "[1]" in job["report"] and "Model chưa viết mục này" in job["report"]
    assert "DANH MỤC NGUỒN" in fake.calls[-1]["content"] and "Câu con 1: giá thép quý 4" in fake.calls[-1]["content"]
    #  Tin chat: rút gọn ≤ 1800 ký tự, có tóm tắt + kết luận + dòng chỉ bản đầy đủ; chi phí nhỏ thì không báo.
    chat = env["sent"][-1]
    assert len(chat) <= dr.CHAT_MAX and "NGHIÊN CỨU SÂU" in chat and "**KẾT LUẬN**" in chat and dr.FULL_LINE in chat
    assert "Chi phí lượt này" not in chat
    #  Word chuẩn DEGO có mục nguồn với tiêu đề trang.
    name, data = env["files"][-1]
    assert name.startswith("nghien-cuu-") and name.endswith(".docx")
    xml = _docx_xml(data)
    assert "DANH MỤC NGUỒN" in xml and "Tiêu đề https://bao.vn/giá" in xml and "BÁO CÁO NGHIÊN CỨU" in xml
    assert "KẾT LUẬN VÀ KHUYẾN NGHỊ" in xml
    #  Sổ chi phí: lượt viết gắn job_id, bước «report».
    steps = [r.artifact["step"] for r in dr.job_runs(db, row.id)]
    assert "report" in steps and job["steps"][-1] == "gửi Word" and "cost_usd" in job


def test_chi_phi_that_lon_thi_bao_cuoi_tin(db, env, monkeypatch):
    _web(monkeypatch)
    _use(monkeypatch, FakeProvider(REPORT_WEB, tokens=(300_000, 20_000)))     # ~0,8 USD với deepseek-v4.1-flash
    row = dr.create_job(db, CHAT, 7, dr.KIND_WEB, "giá thép", queries=["giá thép"])
    assert dr.run_job(db, row.id)["cost_usd"] >= dr.COST_REPORT_USD
    assert "Chi phí lượt này khoảng $" in env["sent"][-1] and len(env["sent"][-1]) <= dr.CHAT_MAX


def test_tin_chat_cat_vua_1800():
    long = "## TÓM TẮT\n" + "\n".join(f"- Ý số {i} " + "rất dài " * 20 for i in range(40)) + \
           "\n## KẾT LUẬN VÀ KHUYẾN NGHỊ\n" + "\n".join(f"- Kết luận {i} " + "dài " * 30 for i in range(20))
    text = dr.chat_text(long, "Giá thép", dr.KIND_WEB)
    assert len(text) <= dr.CHAT_MAX and text.endswith(dr.FULL_LINE) and "- Ý số 0" in text


def test_khong_tim_duoc_nguon_thi_bao_ro_buoc(db, env, monkeypatch):
    monkeypatch.setattr(web_search, "search", lambda q, limit=8: [])
    _use(monkeypatch, FakeProvider(REPORT_WEB))
    row = dr.create_job(db, CHAT, 7, dr.KIND_WEB, "giá thép", queries=["giá thép"])
    assert dr.run_job(db, row.id)["status"] == "error"
    assert "bị hỏng giữa chừng" in env["sent"][-1] and "chưa bước nào" in env["sent"][-1] and not env["files"]
    assert dr._load(db.get(dr.AgentMessage, row.id))["status"] == dr.ST_FAILED


# ---------------------------------------------------------------------------
# 23.2 — tổng hợp tài liệu
# ---------------------------------------------------------------------------
def _docs(monkeypatch, texts: dict[str, str]):
    from app.modules.agent_hub import doc_text

    monkeypatch.setattr(web_search, "fetch_resource", lambda url, max_bytes: {
        "kind": "doc", "url": url, "name": url.rsplit("/", 1)[-1], "mime": "application/pdf", "data": b"%PDF"})
    monkeypatch.setattr(doc_text, "extract", lambda name, mime, data: texts[name])
    monkeypatch.setattr(dr.telegram, "download_file", lambda fid, max_bytes: (b"x", "application/pdf"))


def test_tong_hop_hai_tai_lieu_ra_bang_so_sanh(db, env, monkeypatch):
    _docs(monkeypatch, {"a.pdf": "Báo cáo A: doanh thu tăng 10%. " * 30, "b.docx": "Báo cáo B: doanh thu tăng 12%. " * 30})
    fake = _use(monkeypatch, FakeProvider(REPORT_DOCS))          # model quên bảng → hệ thống chèn bảng tối thiểu
    items = [{"type": "url", "ref": "https://bao.vn/a.pdf", "name": "a.pdf", "url": "https://bao.vn/a.pdf"},
             {"type": "tg", "ref": "F2", "name": "b.docx", "mime": ""}]
    out = dr.start(db, CHAT, 7, dr.KIND_DOCS, "so sánh các tài liệu này", items=items)
    assert out["status"] == dr.ST_QUEUED and "2 tài liệu" in env["sent"][-1]
    assert dr.run_job(db, out["job_id"])["status"] == dr.ST_DONE
    job = dr._load(db.get(dr.AgentMessage, out["job_id"]))
    assert "BẮT BUỘC có một bảng" in fake.calls[-1]["system"] and "[2] b.docx" in fake.calls[-1]["content"]
    for h in dr.HEADINGS[dr.KIND_DOCS]:
        assert f"## {h}" in job["report"]
    assert "| Tiêu chí | [1] a.pdf | [2] b.docx |" in job["report"] and "| Độ dài (chữ) |" in job["report"]
    assert job["estimate"]["docs"] == 2
    chat = env["sent"][-1]
    assert "TỔNG HỢP TÀI LIỆU" in chat and "**ĐIỂM CHUNG**" in chat and len(chat) <= dr.CHAT_MAX
    name, data = env["files"][-1]
    xml = _docx_xml(data)
    assert name.startswith("tong-hop-") and "TỔNG HỢP TÀI LIỆU" in xml and "a.pdf" in xml and "DANH MỤC NGUỒN" in xml


def test_tai_lieu_dai_thi_hoi_ok_truoc_khi_viet(db, env, monkeypatch):
    _docs(monkeypatch, {"a.pdf": "x" * 150_000, "b.pdf": "y" * 150_000})
    monkeypatch.setattr(dr, "_model_name", lambda: "deepseek-v4-pro")
    fake = _use(monkeypatch, FakeProvider(REPORT_DOCS))
    items = [{"type": "url", "ref": "https://bao.vn/a.pdf", "name": "a.pdf"}, {"type": "url", "ref": "https://bao.vn/b.pdf", "name": "b.pdf"}]
    out = dr.start(db, CHAT, 7, dr.KIND_DOCS, "tổng hợp", items=items)
    res = dr.run_job(db, out["job_id"])
    assert res["status"] == dr.ST_WAITING and fake.calls == [] and "Ước tính chi phí" in env["sent"][-1]
    assert "2 tài liệu" in env["sent"][-1]
    from app.modules.agent_hub import service

    msg = service.log_message(db, DIR_IN, CHAT, 9, "ok")
    db.commit()
    assert dr.cost_ok_by_text(db, CHAT, msg, "ok") and env["dispatched"][-1] == out["job_id"]
    assert dr.run_job(db, out["job_id"])["status"] == dr.ST_DONE and len(fake.calls) >= 1


def test_tai_lieu_hong_mot_cai_van_viet_va_ghi_ro(db, env, monkeypatch):
    from app.modules.agent_hub import doc_text

    monkeypatch.setattr(web_search, "fetch_resource", lambda url, max_bytes: {"kind": "none", "reason": "too_large"} if "to" in url
                        else {"kind": "page"})
    monkeypatch.setattr(web_search, "fetch_article", lambda url: {"url": url, "title": "Bài báo", "description": "",
                                                                   "text": "Nội dung bài báo " * 50, "preview_only": False})
    monkeypatch.setattr(doc_text, "extract", lambda name, mime, data: "")
    docs, failed = dr.read_items(db, [{"type": "url", "ref": "https://bao.vn/to.pdf", "name": "to.pdf"},
                                      {"type": "url", "ref": "https://bao.vn/bai", "name": "bai"}], 7)
    assert [d["kind"] for d in docs] == ["bài viết"] and failed == ["to.pdf: tệp quá lớn"]


# ---------------------------------------------------------------------------
# Chỗ cắm: tool Trợ lý, nhóm công cụ, sổ ý định, hướng dẫn
# ---------------------------------------------------------------------------
def test_tool_deep_research_khoi_dong_ve_chat_rieng(db, env, monkeypatch):
    from app.modules.agent_hub import meeting_drive
    from app.modules.assistant import tool_router as tr
    from app.modules.assistant import tools as T
    from app.modules.assistant.tools import research_tool as rt

    assert "deep_research" in {d.name for d in T.tool_defs()}
    assert "deep_research" in tr.select("nghiên cứu sâu giá thép xây dựng") and tr.select("giá thép hôm nay") is not None
    started: list = []
    monkeypatch.setattr(dr, "start", lambda db, chat_id, uid, kind, q, items=None: started.append((chat_id, uid, kind, q))
                        or {"status": dr.ST_QUEUED, "job_id": 1})
    ctx = type("C", (), {"db": db, "user": type("U", (), {"id": 7})()})()
    monkeypatch.setattr(meeting_drive, "private_chat", lambda db, uid: "")
    out = rt._deep_research(ctx, {"question": "giá thép quý 4"})
    assert "error" in out and "/dangnhap" in out["error"] and started == []
    monkeypatch.setattr(meeting_drive, "private_chat", lambda db, uid: CHAT)
    out = rt._deep_research(ctx, {"question": "giá thép quý 4"})
    assert out["started"] and started == [(CHAT, 7, dr.KIND_WEB, "giá thép quý 4")] and "chat riêng" in out["message"]


def test_so_y_dinh_va_huong_dan():
    from app.modules.agent_hub import intent_ledger as il
    from app.modules.agent_hub import user_guide

    assert il.sub_of(il.Intent.RESEARCH, [], "deep") == il.Sub.RESEARCH_WEB
    assert il.sub_of(il.Intent.RESEARCH, [], "deep_docs") == il.Sub.RESEARCH_DOCUMENT
    assert il.sub_of(il.Intent.ASK, ["deep_research"]) == il.Sub.RESEARCH_WEB
    text = json.dumps([list(s.items) for s in user_guide.SECTIONS], ensure_ascii=False) if hasattr(user_guide, "SECTIONS") \
        else open(user_guide.__file__, encoding="utf-8").read()
    assert "nghiên cứu sâu" in text and "tổng hợp các tài liệu này" in text


def test_nghien_cuu_sau_uu_tien_claude_sonnet_du_so_khoa_deepseek_dung_dau(monkeypatch):
    """Đại ca 15/10: báo cáo nghiên cứu sâu đang do DeepSeek viết (khóa DeepSeek đứng đầu sổ, GIỮ thứ tự sổ). Mọi lượt
    model của nghiên cứu sâu ưu tiên khóa Claude với Sonnet — kể cả khi đang trong luồng thường xin Haiku; không Kimi."""
    from app.modules.agent_hub import user_keys
    from app.modules.agent_hub.ai_keys import KeyRef

    tram = "https://modelapi.vn/v1"
    chain = [KeyRef(provider="openai_compat", key="k1", model="deepseek-v4.1-flash", base_url=tram, row_id=1),
             KeyRef(provider="openai_compat", key="k2", model="kimi-k3", base_url=tram, row_id=2),
             KeyRef(provider="openai_compat", key="k3", model="claude-sonnet-5-5", base_url=tram, row_id=3)]
    with user_keys.use_chain(chain, 238):
        with user_keys.prefer(["claude"], model="claude-haiku-5-5"):          # như luồng thường của lõi mới
            with dr._claude_first():
                assert user_keys.active_ref().model == "claude-sonnet-5-5"
                assert [r.model for r in user_keys.chain()][:2] == ["claude-sonnet-5-5", "deepseek-v4.1-flash"]
    #  Ước chi phí theo giá Claude qua trạm (vào 4 × ghi bộ đệm 2 / ra 20), không theo giá DeepSeek.
    est = dr.estimate_web(5)
    t_in, t_out = dr._rates()
    assert (t_in, t_out) == (8.0, 20.0) and est["usd"] > 0
