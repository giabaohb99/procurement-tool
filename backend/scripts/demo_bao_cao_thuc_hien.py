"""Dựng dữ liệu DEMO cho khối BÁO CÁO THỰC HIỆN của một phiếu YCBG.

Chạy:  docker compose exec api python -m scripts.demo_bao_cao_thuc_hien [ID]
Mặc định ID = 2927 (phiếu «Thùng carton 3 lớp» trên máy local).

CHẠY LẠI ĐƯỢC — xóa sạch giai đoạn/nút dòng hàng/hồ sơ cũ CỦA ĐÚNG PHIẾU ĐÓ rồi
dựng lại từ đầu, nên bấm thử hỏng thế nào cũng reset được.

CHỈ DÙNG Ở MÁY LOCAL. Đây là dữ liệu rác dùng để xem giao diện, đừng chạy trên
dev/prod.
"""
import sys
from datetime import date

import app.core.all_models  # noqa: F401 — nạp đủ model, không thì mapper User gãy
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.survey_request.model import SurveyRequest
from app.modules.survey_request.report_constants import DEFAULT_PHASES
from app.modules.survey_request.report_model import (SurveyReportDoc, SurveyReportItem,
                                                     SurveyReportPhase)

DEFAULT_REQUEST_ID = 2927

#  Mã trạng thái hồ sơ (R2/QĐ-11) — xem `report_constants.REPORT_DOC_STATUS_LABELS`.
IDLE, DOING, REVIEW, DONE = 0, 1, 2, 3

#  Nút dòng hàng. Nút CHUNG không nằm ở đây — hồ sơ chung mang `item_id = 0`.
ITEMS = ["Thùng carton 3 lớp"]

#  (giai đoạn 1..5, nút dòng hàng 0=CHUNG, tiêu đề, mô tả, bắt buộc, trạng thái,
#   tệp/link, tiên quyết theo SỐ THỨ TỰ trong chính danh sách này, bắt đầu, hết hạn)
DOCS = [
    # 1. Pháp lý & Giấy phép
    (1, 0, "Giấy đăng ký kinh doanh của NCC",
     "Bản sao công chứng còn hiệu lực. Đối chiếu ngành nghề in ấn - bao bì.",
     True, DONE, "GPKD-NCC.pdf", [], "2026-08-28", ""),
    (1, 0, "Hồ sơ năng lực & khách hàng tham chiếu",
     "Danh sách công trình đã làm, công suất xưởng, ảnh nhà máy.",
     False, DONE, "hosonangluc.pdf", [], "2026-08-28", ""),
    (1, 1, "Chứng nhận ISO 9001 của xưởng in",
     "Kiểm tra hiệu lực trước khi ký hợp đồng - hết hạn thì phải xin bản gia hạn.",
     True, DONE, "ISO9001.pdf", [], "", "2027-03-31"),
    (1, 1, "Kết quả thử nghiệm độ bền nén thùng (ECT)",
     "Mẫu carton 3 lớp, thử tại trung tâm đo lường. Chờ NCC gửi bản gốc.",
     True, REVIEW, "", [], "2026-09-01", ""),

    # 2. Đặt hàng & Hợp đồng
    (2, 0, "Báo giá chính thức có chữ ký & đóng dấu",
     "Giá đã gồm VAT, in 2 màu, giao tận kho Cần Thơ.",
     True, DONE, "BG-NCC-2609.pdf", [1], "2026-09-02", ""),
    (2, 1, "Duyệt maquette in (file thiết kế)",
     "File AI/PDF của phòng Marketing, đúng bộ nhận diện.",
     True, DONE, "maquette-v3.pdf", [], "", ""),
    (2, 1, "Duyệt mẫu in thử (proof) có ký xác nhận",
     "In thử 5 thùng, kiểm màu và độ lệch dao. Ký lên chính mẫu rồi chụp lại.",
     True, DOING, "", [6], "2026-09-08", ""),
    (2, 0, "Hợp đồng nguyên tắc",
     "Điều khoản thanh toán 30/70, phạt chậm giao 0,5%/ngày.",
     True, DOING, "", [5], "2026-09-08", ""),
    (2, 0, "Đơn mua hàng (PO) phát hành",
     "Phát hành sau khi hợp đồng ký xong và mẫu in được duyệt.",
     True, IDLE, "", [7, 8], "", ""),
    (2, 0, "Xác nhận đơn hàng của NCC",
     "NCC xác nhận số lượng, đơn giá và ngày giao bằng văn bản.",
     False, IDLE, "", [9], "", ""),

    # 3. Sản xuất & Vận chuyển
    (3, 1, "Lịch sản xuất & ngày giao dự kiến",
     "NCC gửi lịch chia lô: 2.500 cái đợt 1, 2.500 cái đợt 2.",
     True, IDLE, "", [9], "", ""),
    (3, 1, "Ảnh tiến độ sản xuất",
     "Ảnh chụp tại xưởng mỗi đợt - dùng để đối chiếu khi chậm giao.",
     False, IDLE, "", [11], "", ""),
    (3, 0, "Phiếu xuất kho kiêm vận chuyển nội bộ của NCC",
     "Kèm biển số xe và tên tài xế để bảo vệ cho vào kho.",
     True, IDLE, "", [11], "", ""),
    (3, 0, "Lịch giao hàng chốt với kho",
     "Chốt giờ nhận với thủ kho, tránh trùng ngày kiểm kê.",
     True, IDLE, "", [13], "", ""),

    # 4. Kiểm tra & Thông quan
    (4, 1, "Biên bản kiểm tra kích thước & quy cách 3 lớp",
     "Đo ngẫu nhiên 20 thùng/lô, dung sai +/- 2mm.",
     True, IDLE, "", [13], "", ""),
    (4, 1, "Biên bản kiểm tra chất lượng in",
     "Soi màu với mẫu proof đã duyệt, kiểm độ lệch dao và bong mực.",
     True, IDLE, "", [7, 13], "", ""),
    (4, 0, "Phiếu lấy mẫu lưu",
     "Giữ 2 thùng mỗi lô làm mẫu đối chứng khi có khiếu nại.",
     False, IDLE, "", [15], "", ""),
    (4, 0, "Biên bản xử lý hàng không đạt",
     "Chỉ lập khi có lô không đạt - ghi rõ số lượng trả và hướng xử lý.",
     False, IDLE, "", [15, 16], "", ""),

    # 5. Nhận hàng & Về kho
    (5, 0, "Biên bản giao nhận có ký hai bên",
     "Ký sau khi kiểm tra xong, ghi số lượng thực nhận.",
     True, IDLE, "", [15, 16], "", ""),
    (5, 0, "Phiếu nhập kho",
     "Nhập theo đúng mã hàng, đối chiếu với đơn mua hàng.",
     True, IDLE, "", [19], "", ""),
    (5, 0, "Hóa đơn GTGT",
     "Kiểm tên, mã số thuế, đơn giá trước khi chuyển kế toán.",
     True, IDLE, "", [20], "", ""),
    (5, 0, "Biên bản đối chiếu công nợ",
     "Đối chiếu cuối tháng trước khi đề nghị thanh toán phần 70%.",
     False, IDLE, "", [21], "", ""),
]

#  Hồ sơ được cử người thực hiện (theo số thứ tự ở DOCS) — phần còn lại để trống
#  cho giống thực tế: nhiều hồ sơ chưa ai nhận.
ASSIGNED = {1, 5, 7, 8, 11, 15, 19, 20}


def _to_date(value: str):
    return date.fromisoformat(value) if value else None


def main(request_id: int) -> None:
    db = SessionLocal()
    try:
        request = db.get(SurveyRequest, request_id)
        if not request:
            raise SystemExit(f"Không có phiếu YCBG id {request_id} trong DB này")

        for model in (SurveyReportDoc, SurveyReportPhase, SurveyReportItem):
            db.query(model).filter(model.survey_request_id == request_id).delete()
        db.flush()

        employee = db.query(Employee).order_by(Employee.id).offset(2).first()
        assignee_id = employee.id if employee else 0

        phases = []
        for order, (name, location) in enumerate(DEFAULT_PHASES, start=1):
            phase = SurveyReportPhase(
                survey_request_id=request_id, name=name, location=location, sort_order=order
            )
            db.add(phase)
            phases.append(phase)

        items = []
        for order, name in enumerate(ITEMS, start=1):
            item = SurveyReportItem(survey_request_id=request_id, name=name, sort_order=order)
            db.add(item)
            items.append(item)
        db.flush()

        #  Hai lượt: lượt đầu tạo hồ sơ để có id thật, lượt sau mới nối tiên quyết
        #  (tiên quyết khai bằng SỐ THỨ TỰ, phải đổi sang id sau khi flush).
        docs = []
        for order, row in enumerate(DOCS, start=1):
            phase_no, item_no, title, description, required, status, file_note, _, start, expires = row
            doc = SurveyReportDoc(
                survey_request_id=request_id,
                phase_id=phases[phase_no - 1].id,
                item_id=items[item_no - 1].id if item_no else 0,
                title=title,
                description=description,
                required=required,
                status=status,
                file_note=file_note,
                depends=[],
                start_date=_to_date(start),
                expires_at=_to_date(expires),
                assignee_id=assignee_id if order in ASSIGNED else 0,
                sort_order=order,
            )
            db.add(doc)
            docs.append(doc)
        db.flush()

        for doc, row in zip(docs, DOCS):
            doc.depends = [docs[no - 1].id for no in row[7]]

        db.commit()
        print(
            f"OK — phiếu {request.code} (id {request_id}): "
            f"{len(phases)} giai đoạn · {len(items)} nút dòng hàng · {len(docs)} hồ sơ"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_REQUEST_ID)
