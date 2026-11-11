import { apiGet, downloadFile } from '@/core/api'

/**
 * Ma trận "Tổng hợp theo người" của Quỹ phép năm (duoc-CR-717) — mỗi người một dòng, mỗi loại
 * nghỉ CÓ trừ quỹ một cột, ô = số NGÀY DÙNG ĐƯỢC (`available_days`, loại cộng dần đã trừ phần
 * chưa tới tháng). Gác `leave_balance.read` / `export` + phạm vi; không có khóa báo cáo.
 */

const MATRIX = '/api/leave-balances/matrix'

export interface LeaveBalanceMatrixColumn {
  leave_type_id: number
  name: string
}

export interface LeaveBalanceMatrixRow {
  employee_id: number
  code: string
  name: string
  department_name: string
  /** Chính sách áp trong năm đang xem (duoc-CR-745), nhiều gói nối bằng mũi tên; rỗng = theo loại nghỉ. */
  policy_name?: string
  /**
   * ⚠️ Khóa là CHUỖI id loại nghỉ (JSON không có khóa số). Người thiếu dòng quỹ của một loại thì
   * VẮNG khóa đó — khác hẳn số `0` (có quỹ, đã dùng hết).
   */
  cells: Record<string, number>
  total: number
}

export interface LeaveBalanceMatrix {
  year: number
  /** Cột cố định cho CẢ kết quả (không đổi theo trang), đúng thứ tự `sort_order, id`. */
  columns: LeaveBalanceMatrixColumn[]
  items: LeaveBalanceMatrixRow[]
  /** Tổng số NGƯỜI khớp bộ lọc — phân trang đếm theo người. */
  total: number
}

/** `employee_status` vắng = `working` ở backend; ngoài ba giá trị này là 422. */
export type LeaveBalanceMatrixEmployeeStatus = 'working' | 'resigned' | 'all'

export interface LeaveBalanceMatrixParams {
  year: number
  company_id?: number
  /** Phòng HIỆN TẠI của người giữ quỹ. */
  department_id?: number
  employee_status?: LeaveBalanceMatrixEmployeeStatus
  search?: string
  page?: number
  page_size?: number
}

export const leaveBalanceMatrixApi = {
  get: (params: LeaveBalanceMatrixParams) => apiGet<LeaveBalanceMatrix>(MATRIX, { params }),

  /** Xuất Excel cùng bộ lọc, KHÔNG phân trang (backend tối đa 5000 người; ô thiếu = 0). */
  exportExcel: (params: LeaveBalanceMatrixParams) => {
    const filters: Record<string, unknown> = { ...params }
    delete filters.page
    delete filters.page_size
    return downloadFile(`${MATRIX}/export`, `quy-phep-theo-nhan-su-${params.year}.xlsx`, filters)
  },
}
