import '@testing-library/jest-dom/vitest'

import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Không bật `globals: true` (để `describe/it/expect` phải import rõ ràng), nên
// bản dọn dẹp tự động của Testing Library không tự gắn — gắn tay ở đây. Thiếu
// dòng này thì DOM của test trước còn nguyên, `getByRole` bắt trúng phần tử cũ.
afterEach(cleanup)
