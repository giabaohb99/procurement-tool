import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { CustomsImporterRow } from '../../types/customs'
import { CustomsImporterCard } from './customs-importer-card'

function importer(overrides: Partial<CustomsImporterRow> = {}): CustomsImporterRow & { rank: number } {
  return {
    importer_id: 5,
    name: 'CÔNG TY TNHH NÔNG DƯỢC VIỆT',
    tax_code: '0312345678',
    count: 42,
    qty: 125_000.5,
    share: 0.3456,
    wavg: 2.8175,
    last_date: '2026-09-30',
    rank: 1,
    ...overrides,
  }
}

describe('CustomsImporterCard', () => {
  it('shows rank, name, tax code, last import and the weighted price with its unit', () => {
    render(<CustomsImporterCard row={importer()} unit="kg" />)

    expect(screen.getByText('1.')).toBeInTheDocument()
    expect(screen.getByText('CÔNG TY TNHH NÔNG DƯỢC VIỆT')).toBeInTheDocument()
    expect(screen.getByText(/MST 0312345678/)).toBeInTheDocument()
    expect(screen.getByText(/Nhập gần nhất 30\/09\/2026/)).toBeInTheDocument()
    expect(screen.getByText('2,8175 USD/kg')).toBeInTheDocument()
    expect(screen.getByText(/125\.000,5 kg · 42 dòng/)).toBeInTheDocument()
    expect(screen.getByText('Thị phần 34,56%')).toBeInTheDocument()
  })

  it('does not leave a dangling "USD/" when the unit is unknown', () => {
    render(<CustomsImporterCard row={importer()} unit="" />)

    expect(screen.getByText('2,8175 USD')).toBeInTheDocument()
    expect(screen.queryByText(/USD\/$/)).toBeNull()
  })

  it('hides the share bar when backend has no share, instead of drawing an empty bar labelled 0%', () => {
    render(<CustomsImporterCard row={importer({ share: null })} unit="kg" />)

    expect(screen.queryByText(/Thị phần/)).toBeNull()
  })

  it('says so when the importer has no tax code and keeps a dash for a missing name', () => {
    render(<CustomsImporterCard row={importer({ tax_code: '', name: '', wavg: null })} unit="kg" />)

    expect(screen.getByText('Chưa có mã số thuế')).toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument()
    expect(screen.getByText('— USD/kg')).toBeInTheDocument()
  })
})
