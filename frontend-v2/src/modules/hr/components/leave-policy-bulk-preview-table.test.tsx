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
