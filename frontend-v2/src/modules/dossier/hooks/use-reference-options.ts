import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'
import {
  REFERENCE_PAGE_SIZE,
  referenceSource,
} from '../types/dossier-reference-sources'

interface Row {
  id: number
  [key: string]: unknown
}

export interface ReferenceOption {
  value: string
  label: string
}

const referenceKeys = {
  list: (source: string, query: string) => ['dossier', 'reference', source, query] as const,
  one: (source: string, id: number) => ['dossier', 'reference', source, 'one', id] as const,
}

/**
 * Danh sách mục cho ô «Chọn từ danh mục», có TRA CỨU phía server.
 *
 * ⚠️ Tra phía server chứ không nạp hết rồi lọc trong trình duyệt, và không phải
 * vì tối ưu: danh mục Sản phẩm có **6803 dòng** còn trần phân trang của backend
 * là 5000 — nạp hết là chuyện không làm được. Lọc client thì sản phẩm thứ 5001
 * trở đi biến mất khỏi ô chọn và **không gì báo**.
 *
 * Danh mục nhỏ (Phòng ban 18, Pháp nhân 14) khai `searchParam: null` — lượt gọi
 * đầu đã lấy hết, `SearchSelect` lọc tại chỗ, gõ không bắn thêm request nào.
 *
 * `keepPreviousData` để danh sách không chớp về rỗng giữa mỗi phím gõ.
 */
export function useReferenceOptions(source: string, query: string) {
  const config = referenceSource(source)

  return useQuery({
    queryKey: referenceKeys.list(source, config?.searchParam ? query : ''),
    queryFn: async (): Promise<ReferenceOption[]> => {
      if (!config) return []
      const params: Record<string, unknown> = { page_size: REFERENCE_PAGE_SIZE }
      if (config.searchParam && query) params[config.searchParam] = query

      const res = await apiGet<PaginatedResult<Row>>(config.url, { params })
      return res.items.map((row) => ({
        value: String(row.id),
        label: String(row[config.labelKey] ?? row.id),
      }))
    },
    enabled: Boolean(config),
    placeholderData: keepPreviousData,
    staleTime: 60 * 1000,
  })
}

/**
 * Nhãn của MỘT mục đã lưu — tra riêng theo id.
 *
 * ⚠️ Đây là cái giá của việc **lưu ID**: dòng đang chọn có thể không nằm trong
 * trang đầu của danh sách (sản phẩm thứ 4000 chẳng hạn), nên mở hồ sơ ra là ô
 * chọn không khớp mục nào và hiện **trống trơn** — nhìn y hệt ô chưa ai nhập.
 * Phải đi hỏi đích danh một lượt nữa.
 *
 * ⚠️ `retry: false`: id trỏ vào dòng đã xóa thì trả 404, và thử lại ba lần chỉ
 * làm người dùng chờ lâu hơn để nhận cùng một kết quả.
 */
export function useReferenceLabel(source: string, id: number) {
  const config = referenceSource(source)

  return useQuery({
    queryKey: referenceKeys.one(source, id),
    queryFn: async (): Promise<string> => {
      if (!config) return ''
      const row = await apiGet<Row>(`${config.url}/${id}`)
      return String(row[config.labelKey] ?? '')
    },
    enabled: Boolean(config) && id > 0,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
}
