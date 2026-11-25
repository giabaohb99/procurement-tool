import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { MemoryRouter } from 'react-router-dom'
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
    //  Ô mã là liên kết sang Lịch sử mua hàng nên cần ngữ cảnh router.
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <Harness rows={rows} onAssumedChange={onAssumedChange} />
      </QueryClientProvider>
    </MemoryRouter>,
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

  it('has no floor-ceiling column any more and never invents a limit warning from the typed price', async () => {
    //  Ngưỡng sàn / trần đã bỏ ở phase 04: giá giả định cao đến đâu ghi chú cũng chỉ là cảnh báo máy chủ gửi.
    const { user } = renderTable([row({ warnings: [] })])
    expect(screen.queryByRole('columnheader', { name: /Sàn/ })).not.toBeInTheDocument()
    await user.type(screen.getByLabelText('Giá giả định CPT0105'), '1500000')
    expect(screen.queryByText(/ngưỡng/i)).not.toBeInTheDocument()
  })

  it('shows the warnings the server sent in the note cell', () => {
    renderTable([row({ warnings: [5] })])
    expect(screen.getByText('ĐVT mua khác ĐVT danh mục')).toBeInTheDocument()
  })

  it('shows a real dash for a code without any price, not an empty cell', () => {
    renderTable([row({ old: null, new: null, diff: null, pct: null })])
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(4)
  })
})

/** duoc-CR-784 — chip lọc nhóm của bảng mã đã chọn. */
describe('PackagingImpactSelectedTable group chips', () => {
  const MIX = [
    row({ code: 'CPT1', group: 'Chai' }),
    row({ code: 'CPT2', group: 'Chai' }),
    row({ code: 'NAP1', group: 'Nắp' }),
    row({ code: 'NHT1', group: 'Nhãn thùng' }),
  ]

  function renderMix(rows: PackagingSelectedCode[]) {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const ui = (list: PackagingSelectedCode[]) => (
      <MemoryRouter>
        <QueryClientProvider client={client}>
          <Harness rows={list} onAssumedChange={vi.fn()} />
        </QueryClientProvider>
      </MemoryRouter>
    )
    const view = render(ui(rows))
    return { ...view, rerenderRows: (list: PackagingSelectedCode[]) => view.rerender(ui(list)), user: userEvent.setup() }
  }

  it('shows only the groups present, with counts, in role order', () => {
    renderMix([...MIX].reverse())
    const chips = within(screen.getByRole('group', { name: 'Lọc mã đã chọn theo nhóm' })).getAllByRole('button')
    expect(chips.map((chip) => chip.textContent)).toEqual(['Tất cả (4)', 'Chai (2)', 'Nắp (1)', 'Nhãn thùng (1)'])
  })

  it('hides rows of other groups without touching the selection, and "Tất cả" brings them back', async () => {
    const { user } = renderMix(MIX)
    await user.click(screen.getByRole('button', { name: 'Nắp (1)' }))
    expect(screen.getByText('NAP1')).toBeInTheDocument()
    expect(screen.queryByText('CPT1')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Nắp (1)' })).toHaveAttribute('aria-pressed', 'true')
    await user.click(screen.getByRole('button', { name: 'Tất cả (4)' }))
    expect(screen.getByText('CPT1')).toBeInTheDocument()
  })

  it('falls back to "Tất cả" when the chosen group disappears from the selection', async () => {
    const { user, rerenderRows } = renderMix(MIX)
    await user.click(screen.getByRole('button', { name: 'Nắp (1)' }))
    rerenderRows(MIX.filter((item) => item.group !== 'Nắp'))
    expect(screen.getByText('CPT1')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tất cả (3)' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('offers no chips when there is a single group (nothing to filter)', () => {
    renderMix([row({ code: 'CPT1' }), row({ code: 'CPT2' })])
    expect(screen.queryByRole('group', { name: 'Lọc mã đã chọn theo nhóm' })).not.toBeInTheDocument()
  })
})
