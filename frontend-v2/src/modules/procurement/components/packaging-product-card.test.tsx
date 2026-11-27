import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { PACKAGING_COST_TREND_CODE } from '@/shared/constants/statuses'

import type { PackagingImpactProduct } from '../types/packaging-cost-types'
import { PackagingProductCard } from './packaging-product-card'

const product: PackagingImpactProduct = {
  fg_code: 'HH0260',
  fg_name: 'GC - I - 260 - Bohex SC - 450ml - 40',
  carton_qty: 40,
  parts: [
    { role: 1, code: 'CPT0042', old: 6000, new: 6532, applied: 6532, selected: true },
    { role: 2, code: '', old: null, new: null, applied: null, selected: false },
    { role: 3, code: 'NHG0260', old: 800, new: 700, applied: 700, selected: false },
  ],
  cost_old_bottle: 6800,
  cost_new_bottle: 7232,
  cost_applied_bottle: 7300,
  diff_bottle: 500,
  pct: 0.0735,
  cost_old_carton: 272000,
  cost_applied_carton: 292000,
  diff_carton: -20000,
  trend: PACKAGING_COST_TREND_CODE.UP,
  warnings: [],
}

function renderCard(variant: 'impact' | 'overview') {
  render(
    <MemoryRouter>
      <PackagingProductCard row={product} variant={variant} />
    </MemoryRouter>,
  )
}

describe('PackagingProductCard', () => {
  it('impact: shows old -> applied cost per bottle and the per-bottle / per-carton diffs in table colours', () => {
    renderCard('impact')
    expect(screen.getByText('HH0260')).toBeInTheDocument()
    for (const label of ['CP cũ /chai', 'CP mới /chai', 'Tăng/giảm /chai', 'Tăng/giảm /thùng']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
    //  Tác động đo "mới" bằng giá ĐANG ÁP (7.300), không phải giá mới (7.232).
    expect(screen.getByText('7.300')).toBeInTheDocument()
    expect(screen.getByText('+500')).toHaveClass('text-destructive')
    expect(screen.getByText('-20.000')).toHaveClass('text-emerald-600')
  })

  it('lists only components that have a code, with old -> new price, and the carton spec', () => {
    renderCard('impact')
    expect(screen.getByText('Chai')).toBeInTheDocument()
    expect(screen.getByText('CPT0042')).toBeInTheDocument()
    expect(screen.getByText('6.532')).toHaveClass('text-destructive')
    expect(screen.getByText('700')).toHaveClass('text-emerald-600')
    expect(screen.getByText('Quy cách 40')).toBeInTheDocument()
    //  Nắp không có mã, Nhãn thùng / Thùng không có dòng: ẩn hẳn.
    expect(screen.queryByText('Nắp')).not.toBeInTheDocument()
    expect(screen.queryByText('Thùng')).not.toBeInTheDocument()
  })

  it('marks carton components as per carton and shows warnings', () => {
    render(
      <MemoryRouter>
        <PackagingProductCard
          variant="impact"
          row={{
            ...product,
            parts: [{ role: 5, code: 'THU0001', old: 9000, new: 9500, applied: 9500, selected: false }],
            warnings: [{ kind: 3 }],
          }}
        />
      </MemoryRouter>,
    )
    expect(screen.getByText('Thùng')).toBeInTheDocument()
    expect(screen.getByText('/thùng')).toBeInTheDocument()
    expect(screen.getByText('Thiếu giá thành phần')).toBeInTheDocument()
  })

  it('overview: links the product and component codes to history and shows % and the trend badge', () => {
    renderCard('overview')
    expect(screen.getByRole('link', { name: 'HH0260' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'CPT0042' })).toBeInTheDocument()
    expect(screen.getByText('7.232')).toBeInTheDocument()
    expect(screen.getByText('+7,4%')).toBeInTheDocument()
    expect(screen.getByText('Tăng')).toBeInTheDocument()
  })
})
