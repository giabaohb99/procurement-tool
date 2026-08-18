import { describe, expect, it } from 'vitest'

import { linkRuleSentence } from './link-rule-sentence'

function cau(
  rule: { is_required: boolean; min_count: number; max_count: number },
  sourceTypeName?: string,
) {
  return linkRuleSentence({
    rule,
    relationLabel: 'Căn cứ theo',
    targetTypeName: 'Thư công',
    sourceTypeName,
  })
}

describe('linkRuleSentence', () => {
  it('dòng bắt buộc không giới hạn trên đọc là "ít nhất N"', () => {
    expect(cau({ is_required: true, min_count: 1, max_count: 0 }, 'Trích lục')).toBe(
      'Mỗi văn bản «Trích lục» phải căn cứ theo ít nhất 1 văn bản «Thư công».',
    )
  })

  it('tối thiểu bằng tối đa thì đọc là "đúng N"', () => {
    expect(cau({ is_required: true, min_count: 1, max_count: 1 }, 'Trích lục')).toBe(
      'Mỗi văn bản «Trích lục» phải căn cứ theo đúng 1 văn bản «Thư công».',
    )
  })

  it('có khoảng thì đọc thành "2–3 văn bản"', () => {
    expect(cau({ is_required: true, min_count: 2, max_count: 3 }, 'Trích lục')).toBe(
      'Mỗi văn bản «Trích lục» phải căn cứ theo 2–3 văn bản «Thư công».',
    )
  })

  it('bắt buộc mà khai tối thiểu 0 vẫn đọc là "ít nhất 1"', () => {
    //  Backend tính `max(min_count, 1)` khi chặn gửi duyệt. Câu đọc "0" thì
    //  người khai tưởng để trống cũng được, rồi ngạc nhiên vì bị chặn.
    expect(cau({ is_required: true, min_count: 0, max_count: 0 }, 'Trích lục')).toBe(
      'Mỗi văn bản «Trích lục» phải căn cứ theo ít nhất 1 văn bản «Thư công».',
    )
  })

  it('dòng tùy chọn mở bằng "có thể", không phải "phải"', () => {
    expect(cau({ is_required: false, min_count: 0, max_count: 0 }, 'Trích lục')).toBe(
      'Mỗi văn bản «Trích lục» có thể căn cứ theo một hoặc nhiều văn bản «Thư công».',
    )
  })

  it('tùy chọn có trần thì nói rõ trần', () => {
    expect(cau({ is_required: false, min_count: 0, max_count: 2 }, 'Trích lục')).toBe(
      'Mỗi văn bản «Trích lục» có thể căn cứ theo tối đa 2 văn bản «Thư công».',
    )
  })

  it('không kén loại đích thì không bỏ tên vào ngoặc kép', () => {
    //  «Loại bất kỳ» đọc ra thành tên một loại văn bản có thật, mà đó lại là
    //  chỗ duy nhất không có loại nào.
    expect(
      linkRuleSentence({
        rule: { is_required: false, min_count: 0, max_count: 0 },
        relationLabel: 'Tham chiếu',
        sourceTypeName: 'Trích lục',
      }),
    ).toBe('Mỗi văn bản «Trích lục» có thể tham chiếu một hoặc nhiều văn bản thuộc loại bất kỳ.')
  })

  it('chưa có tên loại (đang tạo mới) thì mở bằng "Văn bản loại này"', () => {
    expect(cau({ is_required: true, min_count: 1, max_count: 0 })).toBe(
      'Văn bản loại này phải căn cứ theo ít nhất 1 văn bản «Thư công».',
    )
  })
})
