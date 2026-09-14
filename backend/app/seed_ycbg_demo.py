"""Seed DEMO cho phân hệ YÊU CẦU BÁO GIÁ (YCBG) — CHỈ DÙNG LOCAL.

    docker compose exec -T api python -m app.seed_ycbg_demo

Vì sao có tệp này: `app/seed.py` nạp model YCBG để dựng bảng và cấp quyền, nhưng
KHÔNG tạo bản ghi nào — nên `tab_survey_request` trên máy lập trình luôn rỗng, và
hai màn *Tiến độ báo giá* · *Chi tiết Yêu cầu báo giá* không kiểm chứng được giao
diện (màn tiến độ trả đúng `total: 0`). Đặt NGOÀI `seed.py` theo đúng lệ của
`seed_khao_sat_demo.py` / các `seed_*_demo.py` khác: dữ liệu mẫu không nên tự chạy
mỗi lần khởi động.

Idempotent: xóa sạch phiếu demo cũ (nhận diện qua tiền tố mã `YCBGDEMO`) cùng mọi
dòng và phương án con, rồi tạo lại — chạy bao nhiêu lần cũng ra cùng kết quả và
KHÔNG đụng dữ liệu thật.

Kịch bản cố ý phủ những ca hay làm lủng giao diện:
  · đủ CHÍN tiến độ dòng của `survey_request/line_state.py` → mọi màu huy hiệu
    đều xuất hiện, và bộ lọc *Tiến độ dòng* lọc ra được từng nhóm
  · dòng TRỄ HẠN (hạn đã qua, chưa trả KQ) và dòng trả MUỘN so với hạn
    → cột *Trễ (ngày)* và bộ lọc *Trễ hạn* đều khác rỗng
  · thông số kỹ thuật DÀI và tên NCC DÀI  → thử tràn chữ / xuống dòng ở bảng lẫn thẻ
  · dòng chưa có phương án nào            → thử ô rỗng, đừng để ra "0 đ" hay "—" sai chỗ
  · ngày trải nhiều tháng                 → thử bộ lọc khoảng ngày theo cả ba mốc

⚠️ Ngày trong tệp này cố định, KHÔNG tính theo "hôm nay". Tiến độ *Chưa tiếp nhận*
và cột *Trễ (ngày)* đều so với ngày hiện tại, nên mốc trôi theo ngày chạy seed thì
mỗi người thấy một tập khác nhau và không ai đối chiếu được với ai.
"""
import app.core.all_models  # noqa: F401 — nạp mapper trước khi query

from app.core.database import SessionLocal
from app.modules.survey_request.model import (
    LS_COMPLETED,
    LS_RESURVEY,
    SurveyRequest,
    SurveyRequestLine,
    SurveyRequestOption,
)

DEMO_PREFIX = "YCBGDEMO"

# (mã, công ty, người YC, bộ phận, mục đích, ngày YC, trạng thái phiếu)
DEMO_REQUESTS = [
    (
        "YCBGDEMO01", 1, "Nhân viên (Demo)", "Phòng Kinh doanh",
        "Khảo sát giá bao bì cho dây chuyền chiết rót số 2",
        "2026-03-02", "survey_done",
    ),
    (
        "YCBGDEMO02", 1, "Nhân viên (Demo)", "Phòng Sản xuất",
        "Khảo sát nguyên liệu nhựa quý III",
        "2026-05-18", "processing",
    ),
    (
        "YCBGDEMO03", 2, "Trưởng bộ phận (Demo)", "Phòng Hành chính",
        "Khảo sát vật tư tiêu hao kho vận",
        "2026-08-10", "approved",
    ),
]

#  (mã phiếu, mã dòng, ngày tiếp nhận, hạn trả KQ, ngày trả KQ, phân loại,
#   thông số kỹ thuật, yêu cầu khác, SL, ĐVT, giá đề xuất, NSTM, mã YCMH,
#   trạng thái dòng, chốt rỗng)
#
#  Cột cuối cùng của mỗi dòng là TIẾN ĐỘ mà `progress_state()` sẽ suy ra — ghi
#  vào comment chứ không vào DB, vì nó là giá trị dẫn xuất, không có cột nào lưu.
DEMO_LINES = [
    # --- YCBGDEMO01: phiếu đã khảo sát xong, phủ nhánh cuối dòng đời ---
    (   # Hoàn thành
        "YCBGDEMO01", "D01-01", "2026-03-04", "2026-03-18", "2026-03-16", "Bao bì",
        "Thùng carton 5 lớp, sóng BC, kích thước 400x300x250mm, in flexo 2 màu, "
        "chịu tải xếp chồng tối thiểu 180kg trong 24 giờ ở độ ẩm 75%",
        "Giao thử 200 thùng trước khi chốt hợp đồng năm",
        12000, "Cái", 9500, "DEMO_PURCHASER", "PYCDEMO01", LS_COMPLETED, False,
    ),
    (   # Đã tạo YCMH
        "YCBGDEMO01", "D01-02", "2026-03-04", "2026-03-18", "2026-03-20", "Bao bì",
        "Màng co PVC bọc nắp chai, khổ 32mm, độ co ngang 55%",
        "", 40000, "Cái", 320, "DEMO_PURCHASER", "PYCDEMO02", "", False,
    ),
    (   # Đã chọn phương án
        "YCBGDEMO01", "D01-03", "2026-03-05", "2026-03-18", "2026-03-17", "Bao bì",
        "Nhãn decal cuộn 90x60mm, chất liệu PP sữa, keo chịu ẩm",
        "Cần mẫu in thử trước", 25000, "Cái", 450, "DEMO_PURCHASER", "", "", False,
    ),
    (   # Cần khảo sát lại
        "YCBGDEMO01", "D01-04", "2026-03-05", "2026-03-18", "2026-03-19", "Bao bì",
        "Thùng carton 3 lớp cho hàng nội bộ, không in",
        "Giá chào cao hơn dự toán, cần tìm thêm NCC", 5000, "Cái", 6200,
        "DEMO_PURCHASER", "", LS_RESURVEY, False,
    ),

    # --- YCBGDEMO02: phiếu đang xử lý, phủ khúc giữa dòng đời ---
    (   # Chốt rỗng
        "YCBGDEMO02", "D02-01", "2026-05-19", "2026-06-02", "2026-06-01", "Nguyên liệu",
        "Hạt nhựa PET nguyên sinh chỉ số IV 0.80, dùng cho chai chịu áp",
        "Không NCC nào đáp ứng được sản lượng tháng", 30000, "Kg", 24500,
        "DEMO_PURCHASER", "", "", True,
    ),
    (   # Đã trả kết quả
        "YCBGDEMO02", "D02-02", "2026-05-19", "2026-06-02", "2026-06-05", "Nguyên liệu",
        "Hạt màu masterbatch xanh lá, tỷ lệ pha 2%, đạt chuẩn tiếp xúc thực phẩm",
        "", 1200, "Kg", 87000, "DEMO_PURCHASER", "", "", False,
    ),
    (   # Đang khảo sát — có phương án nhưng chưa chốt, và ĐÃ QUÁ HẠN
        "YCBGDEMO02", "D02-03", "2026-05-20", "2026-06-02", "", "Nguyên liệu",
        "Phụ gia chống UV cho chai PET trưng bày ngoài trời",
        "", 300, "Kg", 156000, "DEMO_PURCHASER", "", "", False,
    ),

    # --- YCBGDEMO03: phiếu mới duyệt, phủ khúc đầu dòng đời ---
    (   # Đã tiếp nhận — đã có NSTM, chưa có phương án nào
        "YCBGDEMO03", "D03-01", "2026-08-11", "2026-08-25", "", "Vật tư tiêu hao",
        "Băng keo trong dán thùng 48mm x 100 yard, lõi giấy 48mm",
        "", 800, "Cuộn", 9800, "DEMO_PURCHASER", "", "", False,
    ),
    (   # Chưa tiếp nhận — chưa gán NSTM
        "YCBGDEMO03", "D03-02", "", "2026-08-25", "", "Vật tư tiêu hao",
        "Màng PE quấn pallet khổ 500mm, dày 17 micron, cuộn 3kg",
        "Ưu tiên NCC giao trong ngày", 500, "Cuộn", 54000, "", "", "", False,
    ),
]

#  (mã dòng, số thứ tự PA, đã chốt, tên SP, ĐVT báo giá, MOQ, đơn giá, khoảng SL,
#   VAT, mã NCC, tên NCC, ghi chú NSTM)
DEMO_OPTIONS = [
    ("D01-01", 1, True, "Thùng carton 5 lớp BC 400x300x250 in flexo 2 màu",
     "Cái", 1000, 9200, "1.000 - 20.000 cái", 8, "NCC001",
     "CÔNG TY TNHH SẢN XUẤT VÀ THƯƠNG MẠI BAO BÌ CARTON TÂN HIỆP PHÁT MIỀN NAM",
     "Giá tốt nhất, đã mua nhiều lần"),
    ("D01-01", 2, False, "Thùng carton 5 lớp BC 400x300x250 in offset",
     "Cái", 2000, 10400, "2.000 - 20.000 cái", 8, "NCC002", "Bao bì Thành Đạt", ""),

    ("D01-02", 1, True, "Màng co PVC khổ 32mm", "Cái", 10000, 305,
     "10.000 - 100.000 cái", 8, "NCC003", "Nhựa Tân Phú", ""),

    ("D01-03", 1, True, "Nhãn decal PP sữa 90x60mm keo chịu ẩm", "Cái", 5000, 430,
     "5.000 - 50.000 cái", 8, "NCC004", "In ấn Minh Khai", "Mẫu in thử đạt"),
    ("D01-03", 2, False, "Nhãn decal giấy couche 90x60mm", "Cái", 5000, 380,
     "5.000 - 50.000 cái", 8, "NCC005", "In ấn Đại Việt", "Không chịu được ẩm"),

    #  Dòng D01-04 cố ý KHÔNG có phương án nào: nó đang *Cần khảo sát lại*, và
    #  thẻ phải bỏ trắng dòng báo giá chứ không hiện "0 đ".

    ("D02-02", 1, False, "Masterbatch xanh lá 2% chuẩn thực phẩm", "Kg", 500, 84000,
     "500 - 2.000 kg", 8, "NCC006", "Hóa chất ABA", ""),

    ("D02-03", 1, False, "Phụ gia chống UV Tinuvin 234", "Kg", 100, 152000,
     "100 - 500 kg", 10, "NCC007", "Hóa chất Sài Gòn", "Chờ báo giá NCC thứ hai"),
]


def _wipe_demo(db):
    """Xóa phiếu demo cũ + mọi dòng/phương án con. Trả về số phiếu đã xóa."""
    olds = db.query(SurveyRequest).filter(SurveyRequest.code.like(f"{DEMO_PREFIX}%")).all()
    if not olds:
        return 0
    ids = [s.id for s in olds]
    line_ids = [
        row[0]
        for row in db.query(SurveyRequestLine.id)
        .filter(SurveyRequestLine.survey_request_id.in_(ids))
        .all()
    ]
    #  Xóa từ LÁ vào GỐC: ba bảng nối nhau bằng id trần chứ không có khóa ngoại,
    #  nên xóa phiếu trước là để lại dòng và phương án mồ côi — chúng không hiện
    #  ở đâu cả nhưng `option_count` vẫn đếm và `progress_state` vẫn suy theo.
    if line_ids:
        db.query(SurveyRequestOption).filter(
            SurveyRequestOption.survey_request_line_id.in_(line_ids)
        ).delete(synchronize_session=False)
    db.query(SurveyRequestLine).filter(
        SurveyRequestLine.survey_request_id.in_(ids)
    ).delete(synchronize_session=False)
    db.query(SurveyRequest).filter(SurveyRequest.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return len(olds)


def run():
    db = SessionLocal()
    try:
        wiped = _wipe_demo(db)
        if wiped:
            print(f"Đã dọn {wiped} phiếu YCBG demo cũ.")

        by_code = {}
        for code, company_id, requester, department, purpose, request_date, status in DEMO_REQUESTS:
            sr = SurveyRequest(
                code=code, company_id=company_id, requester=requester,
                department=department, purpose=purpose,
                request_date=request_date, status=status,
            )
            db.add(sr)
            by_code[code] = sr
        db.commit()

        lines_by_code = {}
        for (sr_code, line_code, received, due, result, group, detail, other,
             qty, uom, price, assignee, pr_code, line_status, no_option) in DEMO_LINES:
            ln = SurveyRequestLine(
                survey_request_id=by_code[sr_code].id,
                internal_line_code=line_code,
                received_date=received, result_due_date=due, result_date=result,
                item_group=group, requirement_detail=detail, other_requirement=other,
                request_qty=qty, uom=uom, proposed_price=price,
                assignee=assignee, pr_code=pr_code,
                line_status=line_status,
                #  Giữ đúng bất biến ghi ở model: `is_completed` là bản sao của
                #  `line_status == LS_COMPLETED`, lệch nhau là hai màn đọc hai nguồn.
                is_completed=(line_status == LS_COMPLETED),
                no_option=no_option,
            )
            db.add(ln)
            lines_by_code[line_code] = ln
        db.commit()

        for (line_code, public_id, chosen, name, unit, moq, price, vol_range,
             vat, sup_code, sup_name, note) in DEMO_OPTIONS:
            db.add(SurveyRequestOption(
                survey_request_line_id=lines_by_code[line_code].id,
                public_id=public_id,
                display_label=f"Option {public_id}",
                is_chosen=chosen,
                snap_product_name=name, snap_quote_unit=unit, snap_moq=moq,
                snap_price_by_volume=price, snap_volume_range=vol_range, snap_vat=vat,
                supplier_code=sup_code, supplier_name=sup_name, nstm_note=note,
            ))
        db.commit()

        print(
            f"Đã tạo {len(DEMO_REQUESTS)} phiếu YCBG · "
            f"{len(DEMO_LINES)} dòng · {len(DEMO_OPTIONS)} phương án."
        )

        #  Kiểm chứng nhanh: in tiến độ suy ra của từng dòng. Đây là thứ duy nhất
        #  trong tệp không thể khẳng định bằng mắt khi đọc dữ liệu mẫu — nó là
        #  giá trị dẫn xuất, và cả màn Tiến độ báo giá dựng trên nó.
        from app.modules.survey_request.line_state import progress_state

        print("\nKiểm chứng nhanh — tiến độ suy ra của từng dòng:")
        for line_code, ln in lines_by_code.items():
            opts = (
                db.query(SurveyRequestOption)
                .filter(SurveyRequestOption.survey_request_line_id == ln.id)
                .all()
            )
            chosen = any(o.is_chosen for o in opts)
            print(f"  {line_code}: {progress_state(ln, chosen, len(opts))}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
