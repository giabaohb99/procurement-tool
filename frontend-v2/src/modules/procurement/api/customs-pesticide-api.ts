// Mục «Thuốc BVTV» của Tra cứu thị trường — `/api/customs/pesticides` (khóa `customs_price`).
import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'

import type {
  CustomsPesticideDetail,
  CustomsPesticideImportResult,
  CustomsPesticideInput,
  CustomsPesticideList,
  CustomsPesticideOptions,
  CustomsPesticideRelated,
} from '../types/customs-pesticide'

const BASE = '/api/customs/pesticides'

export function fetchCustomsPesticides(params: Record<string, unknown>) {
  return apiGet<CustomsPesticideList>(BASE, { params })
}

export function fetchCustomsPesticideOptions() {
  return apiGet<CustomsPesticideOptions>(`${BASE}/options`)
}

export function fetchCustomsPesticide(id: number) {
  return apiGet<CustomsPesticideDetail>(`${BASE}/${id}`)
}

/** «Sản phẩm khác cùng công ty» + «Thuốc cùng hoạt chất» — `limit` mỗi khối (mặc định 10, trần 300). */
export function fetchCustomsPesticideRelated(id: number, limit: number) {
  return apiGet<CustomsPesticideRelated>(`${BASE}/${id}/related`, { params: { limit } })
}

/** Thay các thuốc lấy từ nguồn bằng tệp `thuoc-bvtv.json` / `.xlsx`, giữ thuốc tự thêm (cần `customs_pesticide.write`). */
export function importCustomsPesticides(file: File) {
  const form = new FormData()
  form.append('file', file)
  return apiPost<CustomsPesticideImportResult>(`${BASE}/import`, form)
}

/** Thêm một thuốc (cần `customs_pesticide.create`) — thuốc thêm tay được giữ qua các lần nạp. */
export function createCustomsPesticide(body: CustomsPesticideInput) {
  return apiPost<CustomsPesticideDetail>(BASE, body)
}

/** Sửa một thuốc (cần `customs_pesticide.write`) — gửi ĐỦ cả bản ghi lẫn phạm vi sử dụng. */
export function updateCustomsPesticide(id: number, body: CustomsPesticideInput) {
  return apiPatch<CustomsPesticideDetail>(`${BASE}/${id}`, body)
}

/** Xóa một thuốc (cần `customs_pesticide.delete`). */
export function deleteCustomsPesticide(id: number) {
  return apiDelete<null>(`${BASE}/${id}`)
}
