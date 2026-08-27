"""Thumbnail sinh lúc upload (core/images.py) — nền của việc feed diễn đàn/avatar
đọc bản nhẹ thay vì kéo nguyên tệp gốc (chốt 27/08/2026, cùng đợt D-Q3)."""
from io import BytesIO

from app.core.images import THUMBABLE_EXTS, make_thumb


def _png(size, color=(200, 30, 30), mode="RGB"):
    from PIL import Image
    buf = BytesIO()
    Image.new(mode, size, color).save(buf, format="PNG")
    buf.seek(0)
    return buf


def _jpeg_nhieu_chi_tiet(size):
    """JPEG nhiễu ngẫu nhiên — ảnh trơn một màu nén quá tốt, không đo được chuyện
    thu nhỏ có làm nhẹ tệp hay không."""
    import random

    from PIL import Image
    random.seed(7)
    img = Image.new("RGB", size)
    img.putdata([(random.randrange(256),) * 3 for _ in range(size[0] * size[1])])
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    return buf


def test_anh_to_duoc_thu_ve_1280_va_nhe_hon():
    from PIL import Image
    goc = _jpeg_nhieu_chi_tiet((2400, 1600))
    goc_size = len(goc.getvalue())
    thumb = make_thumb(goc)
    assert thumb is not None
    ra = Image.open(thumb)
    assert max(ra.size) == 1280
    thumb.seek(0, 2)
    assert thumb.tell() < goc_size
    # Con trỏ luồng gốc phải về 0 — ngay sau make_thumb bên gọi còn upload chính nó.
    assert goc.tell() == 0


def test_png_trong_suot_ra_jpeg_nen_trang_khong_hoa_den():
    from PIL import Image
    goc = _png((2000, 2000), color=(0, 0, 0, 0), mode="RGBA")
    thumb = make_thumb(goc)
    assert thumb is not None
    ra = Image.open(thumb)
    assert ra.mode == "RGB"
    # Vùng trong suốt phải thành TRẮNG — convert("RGB") thẳng là hóa đen (lỗi kinh điển).
    assert ra.getpixel((10, 10)) == (255, 255, 255)


def test_tep_khong_phai_anh_tra_none_khong_no():
    rac = BytesIO(b"day khong phai la anh" * 100)
    assert make_thumb(rac) is None
    assert rac.tell() == 0


def test_gif_khong_nam_trong_danh_sach_sinh_thumb():
    # GIF ép về JPEG là mất chuyển động — cố ý đứng ngoài, hiển thị dùng bản gốc.
    assert "gif" not in THUMBABLE_EXTS
    assert {"jpg", "jpeg", "png", "webp"} <= THUMBABLE_EXTS


def test_avatar_uu_tien_thumb_fallback_ban_goc():
    """`User.avatar` đọc thumb trước, tệp cũ chưa có thumb thì về `url` như trước."""
    from app.modules.attachment.model import StoredFile
    from app.modules.user.model import User

    u = User()
    f = StoredFile(filename="a.jpg", file_key="k", url="u-goc", thumb_url="u-thumb")
    # property đọc self.avatar_file (relationship viewonly) — nhét thẳng vào __dict__
    # để test thuần không cần DB.
    u.__dict__["avatar_file"] = f
    assert u.avatar == "u-thumb"
    f.thumb_url = ""
    assert u.avatar == "u-goc"
