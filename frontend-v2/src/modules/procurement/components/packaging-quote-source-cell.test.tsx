import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'

import type { PackagingQuote } from '../types/packaging-cost-types'
import { PackagingQuoteSourceCell } from './packaging-quote-source-cell'

let canReadImport = true
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => canReadImport && entity === 'import' && action === 'read',
  }),
}))

function quote(over: Partial<PackagingQuote>): PackagingQuote {
  return {
    id: 1,
    product_code: 'CPT0075',
    supplier_code: '',
    price: 1000,
    vat: 8,
    valid_from: '2026-12-01',
    note: '',
    ...over,
  }
}

function Where() {
  return <p data-testid="where">{useLocation().pathname}</p>
}

function renderCell(row: PackagingQuote, onRowClick = vi.fn()) {
  render(
    <MemoryRouter initialEntries={['/start']}>
      <Routes>
        <Route
          path="/start"
          element={
            <div onClick={onRowClick}>
              <PackagingQuoteSourceCell row={row} />
            </div>
          }
        />
        <Route path={appRoutes.system.importDetail(':id')} element={<Where />} />
      </Routes>
    </MemoryRouter>,
  )
  return onRowClick
}

describe('PackagingQuoteSourceCell', () => {
  beforeEach(() => {
    canReadImport = true
  })

  //  bao-CR-792 — trang lô nhập gác `import.read`: thiếu quyền thì chữ nguồn không bấm được.
  it('shows the batch as plain text without import.read', () => {
    canReadImport = false
    renderCell(quote({ source_type: 2, source_id: 57 }))
    expect(screen.getByText('Nhập Excel (lô #57)')).toBeInTheDocument()
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('shows "Nhập tay" as plain text for a hand-typed quote', () => {
    renderCell(quote({ source_type: 1, source_id: 0 }))
    expect(screen.getByText('Nhập tay')).toBeInTheDocument()
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('shows the batch number of an Excel quote and opens that import batch without triggering the row', async () => {
    const onRowClick = renderCell(quote({ source_type: 2, source_id: 57 }))
    await userEvent.setup().click(screen.getByRole('link', { name: 'Nhập Excel (lô #57)' }))
    expect(screen.getByTestId('where')).toHaveTextContent(appRoutes.system.importDetail(57))
    expect(onRowClick).not.toHaveBeenCalled()
  })

  it('renders nothing when the server sends no source (older server)', () => {
    const { container } = render(
      <MemoryRouter>
        <PackagingQuoteSourceCell row={quote({})} />
      </MemoryRouter>,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('falls back to "Mã n" for a source code this build does not know', () => {
    renderCell(quote({ source_type: 9, source_id: 3 }))
    expect(screen.getByText('Mã 9')).toBeInTheDocument()
  })
})
