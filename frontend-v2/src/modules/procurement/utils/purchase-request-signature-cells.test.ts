import { describe, expect, it } from 'vitest'

import type { PrintSignatureCell } from '../types/purchase-request-detail'
import {
  resolvePrintSignatureCells,
  type PrintSignatureSource,
} from './purchase-request-signature-cells'

// bao-CR-531 / bao-CR-536: backend quyết BỘ Ô, giao diện chỉ áp «Không chữ ký» / «Mẫu thuế».

function makeSource(overrides: Partial<PrintSignatureSource> = {}): PrintSignatureSource {
  return {
    requester: 'Nguoi Lap',
    requester_signature: 'https://cdn/ky-lap.png',
    approver_name: 'Le Phuoc Huu',
    approver_signature: 'https://cdn/ky-huu.png',
    purchasing_head_name: 'Pham Khanh Ngan',
    purchasing_head_signature: 'https://cdn/ky-ngan.png',
    ...overrides,
  }
}

//  Ca ICARE theo luật bao-CR-536: đại diện = TP/BP đề xuất → tên lên «Giám đốc», ô đề xuất GIỮ nhưng trống.
const mergedCells: PrintSignatureCell[] = [
  { key: 'director', role: 'Giám đốc', name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' },
  { key: 'purchasing_head', role: 'TP/BP mua hàng', name: 'Pham Khanh Ngan', signature: 'https://cdn/ky-ngan.png' },
  { key: 'proposer', role: 'TP/BP đề xuất', name: '', signature: '' },
  { key: 'preparer', role: 'Người lập', name: 'Nguoi Lap', signature: 'https://cdn/ky-lap.png' },
]

const withSignature = { taxMode: false, showSignature: true }

describe('resolvePrintSignatureCells', () => {
  it('renders exactly the cell set sent by the backend (merged director keeps 4 cells)', () => {
    const cells = resolvePrintSignatureCells(makeSource({ print_signature_cells: mergedCells }), withSignature)
    expect(cells.map((c) => c.role)).toEqual(['Giám đốc', 'TP/BP mua hàng', 'TP/BP đề xuất', 'Người lập'])
    expect(cells[0]).toMatchObject({ name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' })
    //  Không tự "điền lại" ô trống từ khóa rời `approver_name` — ô trùng phải trống như backend gửi.
    expect(cells[2]).toMatchObject({ name: '', signature: '' })
  })

  it('"Không chữ ký" blanks BOTH the image and the name (names used to stay before CR-531)', () => {
    const cells = resolvePrintSignatureCells(makeSource({ print_signature_cells: mergedCells }), {
      taxMode: false,
      showSignature: false,
    })
    expect(cells).toHaveLength(4)
    expect(cells.every((c) => c.name === '' && c.signature === '')).toBe(true)
  })

  it('household prints names like a company, and tax template still blanks them', () => {
    //  bao-CR-539: hộ kinh doanh 4 ô như công ty, chỉ khác nhãn «Chủ hộ»; CÓ tên.
    const household: PrintSignatureCell[] = [
      { key: 'household_owner', role: 'Chủ hộ', name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' },
      { key: 'purchasing_head', role: 'TP/BP mua hàng', name: 'Pham Khanh Ngan', signature: '' },
      { key: 'proposer', role: 'TP/BP đề xuất', name: '', signature: '' },
      { key: 'preparer', role: 'Người lập', name: 'Nguoi Lap', signature: 'https://cdn/ky-lap.png' },
    ]
    const shown = resolvePrintSignatureCells(makeSource({ print_signature_cells: household }), withSignature)
    expect(shown.map((c) => c.role)).toEqual(['Chủ hộ', 'TP/BP mua hàng', 'TP/BP đề xuất', 'Người lập'])
    expect(shown[0].name).toBe('Le Phuoc Huu')
    expect(shown[1].name).toBe('Pham Khanh Ngan')
    expect(shown[3].name).toBe('Nguoi Lap')

    const tax = resolvePrintSignatureCells(makeSource({ print_signature_cells: household }), {
      taxMode: true,
      showSignature: true,
    })
    expect(tax.map((c) => c.role)).toEqual(['Chủ hộ', 'TP/BP mua hàng', 'TP/BP đề xuất', 'Người lập'])
    expect(tax.every((c) => c.name === '' && c.signature === '')).toBe(true)
  })

  it('tax template blanks names even if the backend sent some', () => {
    const cells = resolvePrintSignatureCells(makeSource({ print_signature_cells: mergedCells }), {
      taxMode: true,
      showSignature: true,
    })
    expect(cells.map((c) => c.name)).toEqual(['', '', '', ''])
  })

  it.each([undefined, []])(
    'falls back to the four legacy cells when the backend sends %s (old backend)',
    (value) => {
      const cells = resolvePrintSignatureCells(makeSource({ print_signature_cells: value }), withSignature)
      expect(cells.map((c) => c.role)).toEqual(['Giám đốc', 'TP/BP mua hàng', 'TP/BP đề xuất', 'Người lập'])
      expect(cells[0]).toMatchObject({ name: '', signature: '' })
      expect(cells[2]).toMatchObject({ name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' })
      expect(cells[3]).toMatchObject({ name: 'Nguoi Lap' })
    },
  )

  it('tolerates null-ish fields from the backend without printing "undefined"', () => {
    const broken = [{ key: 'director', role: 'Giám đốc' } as unknown as PrintSignatureCell]
    const cells = resolvePrintSignatureCells(makeSource({ print_signature_cells: broken }), withSignature)
    expect(cells[0]).toEqual({ key: 'director', role: 'Giám đốc', name: '', signature: '' })
  })

  it('does not mutate the backend payload when blanking', () => {
    const payload = mergedCells.map((c) => ({ ...c }))
    resolvePrintSignatureCells(makeSource({ print_signature_cells: payload }), {
      taxMode: false,
      showSignature: false,
    })
    expect(payload[0].name).toBe('Le Phuoc Huu')
  })
})
