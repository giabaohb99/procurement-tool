/**
 * Kiểu & bộ mã của phân hệ DUYỆT DẤU (yêu cầu đóng dấu).
 *
 * Cột `status` backend lưu SMALLINT (rule R2) và trả kèm số + nhãn. Bản đối chiếu
 * nhãn ở đây phải KHỚP `SEAL_STATUS_LABELS` bên backend (`model.py`).
 */

// --- Trạng thái phiếu -----------------------------------------------------
export const SEAL_STATUS = {
  draft: 1, // Nháp
  pending: 2, // Chờ duyệt (TBP)
  approved: 3, // Đã duyệt — chờ Văn thư đóng dấu
  completed: 4, // Hoàn thành
  rejected: 5, // Từ chối
  cancelled: 6, // Đã hủy
  returned: 7, // Yêu cầu chỉnh sửa
} as const
export type SealStatus = (typeof SEAL_STATUS)[keyof typeof SEAL_STATUS]

export const SEAL_STATUS_LABELS: Record<number, string> = {
  [SEAL_STATUS.draft]: 'Nháp',
  [SEAL_STATUS.pending]: 'Chờ duyệt',
  [SEAL_STATUS.approved]: 'Đã duyệt',
  [SEAL_STATUS.completed]: 'Hoàn thành',
  [SEAL_STATUS.rejected]: 'Từ chối',
  [SEAL_STATUS.cancelled]: 'Đã hủy',
  [SEAL_STATUS.returned]: 'Yêu cầu chỉnh sửa',
}

/**
 * Tông màu badge dạng "pill" (gray/warn/ok/err/info). Màu cụ thể của mỗi tông
 * khai ở `components/status-pill.tsx` — đây chỉ là bản đồ trạng thái → tông.
 */
export type BadgeTone = 'gray' | 'warn' | 'ok' | 'err' | 'info'

export const SEAL_STATUS_BADGE: Record<number, BadgeTone> = {
  [SEAL_STATUS.draft]: 'gray', // Nháp
  [SEAL_STATUS.pending]: 'warn', // Chờ duyệt
  [SEAL_STATUS.approved]: 'info', // Đã duyệt (chờ đóng dấu)
  [SEAL_STATUS.completed]: 'ok', // Hoàn thành
  [SEAL_STATUS.rejected]: 'err', // Từ chối
  [SEAL_STATUS.cancelled]: 'gray', // Đã hủy — kết thúc, trung tính
  [SEAL_STATUS.returned]: 'warn', // Yêu cầu chỉnh sửa (bị trả lại)
}

/**
 * Màu lát bánh của biểu đồ "Cơ cấu theo trạng thái" — khai THEO MÃ trạng thái,
 * không theo thứ hạng trong mảng dữ liệu.
 *
 * ⚠️ Bản trước lấy `STATUS_COLORS[i % 5]` với `i` là vị trí sau khi đã lọc bỏ
 * trạng thái rỗng. Hai lỗi cùng lúc: bộ mã có BẢY trạng thái mà bảng màu chỉ
 * năm màu nên «Yêu cầu chỉnh sửa» tô lại đúng màu của «Nháp» (thấy được trên
 * máy thật: hai ô chú giải xanh y hệt nhau); và vì đánh theo thứ hạng nên kỳ
 * nào không có phiếu Nháp là toàn bộ màu dịch một bậc — người đã quen "xanh lá
 * là xong" đọc sai cả biểu đồ.
 *
 * Màu lấy đúng tinh thần tông huy hiệu ở `SEAL_STATUS_BADGE`: cảnh báo = cam,
 * xong = xanh lá, hỏng = đỏ, trung tính = xám. Nháp và Đã hủy cùng tông xám ở
 * huy hiệu nhưng phải KHÁC nhau trên bánh (hai lát cạnh nhau), nên một xám
 * nhạt một xám đậm.
 */
export const SEAL_STATUS_CHART_COLOR: Record<number, string> = {
  [SEAL_STATUS.draft]: 'var(--chart-neutral)',
  [SEAL_STATUS.pending]: 'var(--warning)',
  [SEAL_STATUS.approved]: 'var(--info)',
  [SEAL_STATUS.completed]: 'var(--success)',
  [SEAL_STATUS.rejected]: 'var(--destructive)',
  [SEAL_STATUS.cancelled]: 'var(--muted-foreground)',
  [SEAL_STATUS.returned]: 'var(--chart-2)',
}

/** Chỉ sửa được khi phiếu còn nháp hoặc bị trả về (khớp EDITABLE_STATUSES ở backend). */
export const EDITABLE_SEAL_STATUSES = new Set<number>([SEAL_STATUS.draft, SEAL_STATUS.returned])

/**
 * Một pháp nhân cần đóng dấu, kèm sẵn logo + MST để bày trong ô chọn / chip / bản
 * in mà không phải tra lại danh mục Công ty (khớp phần tử của `companies`).
 */
export interface SealCompanyRef {
  id: number
  name: string
  tax_code: string
  logo: string
}

// --- Bản ghi phiếu (khớp SealRequestResponse) -----------------------------
export interface SealRequest {
  id: number
  code: string
  title?: string
  copies?: number
  status: number
  status_label: string
  purpose: string
  /** Danh sách id pháp nhân cần đóng dấu — nguồn điền lại cho ô chọn khi sửa. */
  company_ids: number[]
  /** Bản hiển thị của từng pháp nhân (logo + tên + MST). */
  companies: SealCompanyRef[]
  department_id: number
  first_approver_id: number
  approver_name: string
  /** Thời điểm TBP duyệt (ISO), rỗng nếu chưa duyệt. */
  approved_at: string
  /** Văn thư đã đóng dấu + thời điểm hoàn thành. */
  completed_by_name: string
  completed_at: string
  requester: string
  requester_id: number
  requester_email: string
  requester_phone: string
  requester_role: string
  note: string
  created_at: string | null
  /** True khi phiếu đang chạy một phiên duyệt nhiều bước (bộ máy `ApprovalSwitch`). */
  approval_running: boolean
  /** ID phiên duyệt gần nhất, KỂ CẢ phiên đã xong — `null` nếu phiếu chưa vào bộ máy.
   *  Gác thẻ Lịch sử phê duyệt bằng ô này, không bằng `approval_running`. Chỉ có ở
   *  phản hồi CHI TIẾT. */
  approval_instance_id?: number | null
  /** Người xem có được thao tác CỔNG-2 (đóng dấu / trả / từ chối) không — CHỈ Văn thư
   *  được phân công (hoặc quản trị). Có ở phản hồi CHI TIẾT; danh sách không kèm. */
  can_stamp?: boolean
}

/** Payload tạo/sửa phiếu — form gửi đúng bộ trường backend nhận. */
export interface SealRequestPayload {
  purpose: string
  company_ids: number[]
  department_id?: number
  first_approver_id: number
  note: string
}

// --- Danh sách người duyệt hợp lệ (GET /api/seal-requests/approvers) -------
/** Một TBP đủ điều kiện duyệt yêu cầu đóng dấu. */
export interface SealApprover {
  id: number
  name: string
  email: string
  /** Ảnh đại diện của TBP (rỗng → hiện chữ cái đầu). */
  avatar: string
  department_id: number
  /** Là trưởng bộ phận thật (quản lý một phòng ban) — được xếp lên đầu danh sách. */
  is_dept_head: boolean
  /** TBP mặc định (trưởng bộ phận của người tạo) — được chọn sẵn khi tạo mới. */
  is_default: boolean
}

export interface SealApproversResult {
  items: SealApprover[]
  /** Id người duyệt mặc định; 0 khi không suy ra được. */
  default_id: number
}
