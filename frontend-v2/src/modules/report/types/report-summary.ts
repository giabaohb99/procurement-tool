/**
 * Hình dữ liệu các đường `/summary` nuôi màn BIỂU ĐỒ của phân hệ Báo cáo. Mỗi
 * đường dùng CHUNG bộ lọc + phạm vi với bảng phân trang tương ứng bên Thu mua,
 * nên số trên biểu đồ khớp số dòng của bảng.
 */

/**
 * Một nhóm của bản tổng hợp Chi tiết YC mua hàng. `idle_*` = dòng CHƯA ĐƯỢC ĐẶT
 * (no_po + not_ordered). Mọi nhóm đã BỎ dòng hủy — chỉ `by_line_status` còn đếm.
 */
export interface PrLinesBucket {
  lines: number
  idle_lines: number
  amount: number
  idle_amount: number
}

/** `GET /api/reports/pr-lines/summary` — cùng bộ lọc + scope với bảng `/pr-lines`. */
export interface PrLinesSummary {
  total: PrLinesBucket
  /** Đếm MỌI dòng kể cả hủy; `code` là mã `PR_LINE_STATUS`. */
  by_line_status: { code: string; lines: number; amount: number }[]
  /** Chỉ tháng có phát sinh, 'YYYY-MM' tăng dần. */
  by_month: (PrLinesBucket & { month: string })[]
  /** Sắp giảm dần theo giá trị. `(Không rõ)` khi bỏ trống. */
  by_department: (PrLinesBucket & { key: string })[]
  by_item_group: (PrLinesBucket & { key: string })[]
  /** Sắp giảm dần theo số dòng CHƯA ĐẶT. `code` rỗng = dòng chưa gán NSTM. */
  by_assignee: (PrLinesBucket & { code: string; name: string })[]
}

/** `GET /api/purchase-progress/summary` — Tiến độ mua hàng. */
export interface PurchaseProgressSummary {
  total: {
    /** Số DÒNG hàng (một dòng nhiều lần giao vẫn đếm một). */
    items: number
    /** Lần giao ĐÃ NHẬN. */
    deliveries: number
    /** Lần giao trễ hẹn NCC hoặc trễ quy định. */
    late: number
    /** Dòng có SL đặt > 0, xếp theo tổng đã nhận: chưa nhận gì · nhận thiếu · nhận đủ. */
    unreceived: number
    under: number
    full: number
  }
  /** `code` là mã `PO_PROGRESS_STATUS`. */
  by_progress_status: { code: string; items: number }[]
  /** Theo tháng NHẬN hàng, chỉ tháng có phát sinh. */
  by_month: { month: string; received: number; late: number }[]
  /** Rỗng khi người xem thiếu `supplier.read`. Sắp giảm dần theo số lần trễ. */
  by_supplier: { key: string; received: number; late: number }[]
  /** Sắp giảm dần theo số dòng còn mở. */
  by_department: { key: string; items: number; open: number }[]
  show_supplier: boolean
}

/** `GET /api/survey-progress/summary` — Tiến độ báo giá. */
export interface SurveyProgressSummary {
  total: {
    lines: number
    late: number
    answered: number
    /** Dòng chưa tới «Đã tạo YCMH» / «Hoàn thành». */
    open: number
    /** Trung bình số ngày xử lý của dòng đã trả kết quả; `null` khi chưa có dòng nào. */
    avg_handling_days: number | null
  }
  /** Nhãn tiến độ do backend dựng (cột tính, không lưu DB), đã xếp theo chuỗi tiến độ. */
  by_state: { state: string; lines: number }[]
  /** Theo tháng YÊU CẦU của phiếu. */
  by_month: { month: string; lines: number; late: number }[]
  /** `name` rỗng = dòng chưa giao NSTM. Sắp giảm dần theo số dòng mở. */
  by_assignee: { name: string; lines: number; open: number; late: number }[]
  by_item_group: { key: string; lines: number; late: number }[]
}

/** `GET /api/survey-report/summary` — Báo cáo khảo sát. */
export interface SurveyReportSummary {
  total: number
  /** Bốn nhãn duyệt lưu CHỮ ở DB (ngoại lệ đã biết của hai bảng dòng khảo sát). */
  by_approve: { state: string; lines: number }[]
  by_kind: { supplier: number; product: number }
  /** Theo ngày liên hệ của dòng (lùi về ngày nhận phiếu). */
  by_month: { month: string; supplier: number; product: number }[]
  by_nspt: { key: string; lines: number; approved: number }[]
  by_item_group: { key: string; lines: number; approved: number }[]
}
