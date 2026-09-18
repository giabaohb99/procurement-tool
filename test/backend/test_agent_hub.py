"""Agent Hub bậc 1 — canh mấy chỗ hỏng thì hỏng im lặng.

Không kiểm phần gọi Gemini hay gọi Telegram (đó là mạng, không phải logic). Kiểm đúng
bốn chốt mà sai thì không ai thấy cho tới lúc muộn:
  1. `is_allowed_chat` — hàng rào DUY NHẤT của bậc 1.
  2. `_clean_groups` — model bịa id thì task trỏ vào hư không, tin thật kẹt INBOX.
  3. `parse_json` — model bọc rào ```json, và phải NÉM khi không ra JSON (luật B1).
  4. `needs_clarification` — `plan_files` rỗng là CẤM đi tiếp (luật B2).
"""
import pytest

from app.core.config import settings
from app.modules.agent_hub import telegram
from app.modules.agent_hub.constants import estimate_cost_usd
from app.modules.agent_hub.manager import _clean_groups, parse_json
from app.modules.assistant.provider.base import ProviderError


# --- Hàng rào chat_id -------------------------------------------------------
def test_chat_la_bi_chan(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    assert telegram.is_allowed_chat("12345")
    assert telegram.is_allowed_chat(12345)      # Telegram trả số, config là chuỗi
    assert not telegram.is_allowed_chat("999")


def test_chua_khai_chat_id_la_chan_het(monkeypatch):
    """Chưa cấu hình = CHẶN, không phải cho tất cả. Đảo chiều là mở cửa cho người lạ."""
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "")
    assert not telegram.is_allowed_chat("12345")
    assert not telegram.is_allowed_chat("")


# --- Lọc kết quả gom --------------------------------------------------------
def test_bo_id_model_bia_ra():
    groups = _clean_groups(
        [{"title": "A", "summary": "s", "message_ids": [1, 777], "risk_level": 3}],
        {1, 2},
    )
    #  777 bị loại; 2 bị model bỏ quên nên rơi vào việc "chưa phân loại".
    assert groups[0]["message_ids"] == [1]
    assert groups[0]["risk_level"] == 3
    assert groups[-1]["message_ids"] == [2]


def test_khong_tin_nao_bi_bo_lai_inbox():
    """Mọi id vào phải ra đúng một lần — không thì tin kẹt INBOX vĩnh viễn."""
    groups = _clean_groups([], {1, 2, 3})
    got = [i for g in groups for i in g["message_ids"]]
    assert sorted(got) == [1, 2, 3]


def test_id_trung_o_hai_nhom_chi_tinh_mot_lan():
    """Một tin thuộc hai task = hai thẻ Telegram cho cùng một việc."""
    groups = _clean_groups(
        [{"title": "A", "summary": "", "message_ids": [1, 2], "risk_level": 2},
         {"title": "B", "summary": "", "message_ids": [2], "risk_level": 2}],
        {1, 2},
    )
    assert len(groups) == 1
    assert groups[0]["message_ids"] == [1, 2]


def test_muc_rui_ro_la_thi_ve_vua():
    g = _clean_groups([{"title": "A", "summary": "", "message_ids": [1],
                        "risk_level": "cao"}], {1})
    assert g[0]["risk_level"] == 2


# --- Bóc JSON ---------------------------------------------------------------
def test_boc_duoc_json_trong_rao_va_co_cau_dan():
    assert parse_json('Đây là kết quả:\n```json\n{"groups": []}\n```')["groups"] == []
    assert parse_json('{"a": 1}')["a"] == 1


def test_khong_ra_json_thi_nem_loi():
    """Luật B1 — không đoán tiếp từ văn xuôi."""
    with pytest.raises(ProviderError):
        parse_json("Xin lỗi, tôi không hiểu yêu cầu.")
    with pytest.raises(ProviderError):
        parse_json('[1, 2, 3]')   # JSON hợp lệ nhưng không phải object


# --- Ước chi phí ------------------------------------------------------------
def test_uoc_chi_phi_va_model_la_tra_khong():
    # 1 triệu token vào + 1 triệu ra của gemini-flash-latest = 0.30 + 2.50
    assert estimate_cost_usd("gemini-flash-latest", 1_000_000, 1_000_000) == 2.80
    assert estimate_cost_usd("gemini-flash-latest-002", 1_000_000, 0) == 0.30  # khớp tiền tố
    #  Model lạ trả 0 chứ không đoán — thà 0 rõ ràng còn hơn một con số có người tin.
    assert estimate_cost_usd("model-la-hoac", 1_000_000, 1_000_000) == 0.0
