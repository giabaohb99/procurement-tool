from collections import Counter
from typing import Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session


def assert_unique_product_codes(new_codes: Iterable[str],
                                old_codes: Iterable[str] = (),
                                message: str = "") -> None:
    """Mã hàng phải DUY NHẤT trên phiếu YCMH (ĐMH KHÔNG còn dùng luật này — bao-CR-308).

    VÌ SAO: dòng ĐMH nối ngược về dòng YCMH bằng CHUỖI `product_code`, không có khóa dòng
    (`purchase_request/service.sync_from_purchase_orders`). Hàm đó cộng dồn SL đặt/nhận theo
    mã rồi ghi CÙNG một con số vào MỌI dòng YCMH trùng mã → tiến độ nhân đôi, kéo theo trạng
    thái dòng và trạng thái phiếu sai. Chiều ngược lại thì an toàn: nhiều dòng ĐMH cùng mã
    được cộng gộp đúng (giống một YCMH rải ra nhiều ĐMH), nên từ bao-CR-308 ĐMH cho phép
    trùng mã để mua theo bộ chứng từ (cùng mã, khác lô / khác Tên trên hóa đơn).

    CHỈ CHẶN TRÙNG MỚI (số lần xuất hiện của một mã tăng so với dữ liệu đang lưu). Dữ liệu đã
    trùng sẵn vẫn lưu lại được — dòng bị khóa không xóa được, chặn cứng sẽ khóa chết phiếu cũ.
    """
    def _count(codes: Iterable[str]) -> Counter:
        return Counter(c for c in ((x or "").strip() for x in codes) if c)

    before, after = _count(old_codes), _count(new_codes)
    bad = sorted(c for c, n in after.items() if n > 1 and n > before.get(c, 0))
    if not bad:
        return
    tmpl = message or ("Mã hàng bị trùng: {codes}. Mỗi mã chỉ được xuất hiện trên 1 dòng — "
                       "hãy gộp số lượng vào một dòng hoặc đổi sang mã khác.")
    raise HTTPException(400, tmpl.format(codes=", ".join(bad)))


def generate_code(db: Session, model, prefix: str) -> str:
    """Generate a sequential code with a given prefix (e.g. CTY001)."""
    last_obj = db.query(model).filter(model.code.like(f"{prefix}%")).order_by(model.code.desc()).first()
    if not last_obj or not last_obj.code.startswith(prefix):
        return f"{prefix}001"
    
    try:
        num = int(last_obj.code[len(prefix):]) + 1
        return f"{prefix}{num:03d}"
    except ValueError:
        return f"{prefix}001"
