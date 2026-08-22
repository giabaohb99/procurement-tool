"""XUẤT EXCEL danh sách văn bản.

Dựng trên bộ khung dùng chung `core/export_xlsx.py` (cùng đường với YCBG, ĐMH,
Tiến độ mua hàng) nên định dạng ô, giới hạn số dòng và tên tệp giống hệt các
màn khác — người dùng mở file ra không phải học lại cách đọc.

Nguồn dữ liệu là `serializer.serialize_many`, tức **đúng thứ đang hiện trên
bảng**: tên loại, tên pháp nhân, tên phòng, tên người đã ghép sẵn. Không tự tra
lại từ id ở đây, vì hai đường tra khác nhau là hai kết quả khác nhau lúc dữ liệu
danh mục đổi.

⚠️ Quyền: endpoint gọi hàm này đã lọc qua `visible_condition` y như danh sách.
Đừng nhận `db.query(Document)` trần vào đây — file Excel là đường rò dữ liệu
kín tiếng nhất, không ai nhìn thấy nó rời khỏi hệ thống.
"""
from app.core.export_xlsx import Col

FILE_NAME = "danh-sach-van-ban"
SHEET_TITLE = "Văn bản"

#  Nhãn mức mật / độ khẩn KHÔNG còn khai ở đây — chúng là danh mục sửa được, đọc
#  từ DB qua `doc_catalog.security_level_service`. Giữ bản chép ở đây thì đổi tên
#  mức trên màn hình xong file Excel vẫn in chữ cũ.
ORIGIN_LABELS = {1: "Nội bộ ban hành", 2: "Văn bản pháp luật ngoài", 3: "Văn bản đến"}

#  `key` trùng key cột trên bảng danh sách để `pick_columns` giữ được đúng thứ
#  tự và đúng những cột người dùng đang hiện.
COLUMNS = [
    Col("display_code", "Số hiệu", width=22),
    Col("book_number_display", "Số vào sổ", width=14),
    Col("title", "Tên văn bản", width=46),
    Col("doc_type_name", "Loại", width=20),
    Col("company_name", "Pháp nhân ban hành", width=30),
    Col("department_name", "Phòng chủ trì", width=24),
    Col("owner_name", "Người chịu trách nhiệm", width=22),
    Col("signer_name", "Người ký", width=22),
    Col("version_no", "Phiên bản", width=10),
    Col("status_label", "Trạng thái", width=16),
    Col("effective_date", "Ngày hiệu lực", "date", 14),
    Col("expire_date", "Ngày hết hiệu lực", "date", 16),
    Col("secrecy_label", "Mức mật", width=12),
    Col("urgency_label", "Độ khẩn", width=12),
    Col("book_name", "Sổ văn bản", width=24),
    Col("legacy_code", "Số hiệu cũ", width=16),
    #  Bản in danh sách mang theo chỗ để bản giấy: cầm file Excel đi lấy hồ sơ
    #  trong kho là ca dùng chính của cột này.
    Col("storage_location", "Nơi lưu trữ cứng", width=26),
    Col("keywords", "Từ khóa", width=28),
    Col("summary", "Trích yếu", width=40),
    Col("needs_review_text", "Cần rà soát", width=14),
    Col("attachment_count", "Số tệp đính kèm", "int", 14),
    Col("created_at", "Ngày tạo", "datetime", 18),
]


def build_rows(db, rows: list[dict]) -> list[dict]:
    """Bồi thêm mấy ô mà bảng danh sách vẽ bằng badge chứ không phải chữ.

    Trên màn hình, mức mật / độ khẩn / cờ rà soát hiện bằng badge màu; đổ thẳng
    số 2, 3 vào Excel thì người nhận file không đọc ra gì.
    """
    from app.modules.doc_catalog.security_level_service import label, label_maps

    #  Tra MỘT LẦN cho cả danh sách, không mỗi dòng một truy vấn.
    nhan_mat, nhan_khan = label_maps(db)

    for row in rows:
        row["secrecy_label"] = label(nhan_mat, row.get("secrecy_level"))
        row["urgency_label"] = label(nhan_khan, row.get("urgency"))
        row["needs_review_text"] = "Cần rà soát" if row.get("needs_review") else ""
        #  Bản riêng của pháp nhân con: nói rõ ra, nếu không thì trong file
        #  Excel nó nằm lẫn giữa các bản gốc mà không có gì phân biệt.
        if row.get("source_document_id"):
            row["title"] = f"[Bản riêng] {row.get('title', '')}"
    return rows
