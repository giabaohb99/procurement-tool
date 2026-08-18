import { describe, expect, it } from 'vitest'

import type { DocTypeLinkRule } from '../types/document-link-rule'
import { countText } from './link-rule-count-text'

/**
 * Cột "Số lượng" đọc từ CẶP `min_count`/`max_count`, mà tài liệu lại mô tả bằng
 * lời: "đúng 1", "từ 1", "0 trở lên". Dịch sai chỗ này thì người khai quy tắc
 * tưởng mình đặt một đằng, hệ thống chặn một nẻo.
 */
//  Chỉ dựng ĐÚNG hai cột hàm này đọc — dựng cả bản ghi thì mỗi lần thêm cột vào
//  bảng quy tắc là bài kiểm đỏ, dù chẳng liên quan gì tới việc nó đang kiểm.
function rule(min: number, max: number): Pick<DocTypeLinkRule, 'min_count' | 'max_count'> {
  return { min_count: min, max_count: max }
}

describe('countText', () => {
  it('min bằng max thì đọc là "đúng N" — dòng HDCV hướng dẫn đúng 1 Quy trình', () => {
    expect(countText(rule(1, 1))).toBe('Đúng 1')
  })

  it('chỉ có min thì đọc là "từ N" — dòng Biểu mẫu thuộc về từ 1 Quy trình', () => {
    expect(countText(rule(1, 0))).toBe('Từ 1')
  })

  it('không khai gì thì đọc là "0 trở lên", không phải "đúng 0"', () => {
    expect(countText(rule(0, 0))).toBe('0 trở lên')
  })

  it('chỉ có max thì nói rõ đó là trần, không phải con số bắt buộc', () => {
    expect(countText(rule(0, 3))).toBe('Tối đa 3')
  })

  it('có cả hai và khác nhau thì đọc thành khoảng', () => {
    expect(countText(rule(1, 3))).toBe('Từ 1 tới 3')
  })
})
