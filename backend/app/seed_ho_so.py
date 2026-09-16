"""NẠP DANH MỤC LOẠI HỒ SƠ (phân hệ Hồ sơ, 16/09/2026) — CHẠY LẠI ĐƯỢC.

    docker compose exec api python -m app.seed_ho_so

⚠️ **Chỉ THÊM, không xóa, không ghi đè.** Chạy trên môi trường thật thì mọi thứ
người ta đã sửa tay ở màn danh mục phải còn nguyên — đối chiếu theo `code`, mã
nào đã có thì bỏ qua nguyên dòng. Chạy mười lần cũng ra một bộ.

⚠️ **Không nằm trong `app/seed.py`** nên `start.sh` không tự chạy. Có chủ ý,
cùng nếp với `seed_nghi_phep`: nạp danh mục vào một môi trường chưa dùng phân hệ
này là bày ra danh mục rác. Chạy tay khi bật phân hệ.

⚠️ **Khách chốt ĐÚNG 5 loại** (16/09/2026), và đây là **năm GIAI ĐOẠN của một lô
nhập hàng** chứ không phải năm nhóm giấy tờ:

    1. Pháp lý & Giấy phép   → trước khi đặt hàng
    2. Đặt hàng & Hợp đồng   → làm việc với NCC
    3. Sản xuất & Vận chuyển → NCC sản xuất, giao hàng
    4. Kiểm tra & Thông quan → kiểm tra chất lượng, thủ tục
    5. Nhận hàng & Về kho    → nhận hàng, đối chiếu, nhập kho

Hệ quả phải nhớ:

* **`sort_order` ở đây mang nghĩa THẬT** — nó là thứ tự công việc, không phải số
  trang trí, nên danh mục phải bày đúng 1→5 (`defaultSort` ở
  `frontend-v2/.../config/dossier-type-crud.tsx`). Chèn giai đoạn mới thì đánh số
  xen kẽ (15, 25…), đừng đánh lại cả dãy.
* **Hạn hiệu lực mặc định để `0`** (vô thời hạn) cho cả năm: một giai đoạn không
  hết hạn. Ô đó chỉ có nghĩa trở lại nếu khách quay về mô hình "loại giấy tờ".

Đổi bộ khác thì sửa thẳng trên giao diện, đừng sửa tệp này rồi chạy lại — nó
không ghi đè nên chẳng có tác dụng gì.
"""
import app.core.all_models  # noqa: F401  — nạp đủ model để mapper cấu hình được
from app.core.database import SessionLocal
from app.modules.dossier.type_model import DossierType

#  (mã, tên, mô tả, hạn hiệu lực mặc định tính bằng THÁNG, thứ tự bày)
#  `0` tháng = vô thời hạn — một lựa chọn thật, không phải ô bỏ trống.
DOSSIER_TYPES = [
    ("PLGP", "Pháp lý & Giấy phép", "Trước khi đặt hàng.", 0, 10),
    ("DHHD", "Đặt hàng & Hợp đồng", "Làm việc với NCC.", 0, 20),
    ("SXVC", "Sản xuất & Vận chuyển", "NCC sản xuất, giao hàng.", 0, 30),
    ("KTTQ", "Kiểm tra & Thông quan", "Kiểm tra chất lượng, thủ tục.", 0, 40),
    ("NHVK", "Nhận hàng & Về kho", "Nhận hàng, đối chiếu, nhập kho.", 0, 50),
]


def seed_dossier_types(db) -> int:
    """Thêm loại còn thiếu. Trả về số dòng đã thêm."""
    #  So theo `code` vì đó là cột duy nhất của bảng; tên thì người dùng sửa
    #  được, lấy tên làm mốc là chạy lần hai đẻ ra bản trùng.
    existing_codes = {code for (code,) in db.query(DossierType.code).all()}
    added = 0
    for code, name, description, months, sort_order in DOSSIER_TYPES:
        if code in existing_codes:
            continue
        db.add(DossierType(
            code=code, name=name, description=description,
            default_valid_months=months, sort_order=sort_order, is_active=True,
        ))
        added += 1
    return added


def run() -> int:
    db = SessionLocal()
    try:
        added = seed_dossier_types(db)
        db.commit()
        print(f"Loại hồ sơ: thêm {added} (tổng {db.query(DossierType).count()})")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(run())
