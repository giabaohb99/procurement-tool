import { describe, expect, it } from 'vitest'

import { CONTRACT_TYPE_OPTIONS, contractTypeLabel } from './contract-type-options'

describe('contractTypeLabel', () => {
  it('dịch mã tiếng Anh lưu trong DB thành nhãn tiếng Việt', () => {
    expect(contractTypeLabel('purchase')).toBe('Hợp đồng mua bán')
    expect(contractTypeLabel('principle')).toBe('Hợp đồng nguyên tắc')
    expect(contractTypeLabel('other')).toBe('Khác')
  })

  it('giá trị lạ thì giữ nguyên chứ không nuốt mất dữ liệu', () => {
    // Trước CR-118 cột này là chữ tự do tiếng Việt (kể cả bản gõ sai "Hơp đồng
    // nguyên tắc"). Bản ghi nào lọt lưới migration mà trả rỗng thì người dùng
    // tưởng mất dữ liệu, rồi gõ đè lên.
    expect(contractTypeLabel('Mua bán')).toBe('Mua bán')
    expect(contractTypeLabel('Hơp đồng nguyên tắc')).toBe('Hơp đồng nguyên tắc')
  })

  it('rỗng thì trả chuỗi rỗng để nơi gọi tự chọn dấu gạch hay chữ "Chưa phân loại"', () => {
    expect(contractTypeLabel('')).toBe('')
    expect(contractTypeLabel(null)).toBe('')
    expect(contractTypeLabel(undefined)).toBe('')
  })
})

describe('CONTRACT_TYPE_OPTIONS', () => {
  it('khớp đúng bộ mã của backend `app/core/contract_types.py`', () => {
    // Lệch bộ này là ô lọc lọc ra 0 dòng mà không báo lỗi gì cả.
    expect(CONTRACT_TYPE_OPTIONS.map((o) => o.value)).toEqual([
      'purchase',
      'principle',
      'economic',
      'template',
      'transport',
      'service',
      'other',
    ])
  })

  it('mọi mã đều có nhãn tiếng Việt, không lọt mã trần ra giao diện', () => {
    for (const opt of CONTRACT_TYPE_OPTIONS) {
      expect(opt.label).toBe(contractTypeLabel(opt.value))
      expect(opt.label).not.toBe(opt.value)
    }
  })
})
