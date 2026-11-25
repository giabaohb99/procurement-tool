import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'

import { EMPTY_IMPACT_FILTERS, type ImpactAdvancedFilters } from '../utils/packaging-impact-filters'
import { PackagingImpactAdvancedFilter } from './packaging-impact-advanced-filter'

function Harness({
  onChange,
  variant,
}: {
  onChange?: (value: ImpactAdvancedFilters) => void
  variant?: 'impact' | 'overview'
}) {
  const [value, setValue] = useState(EMPTY_IMPACT_FILTERS)
  return (
    <PackagingImpactAdvancedFilter
      variant={variant}
      value={value}
      onApply={(next) => {
        setValue(next)
        onChange?.(next)
      }}
    />
  )
}

describe('PackagingImpactAdvancedFilter', () => {
  it('applies the draft only when "Áp dụng" is pressed and shows the active-condition badge', async () => {
    const user = userEvent.setup()
    const applied: ImpactAdvancedFilters[] = []
    render(<Harness onChange={(next) => applied.push(next)} />)
    await user.click(screen.getByRole('button', { name: 'Lọc nâng cao' }))
    await user.click(screen.getByRole('button', { name: 'Tăng' }))
    await user.click(screen.getByRole('button', { name: 'Thùng' }))
    await user.type(screen.getByLabelText('Tăng/giảm /chai từ'), '-1.000')
    expect(applied).toHaveLength(0)
    await user.click(screen.getByRole('button', { name: 'Áp dụng' }))
    expect(applied).toHaveLength(1)
    expect(applied[0]).toMatchObject({ trend: 'up', roles: [5], diffBottle: { min: '-1.000', max: '' } })
    expect(screen.getByRole('button', { name: /Lọc nâng cao/ })).toHaveTextContent('3')
  })

  it('warns on an inverted range and "Xóa lọc" resets the draft', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await user.click(screen.getByRole('button', { name: 'Lọc nâng cao' }))
    await user.type(screen.getByLabelText('Quy cách thùng từ'), '30')
    await user.type(screen.getByLabelText('Quy cách thùng đến'), '10')
    expect(screen.getByRole('alert')).toHaveTextContent('chưa được áp dụng')
    await user.click(screen.getByRole('button', { name: 'Xóa lọc' }))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByLabelText('Quy cách thùng từ')).toHaveValue('')
  })

  it('reopens with the applied filters, not a stale draft', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await user.click(screen.getByRole('button', { name: 'Lọc nâng cao' }))
    await user.type(screen.getByLabelText('Quy cách thùng từ'), '12')
    await user.keyboard('{Escape}')
    await user.click(screen.getByRole('button', { name: 'Lọc nâng cao' }))
    expect(screen.getByLabelText('Quy cách thùng từ')).toHaveValue('')
  })

  it('overview variant: no trend section, six ranges including CP cũ and % chênh, roles by presence', async () => {
    const user = userEvent.setup()
    const applied: ImpactAdvancedFilters[] = []
    render(<Harness variant="overview" onChange={(next) => applied.push(next)} />)
    await user.click(screen.getByRole('button', { name: 'Lọc nâng cao' }))
    expect(screen.queryByRole('group', { name: 'Xu hướng chi phí' })).not.toBeInTheDocument()
    expect(screen.getByText('Có mã ở vai trò')).toBeInTheDocument()
    expect(screen.getByLabelText('CP bao bì/chai cũ từ')).toBeInTheDocument()
    await user.type(screen.getByLabelText('% chênh từ'), '5')
    await user.click(screen.getByRole('button', { name: 'Nắp' }))
    await user.click(screen.getByRole('button', { name: 'Áp dụng' }))
    expect(applied[0]).toMatchObject({ roles: [2], pct: { min: '5', max: '' } })
    expect(screen.getByRole('button', { name: /Lọc nâng cao/ })).toHaveTextContent('2')
  })

  it('impact variant keeps the trend section and the original four ranges', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await user.click(screen.getByRole('button', { name: 'Lọc nâng cao' }))
    expect(screen.getByRole('group', { name: 'Xu hướng chi phí' })).toBeInTheDocument()
    expect(screen.queryByLabelText('% chênh từ')).not.toBeInTheDocument()
  })
})
