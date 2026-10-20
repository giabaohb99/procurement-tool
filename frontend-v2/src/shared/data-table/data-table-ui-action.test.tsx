import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { UI_ACTION_CODE } from '@/core/telemetry/ui-event-codes'

import { DataTablePagination } from './data-table-pagination'
import { FilterResetButton } from './filter-reset-button'
import { createSelectionColumn } from './selection-column'

//  duoc-CR-654: component dùng chung gọi đúng MÃ NÚT (không kiểm queue — đã có track-ui-action.test.ts).
const track = vi.fn()
vi.mock('@/core/telemetry/track-ui-action', () => ({ trackUiAction: (code: number) => track(code) }))

beforeEach(() => track.mockClear())

describe('DataTablePagination -> UI_ACTION', () => {
  it('bấm trang kế / số trang ghi PAGE_CHANGE', async () => {
    const onPageChange = vi.fn()
    render(
      <DataTablePagination page={1} pageSize={20} total={200} onPageChange={onPageChange}
        onPageSizeChange={vi.fn()} unitLabel="người" />,
    )
    await userEvent.click(screen.getByRole('button', { name: /trang sau/i }))
    expect(onPageChange).toHaveBeenCalledWith(2)
    expect(track).toHaveBeenCalledWith(UI_ACTION_CODE.PAGE_CHANGE)
    expect(track).toHaveBeenCalledTimes(1)
  })
})

describe('selection column -> UI_ACTION', () => {
  it('ô tick tiêu đề ghi SELECT_ALL_PAGE và vẫn gọi onToggleAllOnPage', async () => {
    const onToggleAllOnPage = vi.fn()
    const column = createSelectionColumn<{ id: number }>({
      getRowId: (r) => r.id, selectedIds: new Set(), onToggleRow: vi.fn(), onToggleAllOnPage,
      allOnPageSelected: false, someOnPageSelected: false,
    })
    render(<div>{column.headerContent}</div>)
    await userEvent.click(screen.getByRole('checkbox', { name: 'Chọn cả trang' }))
    expect(onToggleAllOnPage).toHaveBeenCalledTimes(1)
    expect(track).toHaveBeenCalledWith(UI_ACTION_CODE.SELECT_ALL_PAGE)
  })
})

describe('FilterResetButton -> UI_ACTION', () => {
  it('«Xóa lọc» ghi FILTER_RESET; không ghi gì khi chỉ render', async () => {
    const onReset = vi.fn()
    render(
      <MemoryRouter>
        <FilterResetButton active onReset={onReset} />
      </MemoryRouter>,
    )
    expect(track).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button'))
    expect(onReset).toHaveBeenCalled()
    expect(track).toHaveBeenCalledWith(UI_ACTION_CODE.FILTER_RESET)
  })
})
