import type { AxiosRequestConfig } from 'axios'

import { downloadFile, httpClient } from '@/core/api'

import type { HeadcountPlanImportResult } from '../types/headcount-plan'

/** Gốc API danh mục kế hoạch nhân sự (duoc-CR-689). Danh sách / thêm / sửa / xóa đi qua khung CRUD chung. */
export const HEADCOUNT_PLAN_API_PATH = '/api/headcount-plans'

/**
 * Xuất CSV theo ĐÚNG bộ lọc đang xem (năm / pháp nhân / phòng). Cột lương để trống khi người
 * xem thiếu `labor_contract.read` — backend lo, giao diện không cần biết.
 */
export function exportHeadcountPlansCsv(params: Record<string, string>) {
  return downloadFile(`${HEADCOUNT_PLAN_API_PATH}/export/csv`, 'ke-hoach-nhan-su.csv', params)
}

/**
 * Nhập CSV — có rồi thì cập nhật, chưa có thì tạo (theo năm × pháp nhân × phòng), NGUYÊN KHỐI:
 * một dòng lỗi là không ghi dòng nào. `httpClient` thẳng vì `multipart/form-data`; KHÔNG đặt tay
 * `Content-Type` — trình duyệt tự sinh `boundary`. `_silent`: lỗi tệp là DANH SÁCH nhiều dòng,
 * nút nhập tự bày hộp thoại liệt kê từng dòng thay cho toast một câu của `httpClient`.
 */
export async function importHeadcountPlansCsv(file: File): Promise<HeadcountPlanImportResult> {
  const body = new FormData()
  body.append('file', file)
  const res = await httpClient.post<{ data: HeadcountPlanImportResult }>(
    `${HEADCOUNT_PLAN_API_PATH}/import/csv`,
    body,
    { _silent: true } as AxiosRequestConfig,
  )
  return res.data.data
}
