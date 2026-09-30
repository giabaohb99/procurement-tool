import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PrintSignatureCell } from '../types/purchase-request-detail'
import type { PrintSignatureSource } from '../utils/purchase-request-signature-cells'
import { SignatureSection } from './purchase-request-print-page'

// bao-CR-531: cụm «XÉT DUYỆT» vẽ 2, 3 hoặc 4 ô theo backend; «Không chữ ký» bỏ cả tên lẫn ảnh.

function makeSource(cells?: PrintSignatureCell[]): PrintSignatureSource {
  return {
    requester: 'Nguoi Lap',
    requester_signature: 'https://cdn/ky-lap.png',
    approver_name: 'Le Phuoc Huu',
    approver_signature: 'https://cdn/ky-huu.png',
    purchasing_head_name: 'Pham Khanh Ngan',
    purchasing_head_signature: '',
    print_signature_cells: cells,
  }
}

const fourCells: PrintSignatureCell[] = [
  { key: 'director', role: 'Giám đốc', name: '', signature: '' },
  { key: 'purchasing_head', role: 'TP/BP mua hàng', name: 'Pham Khanh Ngan', signature: '' },
  { key: 'proposer', role: 'TP/BP đề xuất', name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' },
  { key: 'preparer', role: 'Người lập', name: 'Nguoi Lap', signature: 'https://cdn/ky-lap.png' },
]

//  bao-CR-536 — ca ICARE: đại diện = TP/BP đề xuất → tên lên «Giám đốc», ô đề xuất GIỮ nhưng trống.
const icareCells: PrintSignatureCell[] = [
  { key: 'director', role: 'Giám đốc', name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' },
  { key: 'purchasing_head', role: 'TP/BP mua hàng', name: 'Pham Khanh Ngan', signature: '' },
  { key: 'proposer', role: 'TP/BP đề xuất', name: '', signature: '' },
  { key: 'preparer', role: 'Người lập', name: 'Nguoi Lap', signature: 'https://cdn/ky-lap.png' },
]

//  bao-CR-536 — hộ kinh doanh 3 ô, có tên như công ty.
const householdCells: PrintSignatureCell[] = [
  { key: 'household_owner', role: 'Chủ hộ', name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' },
  { key: 'proposer', role: 'TP/BP đề xuất', name: '', signature: '' },
  { key: 'preparer', role: 'Người lập', name: 'Nguoi Lap', signature: 'https://cdn/ky-lap.png' },
]

function renderSection(cells: PrintSignatureCell[] | undefined, showSignature = true, taxMode = false) {
  const view = render(
    <SignatureSection purchaseRequest={makeSource(cells)} taxMode={taxMode} showSignature={showSignature} />,
  )
  const grid = view.container.querySelector('.pr-print-signature-grid') as HTMLElement
  return { ...view, grid }
}

describe('SignatureSection', () => {
  it('draws four cells with a blank director when nobody merges', () => {
    const { grid } = renderSection(fourCells)
    expect(within(grid).getAllByText('(Ký, ghi rõ họ tên)')).toHaveLength(4)
    expect(grid.style.getPropertyValue('--pr-signature-columns')).toBe('4')
    expect(screen.getAllByRole('img')).toHaveLength(2)
  })

  it('keeps all four cells and puts the legal representative into «Giám đốc» (ICARE case)', () => {
    //  bao-CR-531 bỏ hẳn ô «TP/BP đề xuất» — đại ca báo thiếu ô (PYC29092603). Nay ô vẫn có, chỉ trống.
    const { grid } = renderSection(icareCells)
    expect(screen.getByText('TP/BP đề xuất')).toBeInTheDocument()
    expect(within(grid).getAllByText('(Ký, ghi rõ họ tên)')).toHaveLength(4)
    expect(grid.style.getPropertyValue('--pr-signature-columns')).toBe('4')
    expect(screen.getByAltText('Chữ ký Giám đốc')).toHaveAttribute('src', 'https://cdn/ky-huu.png')
    expect(screen.getAllByText('Le Phuoc Huu')).toHaveLength(1)
  })

  it('draws «Chủ hộ · TP/BP đề xuất · Người lập» with names for a household business', () => {
    const { grid } = renderSection(householdCells)
    expect(screen.getByText('Chủ hộ')).toBeInTheDocument()
    expect(screen.getByText('TP/BP đề xuất')).toBeInTheDocument()
    expect(screen.queryByText('Giám đốc')).toBeNull()
    expect(screen.queryByText('TP/BP mua hàng')).toBeNull()
    expect(screen.getByText('Le Phuoc Huu')).toBeInTheDocument()
    expect(screen.getByText('Nguoi Lap')).toBeInTheDocument()
    expect(grid.style.getPropertyValue('--pr-signature-columns')).toBe('3')
  })

  it('"Không chữ ký" removes names as well as images', () => {
    renderSection(icareCells, false)
    expect(screen.queryByRole('img')).toBeNull()
    expect(screen.queryByText('Le Phuoc Huu')).toBeNull()
    expect(screen.queryByText('Nguoi Lap')).toBeNull()
    expect(screen.getByText('Giám đốc')).toBeInTheDocument()
  })

  it('tax template keeps the backend cell set but blanks everything', () => {
    renderSection(householdCells, true, true)
    expect(screen.queryByRole('img')).toBeNull()
    expect(screen.queryByText('Le Phuoc Huu')).toBeNull()
    expect(screen.queryByText('Nguoi Lap')).toBeNull()
    expect(screen.getByText('Chủ hộ')).toBeInTheDocument()
    expect(screen.queryByText('TP/BP mua hàng')).toBeNull()
  })

  it('falls back to the legacy four cells when the backend has no cell list', () => {
    renderSection(undefined)
    for (const role of ['Giám đốc', 'TP/BP mua hàng', 'TP/BP đề xuất', 'Người lập']) {
      expect(screen.getByText(role)).toBeInTheDocument()
    }
    expect(screen.getByText('Le Phuoc Huu')).toBeInTheDocument()
  })
})
