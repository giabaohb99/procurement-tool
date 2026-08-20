import { describe, expect, it } from 'vitest'

import type { AttachmentFile, DocumentTypeOption } from '../api/purchase-request-support-api'
import { groupAttachmentsByType, withOtherType } from './document-attachment-groups'

const TYPES: DocumentTypeOption[] = [
  { value: 'quotation', label: 'Báo giá' },
  { value: 'vat_invoice', label: 'Hóa đơn GTGT' },
  { value: 'other', label: 'Khác' },
]

function file(id: number, docType: string): AttachmentFile {
  return {
    id,
    file_id: id,
    filename: `tep-${id}.pdf`,
    url: `/files/tep-${id}.pdf`,
    content_type: 'application/pdf',
    size: 1024,
    sha256: '',
    doc_type: docType,
    entity: 'purchase_order',
    entity_id: 1,
  }
}

describe('groupAttachmentsByType', () => {
  it('gom tệp theo mục và giữ đúng thứ tự danh mục của backend', () => {
    const groups = groupAttachmentsByType(
      // Cố tình đảo: hóa đơn tải lên trước, báo giá tải lên sau.
      [file(1, 'vat_invoice'), file(2, 'quotation'), file(3, 'vat_invoice')],
      TYPES,
    )

    expect(groups.map((group) => group.label)).toEqual(['Báo giá', 'Hóa đơn GTGT'])
    expect(groups[1].files.map((f) => f.id)).toEqual([1, 3])
  })

  it('tệp không khai loại thì rơi vào mục "Khác", không mất tích', () => {
    const groups = groupAttachmentsByType([file(1, '')], TYPES)

    expect(groups).toHaveLength(1)
    expect(groups[0].type).toBe('other')
    expect(groups[0].label).toBe('Khác')
  })

  /**
   * Danh mục loại chứng từ nằm cứng trong mã backend; bỏ bớt một loại là các tệp
   * cũ mang loại đó thành "lạ". Vẫn phải hiện ra, không thì số ở tiêu đề thẻ đếm
   * 5 tệp mà bên dưới chỉ thấy 3.
   */
  it('loại lạ vẫn hiện thành một mục riêng, xếp sau các mục có trong danh mục', () => {
    const groups = groupAttachmentsByType([file(1, 'co_cq'), file(2, 'quotation')], TYPES)

    expect(groups.map((group) => group.type)).toEqual(['quotation', 'co_cq'])
  })

  it('không có tệp nào thì không có mục nào', () => {
    expect(groupAttachmentsByType([], TYPES)).toEqual([])
  })
})

describe('withOtherType', () => {
  it('thêm mục "Khác" khi danh mục backend chưa có', () => {
    expect(withOtherType([{ value: 'quotation', label: 'Báo giá' }])).toEqual([
      { value: 'quotation', label: 'Báo giá' },
      { value: 'other', label: 'Khác' },
    ])
  })

  it('danh mục đã có "Khác" thì để nguyên, không nhân đôi', () => {
    expect(withOtherType(TYPES)).toBe(TYPES)
  })
})
