import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'

import { useAuthStore } from '@/core/auth/auth-store'

function readSaved(storageKey: string): string | null {
  try {
    const saved = sessionStorage.getItem(storageKey)
    //  `?` trơn là chuỗi lọc rỗng — khôi phục nó thì chỉ đổi hướng vô ích.
    return saved && saved !== '?' ? saved : null
  } catch {
    return null
  }
}

function writeSaved(storageKey: string, search: string) {
  try {
    if (search && search !== '?') sessionStorage.setItem(storageKey, search)
    else sessionStorage.removeItem(storageKey)
  } catch {
    //  Trình duyệt chặn bộ nhớ (chế độ riêng tư cũ, hết chỗ): mất tính năng nhớ, màn vẫn chạy.
  }
}

/**
 * Nhớ bộ lọc của một màn danh sách theo TAB trình duyệt (kh-NT2-2): mở chi tiết rồi
 * quay lại bằng menu thì bảng vẫn đúng bộ lọc lúc nãy.
 *
 * Trả chuỗi `?...` cần khôi phục — trang gọi `<Navigate replace to={{ search }} />`
 * khi khác `null`, và phải gọi Ở NGOÀI `FilterProvider`: provider chỉ đọc URL MỘT lần
 * lúc dựng, dựng trước khi đổi hướng là bộ lọc nâng cao mất.
 *
 * Luật:
 * - **URL thắng.** Link có sẵn tham số (thông báo, đồng nghiệp gửi) mở đúng link đó.
 * - **Khôi phục một lần.** Sau đó URL trống là do người dùng xóa lọc, và lần xóa đó
 *   được ghi đè lên bản nhớ — lần mở sau ra màn sạch.
 * - **Khóa theo màn và theo tài khoản.** Đổi tài khoản trên cùng tab không mang lọc
 *   của người trước. Chưa đăng nhập thì không nhớ gì.
 *
 * `sessionStorage` chứ không `localStorage`: bộ lọc là ngữ cảnh của một lượt làm
 * việc; mở tab mới hôm sau mà bảng tự lọc sẵn thì người ta tưởng mất dữ liệu.
 */
export function useRememberedListSearch(screenKey: string): string | null {
  const location = useLocation()
  const userId = useAuthStore((state) => state.user?.id)
  const storageKey = userId ? `list-search:${userId}:${screenKey}` : null

  const [pending, setPending] = useState<string | null>(() =>
    storageKey && !location.search ? readSaved(storageKey) : null,
  )

  //  Đã sang URL có tham số (đổi hướng xong, hoặc người dùng tự bấm) thì thôi khôi
  //  phục. Đặt state ngay lúc dựng là cách React khuyên cho trạng thái suy ra — dùng
  //  effect thì có một lượt dựng thừa với cờ cũ.
  if (pending !== null && location.search) setPending(null)

  useEffect(() => {
    if (pending !== null || !storageKey) return
    writeSaved(storageKey, location.search)
  }, [pending, storageKey, location.search])

  return pending !== null && !location.search ? pending : null
}
