import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { CustomsRegulationHit } from '../../types/customs'
import { CustomsRegulationCard } from './customs-regulation-card'

function hit(overrides: Partial<CustomsRegulationHit> = {}): CustomsRegulationHit {
  return {
    id: 3,
    list_code: 10,
    list_label: 'TT 75/2025 — hoạt chất cấm',
    seq_no: '12',
    name: 'Paraquat dichloride',
    name_vi: 'Paraquat',
    cas_no: '1910-42-5',
    formula: 'C12H14Cl2N2',
    category: '',
    threshold_kg: null,
    mixture_pct: null,
    banned_year: 2026,
    legal_basis: 'TT 75/2025/TT-BNNMT',
    note: '',
    obligation: 'Cấm sản xuất, kinh doanh, sử dụng.',
    pesticide_count: 4,
    pesticide_matchable: true,
    ...overrides,
  }
}

describe('CustomsRegulationCard', () => {
  it('leads with the common name, keeps scientific name, CAS and formula on the secondary line', () => {
    render(<CustomsRegulationCard row={hit()} />)

    expect(screen.getByText('Paraquat')).toBeInTheDocument()
    expect(screen.getByText('Paraquat dichloride · CAS 1910-42-5 · C12H14Cl2N2')).toBeInTheDocument()
    expect(screen.getByText('STT 12')).toBeInTheDocument()
    expect(screen.getByText('TT 75/2025 — hoạt chất cấm')).toBeInTheDocument()
    expect(screen.getByText('Cấm sản xuất, kinh doanh, sử dụng.')).toBeInTheDocument()
  })

  it('shows the ban with the year, same wording as the table column', () => {
    render(<CustomsRegulationCard row={hit()} />)

    expect(screen.getByText('CẤM từ 2026')).toBeInTheDocument()
  })

  it('shows the kg threshold of a Phụ lục IV row', () => {
    render(<CustomsRegulationCard row={hit({ list_code: 4, threshold_kg: 1000, banned_year: null })} />)

    expect(screen.getByText('1.000 kg')).toBeInTheDocument()
  })

  it('falls back to the scientific name when there is no Vietnamese name, without repeating it', () => {
    render(<CustomsRegulationCard row={hit({ name_vi: '' })} />)

    expect(screen.getAllByText(/Paraquat dichloride/)).toHaveLength(1)
  })

  it('the "N thuốc" button opens the drug list for that row', async () => {
    const onOpen = vi.fn()
    render(<CustomsRegulationCard row={hit()} onOpenPesticides={onOpen} />)

    await userEvent.click(screen.getByRole('button', { name: '4 thuốc' }))
    expect(onOpen).toHaveBeenCalledWith(expect.objectContaining({ id: 3 }))
  })

  it('without a handler (keyword alert table) there is no drug line at all', () => {
    render(<CustomsRegulationCard row={hit()} />)

    expect(screen.queryByText(/Thuốc BVTV chứa/)).toBeNull()
    expect(screen.queryByRole('button')).toBeNull()
  })

  it('says the drug catalog is not loaded instead of "0" when the count is null', () => {
    render(<CustomsRegulationCard row={hit({ pesticide_count: null })} onOpenPesticides={vi.fn()} />)

    expect(screen.getByText('Chưa nạp danh mục thuốc')).toBeInTheDocument()
  })

  it('a non-TT75 row has no drug line even when a handler is given', () => {
    render(
      <CustomsRegulationCard
        row={hit({ list_code: 1, banned_year: null, pesticide_count: null })}
        onOpenPesticides={vi.fn()}
      />,
    )

    expect(screen.queryByText(/Thuốc BVTV chứa/)).toBeNull()
  })
})
