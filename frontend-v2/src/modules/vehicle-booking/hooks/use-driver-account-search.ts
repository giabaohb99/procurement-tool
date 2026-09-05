import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import type { UserAccount } from '@/modules/hr/types/user-account'
import type { PaginatedResult } from '@/shared/types/api'

/** Số chữ số tối thiểu để coi là "đã nhập đủ số điện thoại" mới đi tìm. */
export const MIN_PHONE_DIGITS = 9

/** Đếm CHỮ SỐ trong chuỗi (bỏ khoảng trắng, dấu chấm…). */
export function phoneDigits(value: string): number {
  return (value.match(/\d/g) ?? []).length
}

/**
 * Tìm TÀI KHOẢN NHÂN SỰ theo số điện thoại, để chọn làm tài xế nội bộ.
 *
 * Chỉ gọi API khi đã nhập ĐỦ số điện thoại (`MIN_PHONE_DIGITS` chữ số) — theo yêu
 * cầu: kết quả chỉ hiện khi nhập đủ SĐT, tránh xổ cả danh bạ khi mới gõ vài số.
 * Backend `/api/users` đã tìm cả theo SĐT và trả kèm avatar / tên / email liên hệ.
 */
export function useDriverAccountSearch(phone: string) {
  const digits = phoneDigits(phone)
  const enabled = digits >= MIN_PHONE_DIGITS
  const query = useQuery({
    queryKey: ['vehicle-booking', 'driver-account-search', phone.trim()],
    queryFn: () =>
      apiGet<PaginatedResult<UserAccount>>('/api/users', {
        params: { search: phone.trim(), page_size: 8 },
      }),
    enabled,
    staleTime: 30_000,
  })
  return { ...query, enabled, digits }
}
