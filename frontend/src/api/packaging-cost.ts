/**
 * duoc-CR-784 — gọi API cụm Giá bao bì (bản v1). Chỉ là lớp mỏng quanh `api` (axios): bóc phong bì
 * `{success, message, data}`, tải tệp Excel, và đọc câu lỗi nằm trong blob khi xuất tệp thất bại.
 *
 * Tham số dạng mảng đi theo `paramsSerializer: { indexes: null }` của `api/client.ts` (`supplier=a&supplier=b`),
 * đúng cách `Query(list[str])` của backend đọc.
 */
import { api } from './client'
import type {
  PackagingBatchPurgePreview, PackagingBatchPurgeResult, PackagingCodeOption, PackagingFgOption, PackagingHistoryParams, PackagingHistoryResult,
  PackagingImpactRequest, PackagingImpactResult, PackagingLastPricesParams, PackagingLastPricesResult,
  PackagingMaterialHistoryParams, PackagingMaterialPriceListParams, PackagingOverviewParams, PackagingOverviewResult,
  PackagingPriceListParams, PackagingPriceRow,
} from './packaging-cost-types'

const BASE = '/api/packaging-cost'
export const PACKAGING_QUOTE_API = '/api/product-price-quotes'
export const PACKAGING_BOM_API = '/api/packaging-boms'
/** `ImportModule.PACKAGING_BOM` ở `backend/app/modules/import_tool/model.py`. */
export const IMPORT_MODULE_PACKAGING_BOM = 4
/** `ImportModule.PACKAGING_QUOTE` — Báo giá VTBB. */
export const IMPORT_MODULE_PACKAGING_QUOTE = 5
/** `ImportModule.PACKAGING_MISA` — Sổ chi tiết mua hàng Misa (giá NVL). */
export const IMPORT_MODULE_PACKAGING_MISA = 6
/** Ba kiểu nhập của cụm giá bao bì: có nút "Ghi thật" ở trang lô, KHÔNG hỗ trợ hoàn tác. */
export const PACKAGING_IMPORT_MODULES: readonly number[] = [
  IMPORT_MODULE_PACKAGING_BOM, IMPORT_MODULE_PACKAGING_QUOTE, IMPORT_MODULE_PACKAGING_MISA,
]

/**
 * bao-CR-792 — khóa phân quyền của cụm: MỖI MÀN MỘT KHÓA (khóa chung cũ của duoc-CR-784 đã nghỉ hẳn ở backend).
 * Endpoint của màn nào backend gác bằng khóa của màn đó; ô chọn mã / ô chọn sản phẩm dùng chung mở khi có `read` trên
 * bất kỳ khóa nào. Báo giá VTBB (`/product-price-quotes`) đi chung khóa với Bảng giá VTBB.
 * bao-CR-800: Bảng giá nguyên liệu có khóa RIÊNG `packaging_material_price` — các đường VTBB (kể cả ô chọn mã dùng chung)
 * không mở cho người chỉ có khóa này, và ngược lại; màn nguyên liệu chỉ gọi các đường `material-*`.
 */
export const PACKAGING_ENTITY = {
  impact: 'packaging_impact',
  products: 'packaging_product_summary',
  priceList: 'packaging_price_list',
  materialPrices: 'packaging_material_price',
  lastPrices: 'packaging_last_price',
  history: 'packaging_history',
  boms: 'packaging_bom',
} as const
export type PackagingEntity = typeof PACKAGING_ENTITY[keyof typeof PACKAGING_ENTITY]

/** bao-CR-792 — khóa quyền theo kiểu nhập: nút nhập Excel và nút xóa dữ liệu theo lô hỏi đúng khóa của màn nhận dữ liệu. */
export const PACKAGING_IMPORT_ENTITY: Record<number, PackagingEntity> = {
  [IMPORT_MODULE_PACKAGING_BOM]: PACKAGING_ENTITY.boms,
  [IMPORT_MODULE_PACKAGING_QUOTE]: PACKAGING_ENTITY.priceList,
  [IMPORT_MODULE_PACKAGING_MISA]: PACKAGING_ENTITY.history,
}

/** Xem trước xóa dữ liệu theo lô nhập (định mức / báo giá / sổ Misa). */
export async function fetchBatchPurgePreview(batchId: number | string): Promise<PackagingBatchPurgePreview> {
  const r = await api.get(`/api/imports/${batchId}/purge-preview`)
  return r.data.data
}

/** Xóa dữ liệu của lô; `includeEdited` = xóa luôn dòng đã sửa tay sau khi nhập. */
export async function purgeBatchData(batchId: number | string, includeEdited: boolean): Promise<PackagingBatchPurgeResult> {
  const r = await api.post(`/api/imports/${batchId}/purge`, { include_edited: includeEdited })
  return r.data.data
}

/**
 * Danh sách mã cho ô chọn nhiều — nạp một lần, lọc ở trình duyệt. `bom` (mặc định, màn Tác động) = mã đang dùng trong định
 * mức (~1.500); `all` = mọi mã có trong sổ giá (Giá mua gần nhất, Bảng giá, Lịch sử mua hàng). Mỗi mã kèm tên NCC từng bán.
 */
export async function fetchCodeOptions(scope: 'bom' | 'all' = 'bom'): Promise<PackagingCodeOption[]> {
  const r = await api.get(`${BASE}/code-options`, scope === 'all' ? { params: { scope } } : undefined)
  const d = r.data.data
  return Array.isArray(d) ? d : (d?.items ?? [])
}

/** Sản phẩm (mã HH) có định mức bao bì — ô chọn của chế độ "Theo mã sản phẩm". */
export async function fetchFgOptions(): Promise<PackagingFgOption[]> {
  const r = await api.get(`${BASE}/fg-options`)
  return r.data.data?.items ?? []
}

/** Tính tác động — đọc thuần (không ghi nhật ký) dù là POST. */
export async function fetchImpact(body: PackagingImpactRequest): Promise<PackagingImpactResult> {
  const r = await api.post(`${BASE}/impact`, body, { _silent: true } as any)
  return r.data.data
}

export async function fetchPriceList(params: PackagingPriceListParams): Promise<{ items: PackagingPriceRow[]; total: number }> {
  const r = await api.get(`${BASE}/price-list`, { params })
  return r.data.data
}

/**
 * bao-CR-800 — Bảng giá nguyên liệu: dòng cùng khuôn Bảng giá VTBB nhưng chỉ mã thuộc nhóm nguyên liệu đã có giá;
 * không có tham số `scope`. Quyền `packaging_material_price.read`.
 */
export async function fetchMaterialPriceList(params: PackagingMaterialPriceListParams): Promise<{ items: PackagingPriceRow[]; total: number }> {
  const r = await api.get(`${BASE}/material-price-list`, { params })
  return r.data.data
}

/** bao-CR-800 — mã cho ô chọn của màn Bảng giá nguyên liệu (mọi mã nguyên liệu đã có giá, kèm tên NCC từng bán). */
export async function fetchMaterialCodeOptions(): Promise<PackagingCodeOption[]> {
  const r = await api.get(`${BASE}/material-code-options`)
  return r.data.data?.items ?? []
}

export async function fetchLastPrices(params: PackagingLastPricesParams): Promise<PackagingLastPricesResult> {
  const r = await api.get(`${BASE}/last-prices`, { params })
  return r.data.data
}

/** Tổng hợp theo sản phẩm: mọi sản phẩm có định mức, chi phí / chai cũ so với mới + xu hướng; lọc / xếp / trang tại máy chủ. */
export async function fetchProductOverview(params: PackagingOverviewParams): Promise<PackagingOverviewResult> {
  const r = await api.get(`${BASE}/product-overview`, { params })
  return r.data.data
}

export async function fetchHistory(params: PackagingHistoryParams): Promise<PackagingHistoryResult> {
  const r = await api.get(`${BASE}/history`, { params })
  return r.data.data
}

/**
 * bao-CR-801 — lịch sử mua hàng của NGUYÊN LIỆU (mở từ mã ở màn Bảng giá nguyên liệu): cùng khuôn kết quả với `fetchHistory`
 * chế độ mã (`series` có khi chọn đúng một mã, `series_by_code` luôn null). Quyền `packaging_material_price.read`.
 */
export async function fetchMaterialHistory(params: PackagingMaterialHistoryParams): Promise<PackagingHistoryResult> {
  const r = await api.get(`${BASE}/material-history`, { params })
  return r.data.data
}

export interface QuotePayload {
  product_code: string
  supplier_code: string
  price: number
  vat: number
  valid_from: string
  note: string
}

export async function createQuote(payload: QuotePayload): Promise<void> {
  await api.post(PACKAGING_QUOTE_API, payload)
}

// ── Tải tệp Excel ───────────────────────────────────────────────────────────────

/** Lỗi trả về dạng blob (do `responseType: 'blob'`) → đọc ra câu thông báo của backend. */
export async function readBlobError(e: any, fallback = 'Không xuất được tệp Excel'): Promise<string> {
  try {
    const body = e?.response?.data
    const text = body instanceof Blob ? await body.text() : ''
    return JSON.parse(text)?.error?.message || fallback
  } catch {
    return fallback
  }
}

function saveBlob(response: { data: Blob; headers: any }, fallbackName: string) {
  const cd = String(response.headers['content-disposition'] || '')
  const name = /filename="?([^";]+)"?/.exec(cd)?.[1] || fallbackName
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', name)
  document.body.appendChild(link)
  link.click()
  link.parentNode?.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/** Các đường có `/export` bằng GET của cụm. */
export type PackagingExportPath = 'price-list' | 'material-price-list' | 'last-prices' | 'history' | 'material-history' | 'product-overview'

/** Xuất Excel bằng GET: cùng bộ lọc + thứ tự đang xem, không kèm `page`. Ném `Error` mang câu thông báo cho nơi gọi. */
export async function downloadExport(
  path: PackagingExportPath, params: object, fallbackName: string,
) {
  try {
    const r = await api.get(`${BASE}/${path}/export`, { params, responseType: 'blob' })
    saveBlob(r, fallbackName)
  } catch (e) {
    throw new Error(await readBlobError(e))
  }
}

/** Xuất màn Tác động (2 sheet) — là POST (thân giống `/impact`). */
export async function exportImpact(body: PackagingImpactRequest) {
  try {
    const r = await api.post(`${BASE}/impact/export`, body, { responseType: 'blob', _silent: true } as any)
    saveBlob(r, 'tac-dong-gia-bao-bi.xlsx')
  } catch (e) {
    throw new Error(await readBlobError(e))
  }
}

/** Tải tệp mẫu Excel của một kiểu nhập (`import.read`). Ném `Error` mang câu thông báo cho nơi gọi. */
export async function downloadImportTemplate(module: number) {
  try {
    const r = await api.get('/api/imports/template', { params: { module }, responseType: 'blob', _silent: true } as any)
    saveBlob(r, `mau-nhap-${module}.xlsx`)
  } catch (e) {
    throw new Error(await readBlobError(e, 'Không tải được tệp mẫu'))
  }
}
