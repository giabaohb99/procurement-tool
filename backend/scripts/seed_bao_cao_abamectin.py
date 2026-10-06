"""Nạp bảng kế hoạch «2870 — Kế hoạch Abamectin 3.6» (Excel của Thu mua) vào khối
Báo cáo thực hiện của MỘT đơn mua hàng — để đại ca xem thử dữ liệu thật trên màn
(bao-CR-598).

    docker compose exec -T api python scripts/seed_bao_cao_abamectin.py <id ĐMH> [--ghi-de]

Ánh xạ cột Excel → trường hồ sơ (ghi ở doc bao-CR-598):
    STT → thứ tự · Hạng mục → tiêu đề · Công việc chi tiết → mô tả
    Người/Đơn vị phụ trách → nhân sự thực hiện (tra theo tên, không thấy thì để trống)
    Ngày thực hiện → ngày bắt đầu · Time xử lý (ngày) → suy ra, không lưu
    Trạng thái → mã (Đang thực hiện = Đang làm, Chưa hoàn thành = Chưa bắt đầu)
    Ngày dự kiến hoàn thành → dự định hoàn tất · Kết quả → kết quả · Link → tệp/link
Bảng Excel không có giai đoạn: xếp vào 5 giai đoạn mẫu theo khâu; mỗi dòng là
tiên quyết của dòng kế (bảng chạy tuần tự). Mọi hồ sơ gắn nút dòng hàng ĐẦU TIÊN
của đơn (kế hoạch này là của một mặt hàng); đơn không có dòng thì để Chung.
"""
from __future__ import annotations

import sys
from datetime import date

from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.survey_request import report_service as svc
from app.modules.survey_request.report_constants import (DEFAULT_PHASES, RD_DOING,
                                                         RD_DONE, RD_IDLE)
from app.modules.survey_request.report_model import (SurveyReportDoc, SurveyReportItem,
                                                     SurveyReportPhase)

OWNER = "purchase_order"

STATUS_OF = {
    "Đang thực hiện": RD_DOING,
    "Chưa hoàn thành": RD_IDLE,
    "Hoàn thành": RD_DONE,
}

#  (giai đoạn 1..5, hạng mục, công việc chi tiết, người phụ trách, ngày thực hiện,
#   số ngày xử lý, trạng thái, ngày dự kiến hoàn thành)
ROWS = [
    (2, "Tìm NCC nước ngoài", "Mục tiêu: Nhập hàng năm 2025\nKế hoạch: đang deal giá 3 nhà cung cấp, và thời gian công nợ\nĐã tìm được 2 NCC: Aston, Anhui", "Tiên", "2024-12-24", 1, "Đang thực hiện", "2024-12-25"),
    (2, "Lấy mẫu", "NCC:", "Tiên", "2024-12-25", 0, "Đang thực hiện", "2024-12-25"),
    (2, "Deal giá + hình thức thanh toán công nợ", "NCC:\nAston:\nAnhui:", "Tiên", "2024-12-25", 5, "Đang thực hiện", "2024-12-30"),
    (2, "Duyệt giá", "Báo cáo giá và chính sách với lãnh đạo", "Ngân", "2024-12-30", 1, "Chưa hoàn thành", "2024-12-31"),
    (2, "Chốt PO Ký hợp đồng", "Ký hợp đồng", "Tiên", "2024-12-31", 1, "Chưa hoàn thành", "2025-01-01"),
    (2, "Dự trù tài chính", "Dự trù tài chính với kế toán", "Tiên", "2025-01-01", 1, "Chưa hoàn thành", "2025-01-02"),
    (3, "NCC sắp xếp hàng hóa trước mỗi sáng Thứ 6", "Trước sáng thứ 6 hàng tuần", "Tiên", "2025-01-02", 7, "Chưa hoàn thành", "2025-01-09"),
    (3, "Chuẩn bị hàng", "Trong vòng 7 ngày", "Tiên", "2025-01-09", 7, "Chưa hoàn thành", "2025-01-16"),
    (3, "Vận chuyển hàng từ Nhà máy -> cảng", "Trong vòng 5 ngày", "Tiên", "2025-01-16", 5, "Chưa hoàn thành", "2025-01-21"),
    (3, "Đóng hàng lên tàu, Tàu chạy", "Yêu cầu tàu chạy ETD (Có thể delay 1 tuần)", "Tiên", "2025-01-21", 3, "Chưa hoàn thành", "2025-01-24"),
    (4, "Hàng về cập cảng + Tờ khai hàng nhập", "Trong vòng 3 ngày", "Tiên", "2025-01-24", 3, "Chưa hoàn thành", "2025-01-27"),
    (4, "Phương án không kịp thời gian", "", "Tiên", "2025-01-27", 1, "Chưa hoàn thành", "2025-01-28"),
    (4, "Đóng thuế", "", "Tiên", "2025-01-28", 2, "Chưa hoàn thành", "2025-01-30"),
    (4, "Kéo hàng về kho", "", "Tiên", "2025-01-30", 2, "Chưa hoàn thành", "2025-02-01"),
    (4, "Lấy mẫu kiểm dịch", "", "Tiên", "2025-02-01", 1, "Chưa hoàn thành", "2025-02-02"),
    (4, "Chờ kết quả kiểm dịch", "", "Tiên", "2025-02-02", 7, "Chưa hoàn thành", "2025-02-09"),
    (4, "Có kết quả", "", "Tiên", "2025-02-09", 1, "Chưa hoàn thành", "2025-02-10"),
    (4, "Thông Quan", "", "Tiên", "2025-02-10", 1, "Chưa hoàn thành", "2025-02-11"),
    (5, "Đưa hàng vào sản xuất", "", "Tiên", "2025-02-11", 1, "Chưa hoàn thành", "2025-02-12"),
    (5, "Lấy mẫu check đối chiếu", "", "Tiên", "2025-02-12", 7, "Chưa hoàn thành", "2025-02-19"),
    (5, "Theo dõi thanh toán công nợ", "", "Tiên", "2025-02-19", 90, "Chưa hoàn thành", "2025-05-20"),
]


def _employee_id_by_name(db, name: str) -> int:
    """Tra nhân sự theo TÊN GỌI trong Excel («Tiên», «Ngân») — lấy người đầu tiên đang
    làm việc có tên kết thúc bằng chữ đó; không thấy thì 0 (chưa cử)."""
    rows = (db.query(Employee.id, Employee.full_name)
            .filter(Employee.full_name.like(f"%{name}"))
            .order_by(Employee.id).all())
    return rows[0][0] if rows else 0


def main(po_id: int, overwrite: bool) -> None:
    db = SessionLocal()
    try:
        po = db.get(PurchaseOrder, po_id)
        if not po:
            raise SystemExit(f"Không có đơn mua hàng id {po_id} trong DB này")
        head = svc.ensure_report(db, OWNER, po.id, user_id=0)
        rid = head.id
        has_any = db.query(SurveyReportDoc.id).filter_by(report_id=rid).first() is not None
        if has_any and not overwrite:
            raise SystemExit(f"Đơn {po.code} đã có báo cáo thực hiện — thêm --ghi-de để làm lại")
        for model in (SurveyReportDoc, SurveyReportItem, SurveyReportPhase):
            db.query(model).filter(model.report_id == rid).delete(synchronize_session=False)
        db.flush()

        phases = [svc.create_phase(db, rid, name, location, 0) for name, location in DEFAULT_PHASES]
        lines = [(it.id, (it.product_name or it.product_code or "").strip()[:100] or f"Dòng {n + 1}")
                 for n, it in enumerate(po_service.items_of(db, po.id))]
        items = [svc.create_item(db, rid, name, 0, line_id=line_id) for line_id, name in lines]
        item_id = items[0].id if items else 0

        assignee_cache: dict[str, int] = {}
        docs: list[SurveyReportDoc] = []
        for order, (phase_no, title, detail, who, start, days, status, planned) in enumerate(ROWS):
            if who not in assignee_cache:
                assignee_cache[who] = _employee_id_by_name(db, who)
            doc = SurveyReportDoc(
                report_id=rid, phase_id=phases[phase_no - 1].id, item_id=item_id,
                title=title, description=detail, required=True,
                status=STATUS_OF.get(status, RD_IDLE), file_note="", result="",
                depends=[], start_date=date.fromisoformat(start),
                planned_date=date.fromisoformat(planned),
                assignee_id=assignee_cache[who], sort_order=order,
                created_by=0, updated_by=0)
            assert (doc.planned_date - doc.start_date).days == days, (title, days)
            db.add(doc)
            docs.append(doc)
        db.flush()
        for previous, doc in zip(docs, docs[1:]):      # bảng chạy tuần tự: dòng sau chờ dòng trước
            doc.depends = [previous.id]
        db.commit()
        missing = [who for who, eid in assignee_cache.items() if not eid]
        print(f"OK — đơn {po.code} (id {po.id}): {len(phases)} giai đoạn · {len(items)} nút dòng hàng · "
              f"{len(docs)} hồ sơ" + (f" · chưa tra được nhân sự: {', '.join(missing)}" if missing else ""))
    finally:
        db.close()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    main(int(args[0]), overwrite="--ghi-de" in sys.argv)
