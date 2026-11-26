import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'

/**
 * Ghi chuỗi truy vấn của màn hình lên URL (duoc-CR-784): `search` là bộ tham số màn đang sở hữu (từ `*ScreenToSearch`),
 * `ownedKeys` là mọi khóa nó được phép đụng — khóa của màn bị xóa rồi ghi lại, tham số lạ (của nơi khác) giữ nguyên.
 *
 * - Dùng `replace`: nút Quay lại vẫn về trang trước, không phải từng bước chọn / gõ.
 * - Trễ `delayMs` sau lần đổi cuối nên gõ giá giả định / từ khóa không ghi URL từng phím.
 * - Chỉ điều hướng khi URL thật sự đổi nên không lặp; đọc `window.location.search` lúc chạy (không phụ thuộc `searchParams`)
 *   để việc đổi URL ở nơi khác không kích hoạt ghi đè ngược.
 * - `enabled=false` (chưa nạp xong trạng thái ban đầu) thì không ghi.
 */
export function useSearchSyncToUrl(search: string, ownedKeys: readonly string[], delayMs = 300, enabled = true) {
  const [, setSearchParams] = useSearchParams()
  useEffect(() => {
    if (!enabled) return
    const timer = window.setTimeout(() => {
      const next = new URLSearchParams(window.location.search)
      ownedKeys.forEach((k) => next.delete(k))
      new URLSearchParams(search).forEach((v, k) => next.append(k, v))
      if (next.toString() !== new URLSearchParams(window.location.search).toString()) setSearchParams(next, { replace: true })
    }, delayMs)
    return () => window.clearTimeout(timer)
  }, [search, ownedKeys, delayMs, enabled, setSearchParams])
}
