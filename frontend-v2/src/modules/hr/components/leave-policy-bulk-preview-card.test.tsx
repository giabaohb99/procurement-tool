import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { PolicyPreviewItem } from '../types/leave-policy'
import { buildLeaveTypeNameLookup } from '../utils/leave-policy-display'
import { LeavePolicyBulkPreviewCard } from './leave-policy-bulk-preview-card'

const typeName = buildLeaveTypeNameLookup([
  { id: 1, name: 'Phép năm' },
  { id: 2, name: 'Nghỉ ốm' },
])

function item(overrides: Partial<PolicyPreviewItem> = {}): PolicyPreviewItem {
  return {
    employee_id: 9,
    code: 'NSU009',
    name: 'Lê Văn Cường',
    department_name: 'Kinh doanh',
    hire_date: '2024-03-15',
    current: { policy_name: 'Gói cơ bản', from: '2026-01-01', to: null },
    conflict: null,
    conflict_message: '',
    changes: [
      { leave_type_id: 1, before: 12, after: 14.5 },
      { leave_type_id: 2, before: 30, after: 30 },
    ],
    ...overrides,
  }
}

function renderCard(overrides: Partial<PolicyPreviewItem> = {}, checked = false) {
  const onToggle = vi.fn()
  render(<LeavePolicyBulkPreviewCard item={item(overrides)} checked={checked} onToggle={onToggle} typeName={typeName} />)
  return onToggle
}

describe('LeavePolicyBulkPreviewCard', () => {
  it('shows who, the code underneath, department, hire date and the current policy', () => {
    renderCard()
    expect(screen.getByText('Lê Văn Cường')).toBeInTheDocument()
    expect(screen.getByText('NSU009')).toBeInTheDocument()
    expect(screen.getByText(/Kinh doanh/)).toBeInTheDocument()
    expect(screen.getByText('Vào làm 15/03/2024')).toBeInTheDocument()
    expect(screen.getByText('Gói cơ bản (01/01/2026 → Không thời hạn)')).toBeInTheDocument()
  })

  it('keeps the before -> after comparison, listing only types whose quota moves', () => {
    renderCard()
    expect(screen.getByText('Hiện tại → Sau phân bổ')).toBeInTheDocument()
    expect(screen.getByText('Phép năm')).toBeInTheDocument()
    expect(screen.getByText('14,5')).toBeInTheDocument()
    //  Loại không đổi hạn mức không kê — cùng luật với ô "Thay đổi quỹ năm nay" của bảng.
    expect(screen.queryByText('Nghỉ ốm')).not.toBeInTheDocument()
  })

  it('says nothing changes when no quota moves, instead of an empty comparison table', () => {
    renderCard({ changes: [{ leave_type_id: 1, before: 12, after: 12 }] })
    expect(screen.getByText('Quỹ năm nay: Không đổi')).toBeInTheDocument()
    expect(screen.queryByText('Hiện tại → Sau phân bổ')).not.toBeInTheDocument()
  })

  it('toggles from the checkbox and from tapping the name', () => {
    const onToggle = renderCard()
    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn Lê Văn Cường' }))
    fireEvent.click(screen.getByText('Lê Văn Cường'))
    expect(onToggle).toHaveBeenCalledTimes(2)
    expect(onToggle).toHaveBeenCalledWith(9)
  })

  it('locks a blocked row, never shows it as ticked, and explains why in words', () => {
    const onToggle = renderCard(
      { conflict: 'overlap', conflict_message: 'Chồng ngày với phân bổ đang có.' },
      true,
    )
    const box = screen.getByRole('checkbox', { name: 'Chọn Lê Văn Cường' })
    expect(box).toBeDisabled()
    expect(box).not.toBeChecked()
    fireEvent.click(box)
    expect(onToggle).not.toHaveBeenCalled()
    expect(screen.getByText('Chồng ngày với phân bổ đang có.')).toBeInTheDocument()
    expect(screen.queryByText('Hiện tại → Sau phân bổ')).not.toBeInTheDocument()
  })

  it('names the self-assignment block even though the backend sends no message for it', () => {
    renderCard({ conflict: 'self', conflict_message: '' })
    expect(screen.getByText('Không tự phân bổ chính sách cho chính mình.')).toBeInTheDocument()
  })

  it('out-of-scope rows (empty name and code) still say who it is and hide the current policy', () => {
    renderCard({ conflict: 'scope', name: '', code: '', department_name: '', hire_date: null, current: null, conflict_message: 'Ngoài phạm vi.' })
    expect(screen.getByText('Nhân sự #9')).toBeInTheDocument()
    expect(screen.queryByText(/Hiện tại:/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Vào làm/)).not.toBeInTheDocument()
  })
})
