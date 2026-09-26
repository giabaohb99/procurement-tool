// bao-CR-470 — gọi API phân hệ Tra cứu giá hải quan (`/api/customs/...`).
//
// Mọi cửa đọc dùng CHUNG một bộ lọc (`line_filters` ở backend) — nên tham số gửi đi
// luôn dựng từ `buildCustomsParams`. Quyền: `customs_price` (read · write = nạp tệp ·
// delete = hoàn tác · export = Excel).
import { apiGet, apiPost, extractErrorMessage, httpClient } from '@/core/api'
import { downloadFile } from '@/core/api/download-file'
import type { SuccessEnvelope } from '@/core/api/response-envelope'

import type {
  CustomsBatchLogList,
  CustomsCompare,
  CustomsCoverage,
  CustomsImportBatch,
  CustomsImportBatchList,
  CustomsImporters,
  CustomsLine,
  CustomsLineList,
  CustomsOptions,
  CustomsRegulationHit,
  CustomsRegulationLookup,
  CustomsStats,
  CustomsTariffRow,
} from '../types/customs'

type Params = Record<string, unknown>

const BASE = '/api/customs'

export function fetchCustomsCoverage() {
  return apiGet<CustomsCoverage>(`${BASE}/coverage`)
}

export function fetchCustomsOptions() {
  return apiGet<CustomsOptions>(`${BASE}/options`)
}

export function fetchCustomsLines(params: Params) {
  return apiGet<CustomsLineList>(`${BASE}/lines`, { params })
}

export function fetchCustomsLine(id: number) {
  return apiGet<CustomsLine>(`${BASE}/lines/${id}`)
}

export function fetchCustomsStats(params: Params) {
  return apiGet<CustomsStats>(`${BASE}/stats`, { params })
}

export function fetchCustomsCompare(params: Params) {
  return apiGet<CustomsCompare>(`${BASE}/compare`, { params })
}

export function fetchCustomsImporters(params: Params) {
  return apiGet<CustomsImporters>(`${BASE}/importers`, { params })
}

export function fetchCustomsAlerts(params: Params) {
  return apiGet<CustomsRegulationHit[]>(`${BASE}/alerts`, { params })
}

export function lookupCustomsRegulations(q: string) {
  return apiGet<CustomsRegulationLookup>(`${BASE}/regulations/lookup`, { params: { q } })
}

export function lookupCustomsTariff(hsCode: string) {
  return apiGet<CustomsTariffRow[]>(`${BASE}/tariff`, { params: { hs_code: hsCode } })
}

/** Tải lên một hoặc nhiều tệp GTT02 → mỗi tệp một lô CHẠY THỬ. */
export function uploadCustomsFiles(files: File[]) {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  return apiPost<CustomsImportBatch[]>(`${BASE}/imports`, form)
}

/** Ghi thật từ một lô chạy thử đã xong — trả về lô GHI THẬT mới. */
export function commitCustomsBatch(id: number) {
  return apiPost<CustomsImportBatch>(`${BASE}/imports/${id}/commit`)
}

/** Hoàn tác một lô ghi thật. Trả kèm câu của backend để báo đúng số dòng đã xóa. */
export async function revertCustomsBatch(id: number) {
  const res = await httpClient.post<SuccessEnvelope<CustomsImportBatch>>(
    `${BASE}/imports/${id}/revert`,
  )
  return { batch: res.data.data, message: res.data.message }
}

export function fetchCustomsBatches(params: Params) {
  return apiGet<CustomsImportBatchList>(`${BASE}/imports`, { params })
}

export function fetchCustomsBatch(id: number) {
  return apiGet<CustomsImportBatch>(`${BASE}/imports/${id}`)
}

export function fetchCustomsBatchLogs(id: number, params: Params) {
  return apiGet<CustomsBatchLogList>(`${BASE}/imports/${id}/logs`, { params })
}

/** bao-CR-493 — tải lại tệp GTT02 gốc của một lô nạp (chỉ lô nạp qua màn hình mới có tệp). */
export async function downloadCustomsBatchFile(id: number, filename: string) {
  try {
    await downloadFile(`${BASE}/imports/${id}/file`, filename || `gtt02-${id}.xls`)
  } catch (error) {
    throw new Error(extractErrorMessage(error), { cause: error })
  }
}

/**
 * Xuất Excel đúng các dòng đang lọc. Tải bằng `responseType: 'blob'` nên câu lỗi của
 * backend (vd "Kết quả quá 50.000 dòng") cũng về dạng blob — phải đọc lại thành JSON
 * thì mới báo được đúng lý do, không thì người dùng chỉ thấy "có lỗi xảy ra".
 */
export async function exportCustomsLines(params: Params) {
  try {
    await downloadFile(`${BASE}/lines/export`, 'tra-cuu-gia-hai-quan.xlsx', params)
  } catch (error) {
    throw new Error(await readBlobErrorMessage(error), { cause: error })
  }
}

async function readBlobErrorMessage(error: unknown): Promise<string> {
  const data = (error as { response?: { data?: unknown } })?.response?.data
  if (data instanceof Blob) {
    try {
      const parsed: unknown = JSON.parse(await data.text())
      return extractErrorMessage({ response: { data: parsed } })
    } catch {
      return 'Không xuất được tệp Excel'
    }
  }
  return extractErrorMessage(error)
}
