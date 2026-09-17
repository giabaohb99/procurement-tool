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

#  BỘ TRƯỜNG TÙY BIẾN gợi ý cho từng giai đoạn — phần «metadata» của loại hồ sơ
#  (16/09/2026). Đây là thứ làm biểu mẫu lập hồ sơ đổi theo loại đang chọn.
#
#  ⚠️ Chỉ là ĐIỂM XUẤT PHÁT, không phải quy định. Người dùng sửa thẳng trên màn
#  chi tiết loại hồ sơ; sửa xong thì seed không đụng vào nữa (xem
#  `_fill_field_schema`). Đừng quay lại sửa tệp này rồi chạy lại để "cập nhật" —
#  nó cố ý không ghi đè.
#
#  Cấu trúc và trần kích thước khai ở `modules/dossier/field_schema.py`.
FIELD_SCHEMAS = {
    "PLGP": [
        {"key": "so_giay_phep", "label": "Số giấy phép", "type": "text", "required": True},
        {"key": "co_quan_cap", "label": "Cơ quan cấp", "type": "text"},
        {"key": "pham_vi", "label": "Phạm vi áp dụng", "type": "textarea"},
    ],
    "DHHD": [
        {"key": "so_hop_dong", "label": "Số hợp đồng", "type": "text", "required": True},
        {"key": "nha_cung_cap", "label": "Nhà cung cấp", "type": "text"},
        {"key": "gia_tri", "label": "Giá trị hợp đồng (VNĐ)", "type": "number"},
        {"key": "dieu_khoan_tt", "label": "Điều khoản thanh toán", "type": "textarea"},
    ],
    "SXVC": [
        {"key": "so_van_don", "label": "Số vận đơn", "type": "text"},
        {"key": "hang_van_chuyen", "label": "Hãng vận chuyển", "type": "text"},
        {"key": "phuong_thuc", "label": "Phương thức", "type": "select",
         "options": ["Đường biển", "Đường hàng không", "Đường bộ", "Đường sắt"]},
        {"key": "ngay_du_kien_den", "label": "Ngày dự kiến đến", "type": "date"},
    ],
    "KTTQ": [
        {"key": "so_to_khai", "label": "Số tờ khai hải quan", "type": "text"},
        {"key": "cua_khau", "label": "Cửa khẩu", "type": "text"},
        {"key": "da_thong_quan", "label": "Đã thông quan", "type": "switch"},
        {"key": "ket_qua_kiem", "label": "Kết quả kiểm tra", "type": "textarea"},
    ],
    "NHVK": [
        {"key": "so_phieu_nhap", "label": "Số phiếu nhập kho", "type": "text"},
        {"key": "kho_nhan", "label": "Kho nhận", "type": "text"},
        {"key": "ngay_nhap_kho", "label": "Ngày nhập kho", "type": "date"},
        {"key": "chenh_lech", "label": "Chênh lệch so với đơn", "type": "textarea"},
    ],
}

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
            field_schema=FIELD_SCHEMAS.get(code, []),
        ))
        added += 1
    return added


def fill_field_schema(db) -> int:
    """Điền bộ trường gợi ý cho loại đã có mà cột còn TRỐNG. Trả về số dòng sửa.

    ⚠️ Chỉ đụng vào dòng đang `NULL` — tức là loại được seed TRƯỚC khi cột
    `field_schema` ra đời (migration `c8a1d4f60b37`). Ai đã khai bộ trường của
    riêng mình, kể cả khai rỗng bằng tay, thì không bị đụng tới.

    ⚠️ Hệ quả của nhánh `is None`: người dùng xóa sạch ô của một loại thì cột
    lưu `[]` chứ không lưu `NULL`, nên lần chạy sau seed cũng không "dựng lại"
    bộ trường mà họ vừa cố tình bỏ đi. Đó là điều mong muốn — đừng đổi thành
    `if not obj.field_defs`.
    """
    fixed = 0
    for obj in db.query(DossierType).filter(DossierType.field_schema.is_(None)).all():
        schema = FIELD_SCHEMAS.get(obj.code)
        if not schema:
            continue
        obj.field_schema = schema
        fixed += 1
    return fixed


def run() -> int:
    db = SessionLocal()
    try:
        added = seed_dossier_types(db)
        filled = fill_field_schema(db)
        db.commit()
        print(f"Loại hồ sơ: thêm {added}, điền bộ trường {filled} "
              f"(tổng {db.query(DossierType).count()})")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(run())
