import { matchesVietnamese } from '@/shared/utils/vn-text'
import type { DossierListResult } from '../types/dossier'
import { MOCK_DOSSIERS } from './dossier-mock-data'
import { fakeLatency } from './mock-latency'

/** Tham số của màn danh sách — giữ đúng tên param sẽ gửi lên backend sau này. */
export interface DossierListParams {
  keyword: string
  /** Mã trạng thái dạng chuỗi (`'2'`), `''` = tất cả — đúng kiểu của query param. */
  status: string
  department: string
  page: number
  pageSize: number
}

/**
 * Lấy một trang hồ sơ.
 *
 * ⚠️ **Bản MẪU**: lọc và cắt trang chạy ngay trong trình duyệt trên
 * `MOCK_DOSSIERS`. Khi có backend, thay ruột hàm này bằng
 * `apiGet<DossierListResult>('/api/dossiers', { params })` — chữ ký giữ nguyên
 * nên trang và hook không phải sửa gì.
 */
export async function fetchDossiers(params: DossierListParams): Promise<DossierListResult> {
  await fakeLatency()

  const filtered = MOCK_DOSSIERS.filter((row) => {
    if (params.status && String(row.status) !== params.status) return false
    if (params.department && row.department_name !== params.department) return false
    //  Tìm bỏ dấu trên cả bốn ô người dùng hay gõ — gõ "hop dong" phải ra "Hợp đồng".
    return matchesVietnamese(
      [row.code, row.name, row.type_name, row.owner_name],
      params.keyword,
    )
  })

  const start = (params.page - 1) * params.pageSize
  return { items: filtered.slice(start, start + params.pageSize), total: filtered.length }
}

/**
 * Danh sách bộ phận có trong dữ liệu — đổ cho ô chọn *Bộ phận*.
 * Backend thật sẽ lấy từ danh mục phòng ban, không suy ra từ dữ liệu hồ sơ.
 */
export function listDossierDepartments(): string[] {
  return [...new Set(MOCK_DOSSIERS.map((row) => row.department_name))].sort((a, b) =>
    a.localeCompare(b, 'vi'),
  )
}
