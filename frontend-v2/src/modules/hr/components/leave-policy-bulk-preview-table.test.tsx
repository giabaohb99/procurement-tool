import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { PolicyPreviewItem } from '../types/leave-policy'
import { buildLeaveTypeNameLookup } from '../utils/leave-policy-display'
import { LeavePolicyBulkPreviewTable } from './leave-policy-bulk-preview-table'

function item(id: number, overrides: Partial<PolicyPreviewItem> = {}): PolicyPreviewItem {
  return {
    employee_id: id,
    code: `NSU00${id}`,
    name: `Người ${id}`,
    department_name: 'Kinh doanh',
    hire_date: null,
    current: null,
    conflict: null,
    conflict_message: '',
    changes: [],
    ...overrides,
  }
}

/**
 * Khổ điện thoại: `setup.ts` cố định `matchMedia` ở khổ desktop, nên ở đây nói rõ ra là đang kiểm bản thẻ.
 */
function renderMobile(items: PolicyPreviewItem[], selected: number[] = []) {
  vi.stubGlobal('matchMedia', (q: string) => ({
    matches: true,
    media: q,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }))
  const onToggle = vi.fn()
  const onToggleAll = vi.fn()
  render(
    <QueryClientProvider client={new QueryClient()}>
      <LeavePolicyBulkPreviewTable
        items={items}
        selectedIds={new Set(selected)}
        onToggle={onToggle}
        onToggleAll={onToggleAll}
        typeName={buildLeaveTypeNameLookup([])}
      />
    </QueryClientProvider>,
  )
  return { onToggle, onToggleAll }
}

describe('LeavePolicyBulkPreviewTable — khổ điện thoại', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('turns rows into cards and keeps a select-all control, since the header checkbox is gone', () => {
    const { onToggleAll } = renderMobile([
      item(1),
      item(2),
      item(3, { conflict: 'overlap', conflict_message: 'Chồng ngày.' }),
    ])
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    const all = screen.getByRole('checkbox', { name: 'Chọn tất cả người phân bổ được (2)' })
    fireEvent.click(all)
    expect(onToggleAll).toHaveBeenCalledTimes(1)
  })

  it('shows select-all as partly ticked when only some selectable people are chosen', () => {
    renderMobile([item(1), item(2)], [1])
    expect(screen.getByRole('checkbox', { name: /Chọn tất cả/ })).toHaveAttribute(
      'data-state',
      'indeterminate',
    )
  })

  it('ticks a single person from the card', () => {
    const { onToggle } = renderMobile([item(1), item(2)])
    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn Người 2' }))
    expect(onToggle).toHaveBeenCalledWith(2)
  })

  it('hides select-all when nobody can be assigned', () => {
    renderMobile([item(1, { conflict: 'self' })])
    expect(screen.queryByRole('checkbox', { name: /Chọn tất cả/ })).not.toBeInTheDocument()
  })
})

describe('LeavePolicyBulkPreviewTable — xếp cột (duoc-CR-748)', () => {
  function renderDesktop(items: PolicyPreviewItem[], selected: number[] = []) {
    const onToggle = vi.fn()
    render(
      <QueryClientProvider client={new QueryClient()}>
        <LeavePolicyBulkPreviewTable
          items={items}
          selectedIds={new Set(selected)}
          onToggle={onToggle}
          onToggleAll={vi.fn()}
          typeName={buildLeaveTypeNameLookup([])}
        />
      </QueryClientProvider>,
    )
    return { onToggle }
  }

  function renderedNames() {
    return screen.getAllByRole('checkbox', { name: /^Chọn (?!tất cả)/ }).map((el) => el.getAttribute('aria-label'))
  }

  it('reorders by name (Vietnamese) in the browser and back to the preview order on the third click', () => {
    renderDesktop([item(1, { name: 'Đặng Hà' }), item(2, { name: 'Bùi An' }), item(3, { name: 'An Bình' })])
    const nameHeader = screen.getByText('Tên', { selector: 'thead span' })
    fireEvent.click(nameHeader)
    expect(renderedNames()).toEqual(['Chọn An Bình', 'Chọn Bùi An', 'Chọn Đặng Hà'])
    fireEvent.click(nameHeader)
    expect(renderedNames()).toEqual(['Chọn Đặng Hà', 'Chọn Bùi An', 'Chọn An Bình'])
    fireEvent.click(nameHeader)
    expect(renderedNames()).toEqual(['Chọn Đặng Hà', 'Chọn Bùi An', 'Chọn An Bình'])
  })

  it('keeps each tick on the SAME person after sorting, and a click still toggles that person', () => {
    //  Ô tick đi theo `employee_id`: xếp lại mà ô đi theo vị trí dòng là phân bổ nhầm người.
    const { onToggle } = renderDesktop([item(1, { name: 'Cường' }), item(2, { name: 'An' })], [1])
    fireEvent.click(screen.getByText('Tên', { selector: 'thead span' }))
    expect(renderedNames()).toEqual(['Chọn An', 'Chọn Cường'])
    expect(screen.getByRole('checkbox', { name: 'Chọn Cường' })).toHaveAttribute('data-state', 'checked')
    expect(screen.getByRole('checkbox', { name: 'Chọn An' })).toHaveAttribute('data-state', 'unchecked')
    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn An' }))
    expect(onToggle).toHaveBeenCalledWith(2)
  })

  it('puts people without a current policy ("Chưa có") at the end in both directions', () => {
    renderDesktop([
      item(1, { name: 'Không gói' }),
      item(2, { name: 'Gói B', current: { policy_name: 'Văn phòng', from: '2026-01-01', to: null } }),
      item(3, { name: 'Gói A', current: { policy_name: 'Ca kíp', from: '2026-01-01', to: null } }),
    ])
    const currentHeader = screen.getByText('Chính sách hiện tại', { selector: 'thead span' })
    fireEvent.click(currentHeader)
    expect(renderedNames()).toEqual(['Chọn Gói A', 'Chọn Gói B', 'Chọn Không gói'])
    fireEvent.click(currentHeader)
    expect(renderedNames()).toEqual(['Chọn Gói B', 'Chọn Gói A', 'Chọn Không gói'])
  })
})
