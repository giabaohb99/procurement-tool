import '@testing-library/jest-dom/vitest'

import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// Không bật `globals: true` (để `describe/it/expect` phải import rõ ràng), nên
// bản dọn dẹp tự động của Testing Library không tự gắn — gắn tay ở đây. Thiếu
// dòng này thì DOM của test trước còn nguyên, `getByRole` bắt trúng phần tử cũ.
afterEach(cleanup)

// jsdom KHÔNG cài đặt Pointer Events API và `scrollIntoView`, mà mọi primitive
// Radix có lớp phủ (Select, Dropdown, Popover…) đều gọi tới chúng ngay lúc mở.
// Thiếu mấy dòng này thì test nào bấm vào một ô chọn cũng chết bằng
// `target.hasPointerCapture is not a function` — lỗi của môi trường chạy test,
// không phải của component đang kiểm.
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = vi.fn(() => false)
  Element.prototype.setPointerCapture = vi.fn()
  Element.prototype.releasePointerCapture = vi.fn()
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = vi.fn()
}
