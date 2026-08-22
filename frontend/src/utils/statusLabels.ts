// Bộ mã của Nhân sự, Nhà cung cấp, Công nợ và cụm Đơn mua hàng + Yêu cầu mua hàng — tầng
// hiển thị của `backend/app/core/status_codes.py` (B-03, B-05 và B-06, xem
// `doc/erp/15-do-be-tong-nen-v2.md`).
//
// Từ B-03, `tab_employee.status` và `tab_supplier.legal_type` lưu MÃ tiếng Anh; từ B-05 thì
// `tab_payable.status` cũng vậy; từ B-06 là sáu cột của cụm ĐMH + YCMH. Chữ tiếng Việt chỉ
// còn ở đây và ở `*_label` mà API gửi kèm.
//
// ⚠️ Bản này CHÉP TAY, cố ý — cùng lý do đã ghi ở `contractStatus.ts` (B-02): `frontend/`
// đã đóng băng (D-026) nên không nối vào `backend/scripts/gen_status_ts.py`, bộ sinh chỉ
// ghi cho `frontend-v2/`. Đây là bản vá cho sống tới ngày tắt `frontend/`; thêm mã mới thì
// sửa ở Python trước, rồi mới ngó lại đây. Đợt B-xx sau thêm bộ mã vào ĐÚNG tệp này, đừng
// đẻ thêm tệp thứ ba.
export const EMPLOYEE_STATUSES = [
  { value: 'official', label: 'Chính thức' },
  { value: 'collaborator', label: 'Cộng tác viên' },
  { value: 'maternity_leave', label: 'Nghỉ thai sản' },
  { value: 'resigned', label: 'Nghỉ việc' },
]

export const SUPPLIER_LEGAL_TYPES = [
  { value: 'company', label: 'Công ty' },
  { value: 'individual', label: 'Cá nhân' },
  { value: 'partnership', label: 'Hợp danh' },
  { value: 'household', label: 'Hộ kinh doanh' },
]

// B-05 — `tab_payable.status`. Không ai chọn giá trị này: backend tính lại từ số đã trả so
// với tổng nợ sau mỗi lần phân bổ thanh toán. Ở đây chỉ dùng để hiện chữ và làm option ô lọc.
//
// ⚠️ "Trả dư" KHÔNG có trong danh sách này và đừng thêm vào. Đó là trạng thái CHỈ ĐỂ HIỆN,
// `supplier-payables-stats.ts` tự suy ra khi `remaining < 0`, chưa bao giờ nằm trong DB.
// Thêm nó vào đây là mời người sau gửi nó lên làm tham số lọc — backend không có dòng nào
// mang giá trị đó nên bảng sẽ rỗng mà không báo lỗi gì.
export const PAYABLE_STATUSES = [
  { value: 'unpaid', label: 'Chờ thanh toán' },
  { value: 'partial', label: 'Thanh toán một phần' },
  { value: 'paid', label: 'Đã thanh toán' },
]

// ── B-06: cụm Đơn mua hàng + Yêu cầu mua hàng ────────────────────────────────────
// Sáu cột: `tab_purchase_request_item.line_status`, `tab_purchase_order.document_status`,
// `tab_po_item.line_status`, `tab_po_delivery.status`, `tab_po_item.progress_status` và
// `tab_po_item.status_before_pause` (cột cuối lưu cùng bộ mã với `progress_status`).

// Trạng thái dòng YCMH. `no_po` là mặc định của dòng mới (CR-074).
export const PR_LINE_STATUSES = [
  { value: 'no_po', label: 'Chưa tạo đơn mua hàng' },
  { value: 'not_ordered', label: 'Chưa đặt hàng' },
  { value: 'ordered', label: 'Đã đặt hàng' },
  { value: 'received', label: 'Đã nhận hàng' },
  { value: 'completed', label: 'Hoàn thành' },
  { value: 'cancelled', label: 'Hủy đơn' },
]

// Hồ sơ chứng từ của ĐMH. ⚠️ Nhãn cũ lưu trong DB viết THƯỜNG ('đã đủ chứng từ') vì màn cũ
// dựa vào `first-letter:uppercase` của CSS; nhãn ở đây viết hoa đầu câu như mọi bộ khác.
export const PO_DOCUMENT_STATUSES = [
  { value: 'none', label: 'Chưa có chứng từ' },
  { value: 'partial', label: 'Đã có thông tin chứng từ' },
  { value: 'full', label: 'Đã đủ chứng từ' },
]

// Mức giao hàng của MỘT DÒNG ĐMH — KHÁC `progress_status`. Cột này không bao giờ mang giá
// trị hủy; việc hủy dòng nằm ở `progress_status`.
export const PO_ITEM_LINE_STATUSES = [
  { value: 'not_delivered', label: 'Chưa giao' },
  { value: 'partial', label: 'Đang giao' },
  { value: 'full', label: 'Đủ' },
]

// Trạng thái của MỘT LẦN GIAO.
export const PO_DELIVERY_STATUSES = [
  { value: 'pending', label: 'Chờ giao' },
  { value: 'short', label: 'Giao thiếu' },
  { value: 'defect', label: 'Lỗi' },
  { value: 'received', label: 'Đã nhận' },
]

// Tiến độ dòng ĐMH. Sáu mã đầu là một chuỗi tuần tự backend tự tính theo dữ liệu; hai mã
// cuối (`paused`, `cancelled`) là nhánh rẽ, chỉ đặt tay được và bắt buộc kèm lý do.
export const PO_PROGRESS_STATUSES = [
  { value: 'not_ordered', label: 'Chưa đặt hàng' },
  { value: 'ordered', label: 'Đã đặt hàng' },
  { value: 'received', label: 'Đã nhận hàng' },
  { value: 'doc_pending', label: 'Chưa gửi ĐMH cho KT' },
  { value: 'doc_sent', label: 'Đã gửi ĐMH cho KT' },
  { value: 'completed', label: 'Hoàn thành' },
  { value: 'paused', label: 'Tạm ngưng' },
  { value: 'cancelled', label: 'Hủy đơn' },
]

const mkLabel = (opts: { value: string; label: string }[]) => {
  const m: Record<string, string> = Object.fromEntries(opts.map((o) => [o.value, o.label]))
  // Mã lạ thì trả NGUYÊN giá trị — dòng chưa chạy migration vẫn phải đọc được, thà hiện
  // chữ tiếng Việt cũ còn hơn hiện ô trống làm người dùng tưởng mất dữ liệu.
  return (v?: string | null) => (v ? m[v] || v : '')
}

export const employeeStatusLabel = mkLabel(EMPLOYEE_STATUSES)
export const supplierLegalTypeLabel = mkLabel(SUPPLIER_LEGAL_TYPES)
export const payableStatusLabel = mkLabel(PAYABLE_STATUSES)
export const prLineStatusLabel = mkLabel(PR_LINE_STATUSES)
export const poDocumentStatusLabel = mkLabel(PO_DOCUMENT_STATUSES)
export const poItemLineStatusLabel = mkLabel(PO_ITEM_LINE_STATUSES)
export const poDeliveryStatusLabel = mkLabel(PO_DELIVERY_STATUSES)
export const poProgressStatusLabel = mkLabel(PO_PROGRESS_STATUSES)
