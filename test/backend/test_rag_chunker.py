"""Cắt đoạn cho tìm kiếm vector loại B (Phase 3) — hàm thuần, chỗ dễ sai âm thầm nhất.

CHỈ kiểm `rag/chunker.py`: bỏ HTML + cắt câu + gói đoạn + chồng lấn + cắt cứng câu khổng lồ.
Không đụng Qdrant / Gemini (mạng) — những phần đó verify tay bằng live test.
"""
from app.modules.assistant.rag.chunker import chunk_text, strip_html


def test_strip_html_giu_ranh_gioi_khoi():
    """Thẻ khối phải thành xuống dòng, không thì hai câu hai đoạn dính làm một."""
    html = "<p>Câu một.</p><p>Câu hai.</p>"
    out = strip_html(html)
    assert "Câu một." in out and "Câu hai." in out
    # Có ranh giới giữa hai câu (xuống dòng hoặc khoảng trắng), không dính 'một.Câu'
    assert "một.Câu" not in out


def test_strip_html_bo_the_va_giai_ma_thuc_the():
    out = strip_html("<b>Đậm</b> &amp; <i>nghiêng</i>&nbsp;xong")
    assert "<" not in out and ">" not in out
    assert "&" in out and "&amp;" not in out


def test_rong_tra_ve_list_rong():
    assert chunk_text("") == []
    assert chunk_text("   ") == []
    assert chunk_text("<p>  </p>") == []


def test_ngan_hon_nguong_thi_mot_doan_nguyen():
    out = chunk_text("Một câu ngắn gọn.")
    assert out == ["Một câu ngắn gọn."]


def test_dai_thi_cat_nhieu_doan_moi_doan_trong_nguong():
    # 60 câu, mỗi câu ~20 ký tự -> chắc chắn vượt 900 và phải cắt.
    text = " ".join(f"Đây là câu số {i}." for i in range(60))
    chunks = chunk_text(text, max_chars=200)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)
    assert all(c.strip() for c in chunks)   # không đoạn nào rỗng


def test_cau_khong_lo_bi_cat_cung():
    """Một câu dài hơn ngưỡng (không có dấu ngắt) vẫn phải bị xẻ nhỏ, không lọt nguyên cục."""
    monster = "a" * 500
    chunks = chunk_text(monster, max_chars=200)
    assert len(chunks) >= 3
    assert all(len(c) <= 200 for c in chunks)
    # Ghép lại đủ mặt ký tự, không mất chữ
    assert "".join(chunks) == monster


def test_chong_lan_mang_cau_cuoi_sang_doan_sau():
    """Câu vắt qua ranh giới vẫn tìm được: câu cuối đoạn trước mở đầu đoạn sau."""
    message = [f"Câu chủ đề {i} nói về một ý riêng biệt." for i in range(8)]
    text = " ".join(message)
    chunks = chunk_text(text, max_chars=120)
    assert len(chunks) >= 2
    # Câu cuối của đoạn đầu xuất hiện lại ở đầu đoạn kế (chồng lấn).
    first_last = chunks[0].split(". ")[-1].strip(". ")
    assert first_last and first_last in chunks[1]
