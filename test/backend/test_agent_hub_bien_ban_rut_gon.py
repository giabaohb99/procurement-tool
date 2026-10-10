"""ai-CR-165 — đại ca 10/10: tin biên bản trong chat quá dài, đọc không hết. Chat chỉ gửi bản RÚT GỌN cỡ một màn điện thoại
(tóm tắt nhanh · đã chốt · việc · còn mở + dòng chỉ chỗ bản đầy đủ); chi tiết theo chủ đề chỉ nằm trong Word."""
import io
import zipfile

from app.modules.agent_hub import meetings as mt

TOPIC = "Đơn hàng thép Hòa Phát: bối cảnh giá tăng, so sánh ba nhà cung cấp, chi tiết từng lô hàng và điều kiện giao. "
RECAP = "\n".join([
    "## TÓM TẮT NHANH",
    *[f"- Ý chính số {i}: giá thép tăng **{i}%** so với tháng trước, cần chốt sớm" for i in range(1, 10)],
    "## NỘI DUNG CUỘC HỌP",
    *[f"### {i}. Chủ đề {i}\n{TOPIC * 3}\nÝ CHÍNH:\n- chi tiết {i}\nĐÃ CHỐT:\n✓ Chốt mua lô {i} giá **4{i} triệu**"
      for i in range(1, 9)],
    "## CÔNG VIỆC CẦN LÀM",
    "| Việc | Người | Hạn | Ưu tiên |",
    "|---|---|---|---|",
    *[f"| Gửi báo giá lô {i} | Mai | {10 + i}/10 | Cao |" for i in range(1, 11)],
    "## VẤN ĐỀ CÒN MỞ",
    *[f"- Câu hỏi mở {i} về điều kiện thanh toán" for i in range(1, 6)],
    "## NGƯỜI THAM DỰ",
    "- Hùng – chủ trì",
])


def test_tin_chat_rut_gon_du_bon_muc_va_vua_mot_man():
    row = type("R", (), {"title": "Giao ban giá thép", "recap": RECAP, "template": "dego"})()
    msg = mt.recap_message(row, "Recap DEGO", 102)
    assert len(msg) <= mt.RECAP_CHAT_MAX
    for head in ("**TÓM TẮT NHANH**", "**ĐÃ CHỐT**", "**VIỆC CẦN LÀM**"):
        assert head in msg, head
    assert "Gửi báo giá lô 1 · Mai · 11/10" in msg and "Chốt mua lô 1" in msg
    assert msg.rstrip().endswith(mt.FULL_LINE) and "cắt bớt" not in msg
    assert TOPIC.strip()[:40] not in msg                      # chi tiết theo chủ đề không vào chat
    assert msg.count("Ý chính số") <= mt.CHAT_LIMITS["tldr"]


def test_bien_ban_ngan_van_co_muc_con_mo_va_mau_rieng_lay_gach_dau_dong():
    short = "## TÓM TẮT NHANH\n- A\n## VẤN ĐỀ CÒN MỞ\n- B\n- C\n- D\n- E"
    msg = mt.chat_summary(short)
    assert "**CÒN MỞ**" in msg and msg.count("\n- ") + 1 >= 3 and "- E" not in msg      # còn mở tối đa 3 ý
    assert "- việc riêng" in mt.chat_summary("Ghi chú cuộc gọi\n- việc riêng\n- việc hai")


def test_word_van_du_chi_tiet_theo_chu_de():
    data = mt.build_docx("Giao ban giá thép", None, RECAP, "", label="Recap DEGO", minutes=102)
    xml = zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml").decode("utf-8")
    assert "Chủ đề 8" in xml and "so sánh ba nhà cung cấp" in xml and "Câu hỏi mở 5" in xml


def test_loi_dan_viet_bot_trich_nguyen_van():
    assert "KHÔNG chép lại câu nói" in mt.RECAP_SYSTEM and "không chép" in mt.CHUNK_SYSTEM
