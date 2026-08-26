import { describe, expect, it } from 'vitest'

import type { DocPrerequisite } from '../types/document-link-rule'
import { prerequisiteText } from './prerequisite-text'

function row(overrides: Partial<DocPrerequisite> = {}): DocPrerequisite {
  return {
    sort_order: 1,
    relation: 4,
    relation_label: 'Hướng dẫn',
    target_type_id: 3,
    target_type_name: 'Quy trình',
    need: 1,
    available: 0,
    ...overrides,
  }
}

describe('prerequisiteText', () => {
  it('nói thẳng "chưa có văn bản nào" khi kho trống', () => {
    expect(prerequisiteText(row())).toBe('Chưa có văn bản nào còn hiệu lực')
  })

  it('nói rõ có mấy cái khi kho có nhưng chưa đủ số lượng', () => {
    //  Cũng nói "chưa có" thì người dùng mở danh sách ra thấy có, và từ đó
    //  không tin cảnh báo nữa.
    expect(prerequisiteText(row({ need: 2, available: 1 }))).toBe(
      'Cần 2 văn bản, hiện mới có 1 còn hiệu lực',
    )
  })
})
