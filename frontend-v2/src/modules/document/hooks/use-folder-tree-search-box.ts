import { useState } from 'react'

/**
 * Ô lọc GỌN kiểu VS Code Explorer — ẩn mặc định, nút "Tìm" ở tiêu đề bật/tắt
 * (yêu cầu 23/09/2026, thay ô tìm to + công tắc to luôn hiện). Đóng (nút "Tìm"
 * bấm lại, hoặc Esc trong ô) thì XÓA từ khóa — không để trạng thái lọc "vô
 * hình" tồn tại sau khi ô đã biến mất.
 *
 * ⚠️ CỐ Ý không tự giữ `inputRef`/hiệu ứng focus ở đây — `react-hooks/refs`
 * (ESLint) cảnh báo "Cannot access refs during render" khi một ref bị gói vào
 * object trả về từ hook rồi đọc lại ở nơi gọi. Nơi dùng (`folder-tree-panel.tsx`)
 * tự giữ ref CỦA CHÍNH NÓ và tự đưa tiêu điểm vào ô khi `searchOpen` bật.
 */
export function useFolderTreeSearchBox() {
  const [keyword, setKeyword] = useState('')
  const [searchOpen, setSearchOpen] = useState(false)

  function close() {
    setSearchOpen(false)
    setKeyword('')
  }

  function toggle() {
    if (searchOpen) close()
    else setSearchOpen(true)
  }

  return { keyword, setKeyword, searchOpen, close, toggle }
}
