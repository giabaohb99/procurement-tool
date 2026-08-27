"""Sinh bản thumbnail cho ảnh lúc TẢI LÊN (Pillow).

Hệ chưa có CDN resize, nên trước đây mọi chỗ hiển thị (feed diễn đàn, avatar,
ảnh sản phẩm) đều kéo nguyên tệp gốc rồi để trình duyệt ép size — tốn băng thông
theo dung lượng tệp chứ không theo khung hiển thị. Giải pháp: sinh MỘT bản nhẹ
ngay lúc upload, lưu cạnh tệp gốc trên storage (`{file_key}.thumb.jpg`), chỗ nào
chỉ hiển thị thì đọc bản nhẹ, bấm xem lớn (đèn chiếu / tải về) mới đụng bản gốc.
"""
from io import BytesIO

# Đuôi ảnh sinh được thumbnail. GIF cố ý ĐỨNG NGOÀI: ép về JPEG là mất chuyển động.
THUMBABLE_EXTS = {"jpg", "jpeg", "png", "webp", "bmp"}


def make_thumb(fileobj, *, max_edge: int = 1280, quality: int = 82) -> BytesIO | None:
    """Thu ảnh về cạnh dài `max_edge`, nén JPEG. Trả None khi không đáng làm
    (ảnh hỏng, hoặc bản nén ra còn NẶNG hơn bản gốc — ảnh nhỏ sẵn thì thôi).

    Luôn trả con trỏ `fileobj` về 0 khi xong — bên gọi còn upload chính luồng này.
    """
    try:
        from PIL import Image, ImageOps

        fileobj.seek(0, 2)
        orig_size = fileobj.tell()
        fileobj.seek(0)
        img = Image.open(fileobj)
        # Ảnh điện thoại hay lưu xoay bằng EXIF — không áp thì thumb nằm ngang.
        img = ImageOps.exif_transpose(img)
        img.thumbnail((max_edge, max_edge))
        # JPEG không có kênh alpha: ảnh PNG trong suốt phải đè lên nền trắng,
        # convert thẳng RGB là vùng trong suốt hóa đen.
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        out = BytesIO()
        img.save(out, format="JPEG", quality=quality, optimize=True)
        if out.tell() >= orig_size:
            return None
        out.seek(0)
        return out
    except Exception:
        return None
    finally:
        try:
            fileobj.seek(0)
        except Exception:
            pass
