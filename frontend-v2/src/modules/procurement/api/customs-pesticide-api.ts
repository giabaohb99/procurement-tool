// Mục «Thuốc BVTV» của Tra cứu thị trường — `/api/customs/pesticides` (khóa `customs_price`).
import { apiDelete, apiGet, apiPatch, apiPost, httpClient } from '@/core/api'
import { downloadFile } from '@/core/api/download-file'
import type { SuccessEnvelope } from '@/core/api/response-envelope'

import { readBlobErrorMessage } from './customs-api'
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

/**
 * Nạp tệp danh mục (cần `customs_pesticide.write`) — tệp toàn bộ/bản cào gốc THAY cả danh mục
 * (giữ thuốc tự thêm); tệp xuất «Trang hiện tại» chỉ CẬP NHẬT đúng các thuốc có trong tệp, backend
 * tự nhận ra qua sheet ẩn (`result.mode`: `replace` | `merge`). Trả kèm `message` của phong bì —
 * câu đó đã đúng theo từng `mode`, hộp thoại hiện NGUYÊN câu này, không tự ghép lại (xem
 * `customs-pesticide-import-dialog.tsx`). Dùng `httpClient` trực tiếp vì `apiPost` bóc bỏ
 * `message` trong phong bì.
 */
export async function importCustomsPesticides(
  file: File,
): Promise<{ result: CustomsPesticideImportResult; message?: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await httpClient.post<SuccessEnvelope<CustomsPesticideImportResult>>(
    `${BASE}/import`,
    form,
  )
  return { result: res.data.data, message: res.data.message }
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

/**
 * Xuất Excel danh mục thuốc BVTV (cần `customs_price.export` — khác quyền SỬA danh mục
 * `customs_pesticide`). `scope=page` kèm đúng bộ lọc + trang màn đang xem; `scope=all` không
 * kèm bộ lọc, xuất cả danh mục. Tải bằng `responseType: 'blob'` nên lỗi (422 vượt trần, 429
 * đang có lượt xuất khác) cũng về dạng blob — đọc lại thành JSON mới ra đúng câu của backend.
 *
 * Tên tệp THẬT lấy từ `Content-Disposition` của backend (có ngày giờ xuất, xem
 * `pesticide_export_service.export_to_tempfile`) — hai tên dưới đây chỉ là tên DỰ PHÒNG khi vì
 * lý do gì đó header không có (xem `downloadFile`), nên vẫn phải khác nhau theo `scope` để không
 * đè lẫn tên tệp của nhau trong thư mục Tải xuống.
 */
export async function exportCustomsPesticides(
  params: Record<string, string>,
): Promise<void> {
  const fallbackName =
    params.scope === 'all' ? 'thuoc-bvtv-toan-bo.xlsx' : `thuoc-bvtv-trang-${params.page ?? ''}.xlsx`
  try {
    await downloadFile(`${BASE}/export`, fallbackName, params)
  } catch (error) {
    throw new Error(await readBlobErrorMessage(error), { cause: error })
  }
}
