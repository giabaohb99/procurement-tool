import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PackagingHistoryPoint } from '../types/packaging-cost-types'
import { PrintPriceChart } from './packaging-history-print-parts'

/** `count` tuần liên tiếp kết thúc đúng 29/10/2026 — điểm cuối sát điểm trước như dữ liệu thật CPT0234. */
function weeklySeries(count: number): PackagingHistoryPoint[] {
  return Array.from({ length: count }, (_, i) => {
    const day = new Date(Date.UTC(2026, 9, 29 - (count - 1 - i) * 7))
    return { date: day.toISOString().slice(0, 10), price: 2000 + i, supplier_code: 'A', supplier: 'A', qty: 1 }
  })
}

describe('PrintPriceChart x-axis labels', () => {
  it('keeps first and last date labels and never lets two labels sit closer than a label width', () => {
    const series = weeklySeries(52)
    const { container } = render(<PrintPriceChart series={series} />)
    const labels = [...container.querySelectorAll('text')].filter((node) => /^\d{2}\/\d{2}\/\d{2}$/.test(node.textContent ?? ''))
    expect(labels.length).toBeGreaterThanOrEqual(3)
    const [year, month, day] = series[0].date.split('-')
    expect(labels[0].textContent).toBe(`${day}/${month}/${year.slice(2)}`)
    expect(labels.at(-1)?.textContent).toBe('29/10/26')
    const xs = labels.map((node) => Number(node.getAttribute('x')))
    for (let i = 1; i < xs.length; i += 1) expect(xs[i] - xs[i - 1]).toBeGreaterThanOrEqual(52)
  })
})
