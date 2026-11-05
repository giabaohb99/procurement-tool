import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { CustomsComparePeriodCard } from './customs-compare-period-card'

const COLORS = ['red', 'green', 'blue'] as const

describe('CustomsComparePeriodCard', () => {
  it('lists every compared item with its price, unit and line count, in input order', () => {
    render(
      <CustomsComparePeriodCard
        row={{ period: '2026-03', label: 'T3/2026', values: [2.8175, 3.1], counts: [12, 4], lowData: [false, true] }}
        terms={['ATRAZINE', 'GLYPHOSATE']}
        colors={COLORS}
        unit="kg"
      />,
    )

    expect(screen.getByText('T3/2026')).toBeInTheDocument()
    const items = screen.getAllByRole('listitem')
    expect(items[0]).toHaveTextContent('ATRAZINE')
    expect(items[0]).toHaveTextContent('2,8175 USD/kg (12)')
    expect(items[1]).toHaveTextContent('GLYPHOSATE')
    expect(items[1]).toHaveTextContent('3,1 USD/kg (4)')
  })

  it('keeps a row with a dash for an item missing in this period — dropping it shifts every row below', () => {
    render(
      <CustomsComparePeriodCard
        row={{ period: '2026-04', label: 'T4/2026', values: [null, 0, 5], counts: [0, 2, 1], lowData: [false, false, false] }}
        terms={['A', 'B', 'C']}
        colors={COLORS}
        unit=""
      />,
    )

    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(3)
    expect(items[0]).toHaveTextContent('—')
    //  Giá 0 là một con số thật, không được đọc thành "không có giá".
    expect(items[1]).toHaveTextContent('0 USD (2)')
    expect(items[2]).toHaveTextContent('5 USD (1)')
  })

  it('two items typed with the same name still render two rows', () => {
    render(
      <CustomsComparePeriodCard
        row={{ period: 'p', label: 'p', values: [1, 2], counts: [1, 1], lowData: [false, false] }}
        terms={['X', 'X']}
        colors={COLORS}
        unit="kg"
      />,
    )

    expect(screen.getAllByRole('listitem')).toHaveLength(2)
  })
})
