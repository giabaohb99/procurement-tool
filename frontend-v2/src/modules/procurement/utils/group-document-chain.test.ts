import { describe, expect, it } from 'vitest'

import type { ChainAttachment } from '../types/document-chain'
import {
  groupDocumentChain,
  isChainImage,
  isChainPdf,
  isPreviewableChainFile,
} from './group-document-chain'

function makeFile(overrides: Partial<ChainAttachment> = {}): ChainAttachment {
  return {
    link_id: 1,
    source: 'PO',
    source_code: 'PO25080001',
    entity: 'purchase_order',
    entity_id: 10,
    doc_type: 'quote',
    doc_type_label: 'Báo giá',
    filename: 'bao-gia.pdf',
    url: '/files/bao-gia.pdf',
    content_type: 'application/pdf',
    size: 2048,
    sha256: '',
    ...overrides,
  }
}

describe('groupDocumentChain', () => {
  it('trả về danh sách rỗng khi đơn chưa có chứng từ nào', () => {
    expect(groupDocumentChain([])).toEqual([])
  })

  it('xếp các nấc theo đúng thứ tự PO -> PYC -> PKS -> YCKS dù backend trả lộn xộn', () => {
    const groups = groupDocumentChain([
      makeFile({ link_id: 1, source: 'YCKS', source_code: 'YCKS01' }),
      makeFile({ link_id: 2, source: 'PKS', source_code: 'PKS01' }),
      makeFile({ link_id: 3, source: 'PO', source_code: 'PO01' }),
      makeFile({ link_id: 4, source: 'PYC', source_code: 'PYC01' }),
    ])

    expect(groups.map((group) => group.source)).toEqual(['PO', 'PYC', 'PKS', 'YCKS'])
    expect(groups.map((group) => group.label)).toEqual([
      'Đơn mua hàng',
      'Yêu cầu mua hàng',
      'Phiếu khảo sát',
      'Yêu cầu báo giá',
    ])
  })

  it('bỏ nấc không có tệp nào thay vì hiện thẻ rỗng', () => {
    const groups = groupDocumentChain([makeFile({ link_id: 1, source: 'PO' })])
    expect(groups).toHaveLength(1)
    expect(groups[0].source).toBe('PO')
  })

  // Bẫy có thật: `_resolve_chain` khai entity `survey_line` HAI LẦN (id dòng NCC
  // và id dòng sản phẩm), nên cùng một tệp về hai lần. Bản v1 không khử trùng
  // nên đếm dôi. Xóa test này là mở lại đúng lỗi đó.
  it('khử tệp trùng theo link_id khi backend trả cùng một tệp nhiều lần', () => {
    const groups = groupDocumentChain([
      makeFile({ link_id: 7, source: 'PKS', entity: 'survey_line' }),
      makeFile({ link_id: 7, source: 'PKS', entity: 'survey_line' }),
      makeFile({ link_id: 8, source: 'PKS', entity: 'survey_line' }),
    ])

    expect(groups).toHaveLength(1)
    expect(groups[0].total).toBe(2)
    expect(groups[0].types[0].files.map((file) => file.link_id)).toEqual([7, 8])
  })

  it('gom theo nhãn loại chứng từ, giữ thứ tự gặp đầu tiên', () => {
    const groups = groupDocumentChain([
      makeFile({ link_id: 1, doc_type_label: 'Hóa đơn GTGT' }),
      makeFile({ link_id: 2, doc_type_label: 'Báo giá' }),
      makeFile({ link_id: 3, doc_type_label: 'Hóa đơn GTGT' }),
    ])

    expect(groups[0].types.map((type) => type.label)).toEqual(['Hóa đơn GTGT', 'Báo giá'])
    expect(groups[0].types[0].files).toHaveLength(2)
  })

  it('dồn tệp không rõ loại về mục "Khác" — kể cả khi backend trả gạch ngang', () => {
    const groups = groupDocumentChain([
      makeFile({ link_id: 1, doc_type: '', doc_type_label: '—' }),
      makeFile({ link_id: 2, doc_type: '', doc_type_label: '' }),
    ])

    expect(groups[0].types).toHaveLength(1)
    expect(groups[0].types[0].label).toBe('Khác')
    expect(groups[0].types[0].files).toHaveLength(2)
  })

  it('giữ lại nấc lạ và xếp xuống cuối thay vì nuốt mất tệp', () => {
    const groups = groupDocumentChain([
      makeFile({ link_id: 1, source: 'HDNT', source_code: 'HD01' }),
      makeFile({ link_id: 2, source: 'PO', source_code: 'PO01' }),
    ])

    expect(groups.map((group) => group.source)).toEqual(['PO', 'HDNT'])
    // Không tra được nhãn thì hiện chính mã nấc, đừng để trống.
    expect(groups[1].label).toBe('HDNT')
  })

  it('lấy mã nấc từ tệp đầu tiên CÓ mã, không để rỗng khi tệp đầu thiếu mã', () => {
    const groups = groupDocumentChain([
      makeFile({ link_id: 1, source_code: '' }),
      makeFile({ link_id: 2, source_code: 'PO25080009' }),
    ])

    expect(groups[0].code).toBe('PO25080009')
  })

  it('mã rỗng ở mọi tệp thì trả chuỗi rỗng chứ không undefined', () => {
    const groups = groupDocumentChain([makeFile({ source_code: '' })])
    expect(groups[0].code).toBe('')
  })
})

describe('isPreviewableChainFile', () => {
  it('cho xem trước ảnh và PDF', () => {
    expect(isPreviewableChainFile(makeFile({ content_type: 'image/png' }))).toBe(true)
    expect(isPreviewableChainFile(makeFile({ content_type: 'application/pdf' }))).toBe(true)
  })

  it('không xem trước được Word/Excel', () => {
    expect(
      isPreviewableChainFile(
        makeFile({ filename: 'bang-gia.xlsx', content_type: 'application/vnd.ms-excel' }),
      ),
    ).toBe(false)
  })

  // Backend để `url` rỗng với entity riêng tư. Không chặn ở đây thì thẻ ảnh trỏ
  // vào chuỗi rỗng và trình duyệt vẽ ra một ô ảnh hỏng.
  it('không xem trước khi backend không trả đường đọc (entity riêng tư)', () => {
    expect(isPreviewableChainFile(makeFile({ content_type: 'image/png', url: '' }))).toBe(false)
  })

  it('nhận PDF theo đuôi tệp khi content_type bị rỗng', () => {
    expect(isChainPdf(makeFile({ content_type: '', filename: 'HOP-DONG.PDF' }))).toBe(true)
    expect(isChainImage(makeFile({ content_type: '' }))).toBe(false)
  })
})
