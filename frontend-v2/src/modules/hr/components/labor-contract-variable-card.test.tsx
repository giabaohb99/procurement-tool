import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import {
  VARIABLE_SOURCE_CUSTOM,
  VARIABLE_SOURCE_SYSTEM,
  VARIABLE_TYPE_MONEY,
  type LaborContractVariable,
} from '../types/labor-contract-variable'
import { LaborContractVariableCard } from './labor-contract-variable-card'

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

function variable(overrides: Partial<LaborContractVariable> = {}): LaborContractVariable {
  return {
    id: 3, code: 'phu_cap_xang', source: VARIABLE_SOURCE_CUSTOM, value_type: VARIABLE_TYPE_MONEY,
    label: 'Phụ cấp xăng', description: '', example: '500.000', default_value: '', is_required: true,
    is_active: true, is_hidden: false, sort_order: 0, template_count: 2, group: 'Lương & phụ cấp',
    created_at: null, created_by_name: '', ...overrides,
  }
}

function actions(canManage = true, canDelete = true) {
  return { canManage, canDelete, onEdit: vi.fn(), onToggleActive: vi.fn(), onToggleHidden: vi.fn(), onDelete: vi.fn() }
}

describe('LaborContractVariableCard', () => {
  it('tên lên đầu, mã {{ }} kèm nút chép, nhóm · kiểu, bắt buộc, ví dụ, số mẫu dùng', () => {
    render(<LaborContractVariableCard variable={variable()} actions={actions()} />)
    expect(screen.getByText('Phụ cấp xăng')).toBeInTheDocument()
    expect(screen.getByText('{{ phu_cap_xang }}')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Chép biến Phụ cấp xăng: {{ phu_cap_xang }}' })).toBeInTheDocument()
    expect(screen.getByText('Lương & phụ cấp · Tiền')).toBeInTheDocument()
    expect(screen.getByText('Bắt buộc')).toBeInTheDocument()
    expect(screen.getByText('Ví dụ: 500.000')).toBeInTheDocument()
    expect(screen.getByText('Dùng trong 2 mẫu')).toBeInTheDocument()
  })

  it('biến hệ thống: không có kiểu / bắt buộc (như bảng), huy hiệu chỉ hiện khi bị Ẩn', () => {
    const sys = variable({ source: VARIABLE_SOURCE_SYSTEM, code: 'ho_ten', label: 'Họ tên', group: 'Nhân sự' })
    const { unmount } = render(<LaborContractVariableCard variable={sys} actions={actions()} />)
    expect(screen.getByText('Nhân sự')).toBeInTheDocument()
    expect(screen.queryByText('Bắt buộc')).toBeNull()
    expect(screen.queryByText('Đang dùng')).toBeNull()
    unmount()
    render(<LaborContractVariableCard variable={{ ...sys, is_hidden: true }} actions={actions()} />)
    expect(screen.getByText('Ẩn')).toBeInTheDocument()
  })

  it('biến tùy chỉnh ngừng dùng thì có huy hiệu "Ngừng"', () => {
    render(<LaborContractVariableCard variable={variable({ is_active: false })} actions={actions()} />)
    expect(screen.getByText('Ngừng')).toBeInTheDocument()
  })

  it('chỉ có quyền đọc: còn nút chép, không có nút thao tác nào khác', () => {
    render(<LaborContractVariableCard variable={variable()} actions={actions(false, false)} />)
    expect(screen.getAllByRole('button')).toHaveLength(1)
  })

  it('có quyền: nút Xóa trên thẻ gọi đúng hàm của bảng', async () => {
    const a = actions()
    render(<LaborContractVariableCard variable={variable()} actions={a} />)
    await userEvent.click(screen.getByRole('button', { name: 'Xóa biến phu_cap_xang' }))
    expect(a.onDelete).toHaveBeenCalledTimes(1)
  })
})
