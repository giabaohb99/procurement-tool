"""ai-CR-197 — một trạm (hãng tùy chỉnh) bán nhiều gói: khóa Kimi thêm sau KHÔNG được thay khóa Claude.

Lỗi 14/10/2026: đại ca thêm khóa thứ hai cùng trạm modelapi.vn (Claude) thì màn Khóa AI đóng luôn khóa DeepSeek cũ —
`add_key` coi «cùng hãng» = cùng `provider`, mà mọi gói của trạm đều là `openai_compat`. Nay cùng hãng với trạm tùy
chỉnh nghĩa là cùng trạm + cùng model; hãng thường (gemini, claude…) vẫn thay khóa như cũ.
"""
from app.modules.agent_hub import ai_keys

TRAM = "https://modelapi.vn/v1"


def _add(db, owner_id, raw, *, provider=ai_keys.PROVIDER_CUSTOM, model="", base_url=TRAM, priority=0):
    return ai_keys.add_key(db, owner_type=ai_keys.OWNER_USER, owner_id=owner_id, provider=provider, raw=raw,
                           model=model, base_url=base_url, priority=priority, check=False)


def _rows(db, owner_id):
    return [(r.model, r.key_hint, int(r.priority)) for r in ai_keys.active_rows(db, ai_keys.OWNER_USER, owner_id)]


def test_cung_tram_khac_model_them_dong_moi_khong_thay(db):
    ai_keys.clear_cache()
    _add(db, 7, "sk-tram-deepseek-abcdefgh-0001", model="deepseek-v4.1-flash")
    _add(db, 7, "sk-tram-claude-abcdefghij-0002", model="claude-sonnet-5-5")
    _add(db, 7, "sk-tram-kimi-abcdefghijkl-0003", model="kimi-k3")
    #  Ba gói, ba dòng sống, ưu tiên nối tiếp theo thứ tự thêm.
    assert _rows(db, 7) == [("deepseek-v4.1-flash", "0001", 1), ("claude-sonnet-5-5", "0002", 2), ("kimi-k3", "0003", 3)]


def test_cung_tram_cung_model_thi_thay_khoa_giu_cho_uu_tien(db):
    ai_keys.clear_cache()
    _add(db, 8, "sk-tram-claude-abcdefghij-0002", model="claude-sonnet-5-5")
    _add(db, 8, "sk-tram-kimi-abcdefghijkl-0003", model="kimi-k3")
    _add(db, 8, "sk-tram-claude-moi-abcdefgh-0009", model="claude-sonnet-5-5")
    #  Khóa Claude mới thay khóa Claude cũ ở đúng ưu tiên 1; Kimi không bị đụng.
    assert _rows(db, 8) == [("claude-sonnet-5-5", "0009", 1), ("kimi-k3", "0003", 2)]


def test_khac_tram_cung_model_cung_la_dong_rieng(db):
    ai_keys.clear_cache()
    _add(db, 9, "sk-tram-a-claude-abcdefgh-0011", model="claude-sonnet-5-5", base_url="https://tram-a.vn/v1")
    _add(db, 9, "sk-tram-b-claude-abcdefgh-0012", model="claude-sonnet-5-5", base_url="https://tram-b.vn/v1")
    assert [r.key_hint for r in ai_keys.active_rows(db, ai_keys.OWNER_USER, 9)] == ["0011", "0012"]


def test_hang_thuong_van_thay_khoa_nhu_cu(db):
    ai_keys.clear_cache()
    _add(db, 10, "AIzaSy-gemini-cu-abcdefgh-0001", provider="gemini", base_url="")
    _add(db, 10, "AIzaSy-gemini-moi-abcdefgh-0002", provider="gemini", base_url="")
    assert [r.key_hint for r in ai_keys.active_rows(db, ai_keys.OWNER_USER, 10)] == ["0002"]
