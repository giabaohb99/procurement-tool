import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'

import { EMPTY_IMPACT_FILTERS, type ImpactAdvancedFilters } from '../utils/packaging-impact-filters'
import { PackagingImpactAdvancedFilter } from './packaging-impact-advanced-filter'

function Harness({ onChange }: { onChange?: (value: ImpactAdvancedFilters) => void }) {
  const [value, setValue] = useState(EMPTY_IMPACT_FILTERS)
  return (
    <PackagingImpactAdvancedFilter
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
})
