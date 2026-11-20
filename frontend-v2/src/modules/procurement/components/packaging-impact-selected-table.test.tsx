import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PackagingSelectedCode } from '../types/packaging-cost-types'
import { PackagingImpactSelectedTable } from './packaging-impact-selected-table'

const row = (over: Partial<PackagingSelectedCode> = {}): PackagingSelectedCode => ({
  code: 'CPT0105',
  name: 'Chai PET 1 lít',
  group: 'Chai',
  unit: 'Cái',
  old: 1000,
  new: 1100,
  assumed: null,
  applied: 1100,
  diff: 100,
  pct: 10,
  usage: 12,
  min: 950,
  max: 1150,
  floor: null,
  ceiling: null,
  warnings: [],
  ...over,
})

/** Bọc state thật để ô nhập nhận lại giá trị như trên màn, không chỉ đếm lời gọi. */
function Harness({
  rows,
  onAssumedChange,
}: {
  rows: PackagingSelectedCode[]
  onAssumedChange: (c: string, p: number | null) => void
}) {
  const [assumed, setAssumed] = useState<Record<string, number>>({})
  return (
    <PackagingImpactSelectedTable
      rows={rows}
      isLoading={false}
      isError={false}
      assumed={assumed}
      onAssumedChange={(code, price) => {
        onAssumedChange(code, price)
        setAssumed((prev) => {
          const next = { ...prev }
          if (price == null) delete next[code]
          else next[code] = price
          return next
        })
      }}
      onRemove={vi.fn()}
    />
  )
}

function renderTable(rows: PackagingSelectedCode[]) {
  const onAssumedChange = vi.fn()
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <Harness rows={rows} onAssumedChange={onAssumedChange} />
    </QueryClientProvider>,
  )
  return { onAssumedChange, user: userEvent.setup() }
}

beforeEach(() => localStorage.clear())

describe('PackagingImpactSelectedTable', () => {
  it('parses a Vietnamese-formatted assumed price ("1.234,5" -> 1234.5)', async () => {
    const { user, onAssumedChange } = renderTable([row()])
    await user.type(screen.getByLabelText('Giá giả định CPT0105'), '1.234,5')
    expect(onAssumedChange).toHaveBeenLastCalledWith('CPT0105', 1234.5)
  })

  it('clearing the cell removes the assumption instead of sending a 0 price', async () => {
    const { user, onAssumedChange } = renderTable([row()])
    const input = screen.getByLabelText('Giá giả định CPT0105')
    await user.type(input, '900')
    await user.clear(input)
    expect(onAssumedChange).toHaveBeenLastCalledWith('CPT0105', null)
  })

  it('flags an assumed price above the ceiling before the server answers', async () => {
    const { user } = renderTable([row({ floor: 800, ceiling: 1200 })])
    expect(screen.queryByText(/Vượt ngưỡng trần/)).not.toBeInTheDocument()
    await user.type(screen.getByLabelText('Giá giả định CPT0105'), '1500')
    expect(screen.getByText(/Vượt ngưỡng trần/)).toBeInTheDocument()
  })

  it('drops a stale server ceiling warning once the typed price is back inside the limits', async () => {
    //  Máy chủ đã báo vượt trần (mã 7) cho giá cũ 1.300; người dùng gõ 1.000 — chưa kịp gửi lại.
    const { user } = renderTable([row({ new: 1300, floor: 800, ceiling: 1200, warnings: [7] })])
    expect(screen.getByText(/Vượt ngưỡng trần/)).toBeInTheDocument()
    await user.type(screen.getByLabelText('Giá giả định CPT0105'), '1000')
    expect(screen.queryByText(/Vượt ngưỡng trần/)).not.toBeInTheDocument()
  })

  it('shows a real dash for a code without any price, not an empty cell', () => {
    renderTable([row({ old: null, new: null, diff: null, pct: null })])
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(4)
  })
})
