import { apiGet, downloadFile } from '@/core/api'
import type {
  DailyReport,
  MatrixRow,
  ProcurementReport,
  ReportMatrix,
  RequestMatrix,
  ShippingDetailResult,
} from '../types/purchase-report'

/**
 * Tham số dùng chung của mọi đường báo cáo. Bỏ trống = không lọc.
 *
 * Khai bằng `type` chứ không phải `interface`: mấy hàm khóa cache nhận
 * `Record<string, unknown>`, mà interface KHÔNG tự có chữ ký chỉ mục ngầm nên
 * truyền vào là lỗi kiểu — type alias thì có.
 */
export type ReportScope = {
  /** 'YYYY' hoặc 'all'. */
  year?: string
  company_id?: string
}

/**
 * Bốn đường tính REALTIME theo khoảng ngày, mỗi tab ma trận một đường.
 *
 * Khác `/matrix` (snapshot cả năm, có cache 120 giây): mấy đường này quét thẳng
 * DB nên chỉ gọi khi người dùng thật sự chọn khoảng ngày.
 */
export const RANGE_ENDPOINTS: Record<string, string> = {
  supplier: '/api/reports/sup-range',
  item_group: '/api/reports/ig-range',
  nspt: '/api/reports/nspt-range',
  department: '/api/reports/dept-range',
  pyc_req: '/api/reports/request-range',
  ycks_req: '/api/reports/request-range',
}

function toQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  for (const [name, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.set(name, String(value))
  }
  const query = search.toString()
  return query ? `?${query}` : ''
}

export const purchaseReportApi = {
  /** Số liệu tab Tổng quan. `month` là bộ lọc PHỤ trong năm đang xem. */
  getProcurement: (params: ReportScope & { month?: string }) =>
    apiGet<ProcurementReport>(`/api/reports/procurement${toQuery({ ...params })}`),

  /**
   * Ma trận cả năm cho 5 chiều phân tích.
   *
   * `refresh` chỉ đặt khi người dùng bấm "Cập nhật": backend tính lại ĐỒNG BỘ
   * (chậm). Bỏ trống thì trả snapshot ngay và tự tính lại ngầm nếu quá hạn.
   */
  getMatrix: (params: ReportScope & { refresh?: 1 }) =>
    apiGet<ReportMatrix>(`/api/reports/matrix${toQuery({ ...params })}`),

  /** Ma trận phòng ban × tháng của YCMH (`pyc`) hoặc YCBG (`ycks`). */
  getRequestMatrix: (params: ReportScope & { kind: string }) =>
    apiGet<RequestMatrix>(`/api/reports/request-matrix${toQuery({ ...params })}`),

  /**
   * Bảng phẳng theo khoảng ngày. Thiếu `date_from`/`date_to` backend trả mảng
   * rỗng chứ không báo lỗi — chỗ gọi tự chặn trước bằng `enabled`.
   */
  getRange: (
    endpoint: string,
    params: { date_from: string; date_to: string; company_id?: string; kind?: string },
  ) => apiGet<MatrixRow[]>(`${endpoint}${toQuery({ ...params })}`),

  /** Chi tiết chi phí vận chuyển theo đơn hàng — phân trang phía server. */
  getShippingDetail: (
    params: ReportScope & {
      carrier?: string
      month?: string
      page: number
      page_size: number
    },
  ) => apiGet<ShippingDetailResult>(`/api/reports/shipping-detail${toQuery({ ...params })}`),

  /** Chi phí theo NGÀY trong một tháng — mở khi bấm vào cột biểu đồ. */
  getDaily: (params: { month: string; company_id?: string }) =>
    apiGet<DailyReport>(`/api/reports/daily${toQuery({ ...params })}`),

  /**
   * Xuất Excel. Luôn theo MỘT năm cụ thể: workbook có sẵn cột 12 tháng nên
   * "Tất cả các năm" không có chỗ đổ số — chỗ gọi phải quy về năm hiện tại.
   */
  exportExcel: (sheet: string, params: { year: string; company_id?: string }) =>
    downloadFile(
      `/api/reports/export${toQuery({ sheet, ...params })}`,
      `bao-cao-mua-hang-${sheet}-${params.year}.xlsx`,
    ),
}
