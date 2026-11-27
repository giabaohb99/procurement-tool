import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { PackagingHistoryRow } from '../types/packaging-cost-types'
import { PackagingHistoryCard } from './packaging-history-card'

//  bao-CR-792: mã / số chứng từ chỉ thành đường bấm khi có quyền ở màn đích — bài kiểm này đứng ở vai người có đủ quyền.
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true }),
}))

const row: PackagingHistoryRow = {
  id: 7,
  date: '2026-09-11',
  code: 'NAP0029',
  name: 'Nắp HD cổ 50 (10gr) trắng',
  group: 'Nắp',
  supplier_code: 'N1',
  supplier: 'Công ty Nắp Việt',
  warehouse: 'Kho Dego',
  qty: 2000,
  unit: 'Cái',
  price: 900,
  vat: 8,
  amount: 1_800_000,
  source_type: 2,
  line_stage: 1,
  is_open: true,
  doc_id: 55,
  po_code: 'PO-0055',
  prev_price: 850,
  diff: 50,
  pct: 0.0588,
  seq: 1,
  fg_code: '',
  fg_name: '',
  role: null,
}

function renderCard(over: Partial<PackagingHistoryRow> = {}, productMode = false, rawMaterial = false) {
  render(
    <MemoryRouter>
      <PackagingHistoryCard row={{ ...row, ...over }} productMode={productMode} rawMaterial={rawMaterial} />
    </MemoryRouter>,
  )
}

describe('PackagingHistoryCard', () => {
  //  bao-CR-801 — thẻ của Lịch sử mua nguyên liệu: mã chữ thường (đang ở chính màn lịch sử của nó, kể cả người đủ quyền),
  //  số ĐMH ở Nguồn vẫn bấm được.
  it('shows a raw-material code as plain text but keeps the purchase order link', () => {
    renderCard({ code: 'NL0001', name: 'Hoạt chất Abamectin 95%' }, false, true)
    expect(screen.getByText('NL0001')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'NL0001' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'PO-0055' })).toBeInTheDocument()
  })

  it('leads with the purchase date and unit price, then the code link and the table fields', () => {
    renderCard()
    expect(screen.getByText('11/09/2026')).toBeInTheDocument()
    expect(screen.getByText('900')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'NAP0029' })).toBeInTheDocument()
    expect(screen.getByText('Công ty Nắp Việt')).toBeInTheDocument()
    expect(screen.getByText('1.800.000')).toBeInTheDocument()
    expect(screen.getByText('ĐMH đang mở')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'PO-0055' })).toBeInTheDocument()
  })

  it('colours "So lần trước" like the table (more expensive = red)', () => {
    renderCard()
    expect(screen.getByText(/\+50/)).toHaveClass('text-destructive')
  })

  it('shows the product and component line in product mode', () => {
    renderCard({ fg_code: 'HH0324', fg_name: 'IDA Global Chito', role: 2 }, true)
    expect(screen.getByText('HH0324')).toBeInTheDocument()
    expect(screen.getByText('IDA Global Chito')).toBeInTheDocument()
    expect(screen.getByText('Nắp')).toBeInTheDocument()
  })
})
