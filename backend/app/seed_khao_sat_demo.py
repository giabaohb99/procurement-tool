"""Seed DEMO cho phân hệ Khảo sát — CHỈ DÙNG LOCAL.

    docker compose exec -T api python -m app.seed_khao_sat_demo

Vì sao có tệp này: `app/seed.py` nạp model khảo sát để dựng bảng và cấp quyền,
nhưng KHÔNG tạo bản ghi nào — nên màn *Phiếu khảo sát* và *Báo cáo khảo sát*
trên máy lập trình luôn trống, không kiểm chứng được giao diện. Đặt NGOÀI
`seed.py` theo đúng lệ của các `seed_*_demo.py` khác: dữ liệu mẫu không nên tự
chạy mỗi lần khởi động.

Idempotent: xóa sạch phiếu demo cũ (nhận diện qua tiền tố mã `KSDEMO`) cùng mọi
dòng con của chúng, rồi tạo lại — chạy bao nhiêu lần cũng ra cùng kết quả và
KHÔNG đụng dữ liệu thật.

Kịch bản cố ý phủ những ca hay làm lủng giao diện:
  · đủ BỐN kết quả duyệt dòng (Chờ duyệt · Đã duyệt · Không duyệt · Thiếu thông tin)
    → bốn ô đếm ở đầu Báo cáo khảo sát đều khác 0
  · tên NCC và tên SP DÀI              → thử tràn chữ / xuống dòng ở bảng lẫn thẻ
  · một phiếu có cả dòng NCC lẫn dòng SP → thử trang trộn hai loại dòng
  · dòng SP thiếu giá, dòng NCC thiếu MST → thử ô rỗng, đừng để ra "0" hay "—" sai chỗ
  · ngày trải nhiều tháng               → thử bộ lọc khoảng ngày
"""
import app.core.all_models  # noqa: F401 — nạp mapper trước khi query

from app.core.database import SessionLocal
from app.modules.survey.model import Survey, SurveyProductLine, SurveySupplierLine

DEMO_PREFIX = "KSDEMO"

#  Bốn kết quả duyệt DÒNG là chuỗi tiếng Việt, không phải mã — xem ghi chú
#  "hai leftover giữ tiếng Việt" ở CLAUDE.md (`line_approve` trên hai bảng dòng
#  khảo sát nằm ngoài phạm vi đợt chuyển mã B-01…B-06).
CHO_DUYET = "Chờ duyệt"
DA_DUYET = "Đã duyệt"
KHONG_DUYET = "Không duyệt"
THIEU_TT = "Thiếu thông tin"

# (mã, loại phiếu, mã YCBG, mã PYC, ngày tiếp nhận, hạn trả KQ, phân loại,
#  nội dung chính, mã VTBB, tên VTBB, ĐVT, SL dự kiến, trạng thái phiếu)
DEMO_SURVEYS = [
    (
        "KSDEMO01", "combined", "YCBG-DEMO-01", "PYC-DEMO-01",
        "2026-03-04", "2026-03-18", "Bao bì",
        "Khảo sát nhà cung cấp thùng carton 5 lớp cho dây chuyền chiết rót số 2",
        "THI0002", "Thùng IDA Chai Pet Vuông 35 450ml-500ml - Xanh lá", "Cái", 12000,
        "approved",
    ),
    (
        "KSDEMO02", "combined", "YCBG-DEMO-02", "PYC-DEMO-02",
        "2026-05-19", "2026-06-02", "Nguyên liệu",
        "Khảo sát giá hạt nhựa PET nguyên sinh quý III",
        "NL0001", "Hạt nhựa PET nguyên sinh - Chỉ số IV 0.80", "Kg", 30000,
        "submitted",
    ),
    (
        "KSDEMO03", "combined", "YCBG-DEMO-03", "",
        "2026-08-11", "2026-08-25", "Vật tư tiêu hao",
        "Khảo sát băng keo dán thùng và màng PE quấn pallet",
        "", "", "Cuộn", 800,
        "draft",
    ),
]

# (mã phiếu, mã NCC, tên NCC, MST, người liên hệ, điện thoại, ngày liên hệ,
#  nhóm cung cấp, nguồn thông tin, thời gian sản xuất, chính sách hóa đơn,
#  công nợ, kết quả duyệt dòng, ghi chú duyệt)
DEMO_SUPPLIER_LINES = [
    (
        "KSDEMO01", "Cẩm Hùng", "CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI BAO BÌ CẨM HÙNG",
        "0301234567", "Anh Tuấn", "0901234567", "2026-03-05",
        "Bao bì carton", "Giới thiệu từ NCC cũ", "7 ngày", "Hóa đơn VAT đầy đủ",
        "30 ngày", DA_DUYET, "Giá tốt, đã từng hợp tác",
    ),
    (
        "KSDEMO01", "Đông Tây", "CÔNG TY TNHH SẢN XUẤT BAO BÌ ĐÔNG TÂY",
        "0312345678", "Chị Hà", "0912345678", "2026-03-06",
        "Bao bì carton", "Tìm trên mạng", "10 ngày", "Hóa đơn VAT đầy đủ",
        "15 ngày", CHO_DUYET, "",
    ),
    (
        #  MST rỗng — đúng ca "thiếu thông tin", và là ô trống để thử xem giao
        #  diện có bịa ra dấu gạch hay số 0 ở chỗ đáng lẽ bỏ trắng không.
        "KSDEMO01", "Tân Đức", "CÔNG TY CỔ PHẦN BAO BÌ VÀ IN ẤN TÂN ĐỨC PHÁT",
        "", "Anh Minh", "", "2026-03-09",
        "Bao bì carton", "Hội chợ triển lãm", "", "",
        "", THIEU_TT, "Chưa gửi được mã số thuế và bảng giá",
    ),
    (
        "KSDEMO02", "Nhựa Việt", "CÔNG TY TNHH THƯƠNG MẠI VÀ SẢN XUẤT NHỰA VIỆT PHÚ",
        "0323456789", "Chị Lan", "0923456789", "2026-05-20",
        "Nguyên liệu nhựa", "NCC chủ động chào hàng", "14 ngày", "Hóa đơn VAT đầy đủ",
        "45 ngày", DA_DUYET, "",
    ),
    (
        "KSDEMO02", "Hóa chất Bình Minh", "CÔNG TY TNHH HÓA CHẤT VÀ NGUYÊN LIỆU BÌNH MINH",
        "0334567890", "Anh Sơn", "0934567890", "2026-05-22",
        "Nguyên liệu nhựa", "Giới thiệu nội bộ", "21 ngày", "Không xuất hóa đơn VAT",
        "Tiền mặt", KHONG_DUYET, "Không xuất được hóa đơn VAT nên loại",
    ),
    (
        "KSDEMO03", "Việt Thắng", "CÔNG TY TNHH VẬT TƯ CÔNG NGHIỆP VIỆT THẮNG",
        "0345678901", "Chị Thu", "0945678901", "2026-08-12",
        "Vật tư tiêu hao", "Tìm trên mạng", "5 ngày", "Hóa đơn VAT đầy đủ",
        "30 ngày", CHO_DUYET, "",
    ),
]

# (mã phiếu, mã NCC, mã SP theo NCC, tên SP, quy cách, xuất xứ, ĐVT báo giá,
#  MOQ, đơn giá theo sản lượng, khoảng sản lượng, VAT, SL, ngày liên hệ,
#  thời gian giao, có mẫu, kết quả duyệt dòng)
DEMO_PRODUCT_LINES = [
    (
        "KSDEMO01", "Cẩm Hùng", "CH-TH-5L-403020",
        "Thùng carton 5 lớp sóng BC, in flexo 2 màu, kích thước 40x30x20cm",
        "Sóng BC, định lượng 560gsm, in 2 màu", "Việt Nam", "Cái",
        500, 12500, "500 - 5.000 cái", 8, 12000, "2026-03-05",
        "7 ngày kể từ ngày chốt đơn", True, DA_DUYET,
    ),
    (
        "KSDEMO01", "Đông Tây", "DT-C5-403020",
        "Thùng carton 5 lớp sóng BC in 1 màu 40x30x20cm",
        "Sóng BC, định lượng 520gsm", "Việt Nam", "Cái",
        1000, 11800, "1.000 - 10.000 cái", 8, 12000, "2026-03-06",
        "10 ngày", False, CHO_DUYET,
    ),
    (
        #  Chưa có giá — NCC mới gửi quy cách, chưa gửi báo giá. Cột tiền phải
        #  bỏ TRẮNG, không được hiện "0 đ" (đọc ra như hàng cho không).
        "KSDEMO01", "Tân Đức", "",
        "Thùng carton 5 lớp - chờ NCC gửi quy cách chi tiết",
        "", "", "Cái",
        0, 0, "", 0, 12000, "2026-03-09",
        "", False, THIEU_TT,
    ),
    (
        "KSDEMO02", "Nhựa Việt", "NV-PET-IV080",
        "Hạt nhựa PET nguyên sinh chỉ số IV 0.80, dùng cho chai nước đóng chai",
        "Bao 25kg, độ ẩm < 0.2%", "Hàn Quốc", "Kg",
        5000, 28500, "5.000 - 50.000 kg", 10, 30000, "2026-05-20",
        "14 ngày", True, DA_DUYET,
    ),
    (
        "KSDEMO02", "Hóa chất Bình Minh", "BM-PET-R",
        "Hạt nhựa PET tái sinh",
        "Bao 25kg", "Trung Quốc", "Kg",
        10000, 19200, "10.000 kg trở lên", 0, 30000, "2026-05-22",
        "21 ngày", False, KHONG_DUYET,
    ),
    (
        "KSDEMO03", "Việt Thắng", "VT-BK-4818",
        "Băng keo trong dán thùng 48mm x 100 yard",
        "Lõi 48mm, dày 45 micron", "Việt Nam", "Cuộn",
        100, 9800, "100 - 1.000 cuộn", 8, 800, "2026-08-12",
        "5 ngày", True, CHO_DUYET,
    ),
    (
        "KSDEMO03", "Việt Thắng", "VT-PE-500",
        "Màng PE quấn pallet khổ 500mm, cuộn 3kg",
        "Dày 17 micron, lõi giấy", "Việt Nam", "Cuộn",
        50, 54000, "50 - 500 cuộn", 8, 800, "2026-08-12",
        "5 ngày", False, THIEU_TT,
    ),
]


def _wipe_demo(db):
    """Xóa phiếu demo cũ + mọi dòng con. Trả về số phiếu đã xóa."""
    olds = db.query(Survey).filter(Survey.code.like(f"{DEMO_PREFIX}%")).all()
    if not olds:
        return 0
    ids = [s.id for s in olds]
    #  Xóa DÒNG trước rồi mới tới phiếu: hai bảng dòng nối bằng `survey_id` trần
    #  chứ không có khóa ngoại, nên xóa phiếu trước là để lại dòng mồ côi —
    #  chúng không hiện ở đâu cả nhưng vẫn bị `report_rows` đếm vào ô tổng.
    db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id.in_(ids)).delete(
        synchronize_session=False
    )
    db.query(SurveyProductLine).filter(SurveyProductLine.survey_id.in_(ids)).delete(
        synchronize_session=False
    )
    db.query(Survey).filter(Survey.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return len(olds)


def run():
    db = SessionLocal()
    try:
        wiped = _wipe_demo(db)
        if wiped:
            print(f"Đã dọn {wiped} phiếu khảo sát demo cũ.")

        by_code = {}
        for (code, stype, sr_code, pr_code, received, due, group, main,
             item_code, item_name, uom, qty, status) in DEMO_SURVEYS:
            s = Survey(
                code=code, survey_type=stype, sr_code=sr_code, pr_code=pr_code,
                received_date=received, result_due_date=due, item_group=group,
                main_content=main, item_code=item_code, item_name=item_name,
                has_product_code=bool(item_code), uom=uom, request_qty=qty,
                nspt="Dego Admin", status=status,
                approve_status="approved" if status == "approved" else "pending",
            )
            db.add(s)
            by_code[code] = s
        db.commit()

        for (survey_code, sup_code, sup_name, tax, person, phone, contact_date,
             group, source, prod_time, invoice, debt, approve, note) in DEMO_SUPPLIER_LINES:
            db.add(SurveySupplierLine(
                survey_id=by_code[survey_code].id,
                supplier_code=sup_code, supplier_name=sup_name, tax_code=tax,
                contact_person=person, contact_phone=phone, contact_date=contact_date,
                supply_group=group, source_of_information=source,
                production_time=prod_time, invoice_policy=invoice, debt_policy=debt,
                line_approve=approve, line_approve_note=note,
            ))

        for (survey_code, sup_code, internal, name, spec, origin, unit, moq, price,
             vol_range, vat, qty, contact_date, delivery, sample, approve) in DEMO_PRODUCT_LINES:
            db.add(SurveyProductLine(
                survey_id=by_code[survey_code].id,
                supplier_code=sup_code, internal_code=internal, product_name=name,
                spec=spec, origin=origin, quote_unit=unit, moq=moq,
                price_by_volume=price, volume_range=vol_range, vat=vat,
                request_qty=qty, amount=price * qty, contact_date=contact_date,
                delivery_time=delivery, sample_ready=sample, line_approve=approve,
            ))
        db.commit()

        print(
            f"Đã tạo {len(DEMO_SURVEYS)} phiếu · "
            f"{len(DEMO_SUPPLIER_LINES)} dòng NCC · {len(DEMO_PRODUCT_LINES)} dòng SP."
        )
        print("\nKiểm chứng nhanh — bốn ô đếm ở Báo cáo khảo sát:")
        for label in (CHO_DUYET, DA_DUYET, KHONG_DUYET, THIEU_TT):
            n = (
                db.query(SurveySupplierLine)
                .filter(SurveySupplierLine.line_approve == label).count()
                + db.query(SurveyProductLine)
                .filter(SurveyProductLine.line_approve == label).count()
            )
            print(f"  {label}: {n} dòng")
    finally:
        db.close()


if __name__ == "__main__":
    run()
