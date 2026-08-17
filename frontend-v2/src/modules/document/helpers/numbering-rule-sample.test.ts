import { describe, expect, it } from 'vitest'

import { numberingRuleSample } from './numbering-rule-sample'

describe('numberingRuleSample', () => {
  it('thay hết token trong mẫu mặc định, không sót dấu ngoặc nhọn nào', () => {
    const result = numberingRuleSample('{STT}/{Nam}/{LoaiVB}-{PhongBan}-{PhapNhan}', 8, 2026)

    expect(result).toBe('08/2026/TB-HCNS-DEGO')
    expect(result).not.toContain('{')
  })

  it('đệm số thứ tự thành hai chữ số — số hiệu hành chính không viết 8 mà viết 08', () => {
    expect(numberingRuleSample('{STT}', 1, 2026)).toBe('01')
  })

  it('không cắt số khi bộ đếm đã qua ba chữ số', () => {
    expect(numberingRuleSample('{STT}', 145, 2026)).toBe('145')
  })

  it('thay MỌI lần xuất hiện của cùng một token, không phải lần đầu', () => {
    expect(numberingRuleSample('{Nam}-{STT}-{Nam}', 3, 2026)).toBe('2026-03-2026')
  })

  it('trả nguyên văn phần chữ người dùng tự gõ ngoài token', () => {
    expect(numberingRuleSample('CV-{STT}/QĐ', 12, 2026)).toBe('CV-12/QĐ')
  })

  it('token viết sai tên thì giữ nguyên để người khai nhìn ra mình gõ nhầm', () => {
    expect(numberingRuleSample('{STT}/{Namm}', 5, 2026)).toBe('05/{Namm}')
  })
})
