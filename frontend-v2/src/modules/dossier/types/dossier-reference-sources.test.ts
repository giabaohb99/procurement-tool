import { describe, expect, it } from 'vitest'

import {
  REFERENCE_PAGE_SIZE,
  REFERENCE_SOURCES,
  referenceSource,
} from './dossier-reference-sources'

/**
 * Bảng danh mục cho ô «Chọn từ danh mục».
 *
 * Bài kiểm chéo với backend nằm ở phía kia (`test/backend/test_ho_so_truong_rieng.py`
 * đọc thẳng tệp này) vì chỉ bên đó cầm được cả hai danh sách. Ở đây kiểm những
 * thứ chỉ frontend biết: hình dạng từng dòng và cách tra khóa.
 */

describe('REFERENCE_SOURCES — hình dạng từng dòng', () => {
  const entries = Object.entries(REFERENCE_SOURCES)

  it('khóa là slug thường, đúng thứ gõ được xuống backend', () => {
    //  Khóa này đi thẳng vào `custom_fields.source` rồi sang backend so khớp.
    //  Chữ hoa hay gạch ngang là lệch khỏi `REFERENCE_MODELS` bên Python.
    for (const [key] of entries) expect(key).toMatch(/^[a-z][a-z0-9_]*$/)
  })

  it('mỗi dòng có đủ nhãn · url · cột nhãn', () => {
    for (const [key, src] of entries) {
      expect(src.label, key).toBeTruthy()
      expect(src.url, key).toMatch(/^\/api\//)
      expect(src.labelKey, key).toBeTruthy()
    }
  })

  it('nhãn KHÔNG trùng nhau', () => {
    //  Hai dòng cùng nhãn thì ô chọn «Danh mục» bày ra hai mục đọc y hệt nhau,
    //  và người dùng không có cách nào biết mình vừa chọn cái nào.
    const labels = entries.map(([, src]) => src.label)
    expect(new Set(labels).size).toBe(labels.length)
  })

  it('url KHÔNG trùng nhau', () => {
    const urls = entries.map(([, src]) => src.url)
    expect(new Set(urls).size).toBe(urls.length)
  })

  it('Sản phẩm PHẢI tra phía server', () => {
    //  ⚠️ Không phải chuyện tối ưu: danh mục có 6803 dòng (đo 17/09/2026) còn
    //  trần phân trang của backend là 5000 — nạp hết là chuyện không làm được.
    //  Đổi dòng này về `null` thì sản phẩm thứ 5001 trở đi biến mất khỏi ô chọn
    //  và KHÔNG GÌ BÁO: ô vẫn mở ra, vẫn có dòng, chỉ thiếu.
    expect(REFERENCE_SOURCES.product.searchParam).toBe('name')
  })

  it('Nhân sự lọc bằng `full_name`, không phải `name`', () => {
    //  ⚠️ `apply_filters` BỎ QUA trong im lặng tham số ngoài `filterable` —
    //  gõ tìm sẽ trả nguyên danh sách, không lỗi nào để lần ra. Đã thử tay.
    expect(REFERENCE_SOURCES.employee.searchParam).toBe('full_name')
  })

  it('trang nạp đủ lớn để danh mục nhỏ vào hết một lượt', () => {
    //  Phòng ban 18 · Pháp nhân 14 khai `searchParam: null`, tức lượt gọi đầu
    //  phải lấy HẾT. Hạ trần này xuống dưới số dòng thật là chúng mất mục mà
    //  không có đường tìm bù.
    expect(REFERENCE_PAGE_SIZE).toBeGreaterThanOrEqual(100)
  })
})

describe('referenceSource — tra khóa', () => {
  it('trả về đúng dòng với khóa có thật', () => {
    expect(referenceSource('employee')).toBe(REFERENCE_SOURCES.employee)
  })

  it('khóa lạ và chuỗi rỗng trả về undefined', () => {
    expect(referenceSource('users')).toBeUndefined()
    expect(referenceSource('')).toBeUndefined()
  })

  it('KHÔNG trả về thứ thừa kế từ Object.prototype', () => {
    //  ⚠️ LỖI ĐÃ TRÁNH: `REFERENCE_SOURCES['__proto__']` trả về `Object.prototype`
    //  — một vật thể **truthy** mà `label` là `undefined`. Nơi gọi kiểm
    //  `if (!config)` nên nó lọt qua, rồi `config.label.toLowerCase()` ném
    //  `TypeError` NGAY LÚC VẼ: cả biểu mẫu trắng xóa, không phải một ô báo lỗi.
    //  `constructor` và `toString` cùng đường.
    for (const key of ['__proto__', 'constructor', 'toString', 'hasOwnProperty']) {
      expect(referenceSource(key), key).toBeUndefined()
    }
  })
})
