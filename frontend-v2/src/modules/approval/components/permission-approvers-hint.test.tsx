import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PermissionApproversHint } from './permission-approvers-hint'

const { mockUsePermissionApprovers } = vi.hoisted(() => ({
  mockUsePermissionApprovers: vi.fn(),
}))

vi.mock('../hooks/use-approvals', () => ({
  usePermissionApprovers: mockUsePermissionApprovers,
}))

describe('PermissionApproversHint', () => {
  beforeEach(() => mockUsePermissionApprovers.mockReset())

  it('asks for holders of the flow entity and names it in the rule sentence', () => {
    mockUsePermissionApprovers.mockReturnValue({ data: [], isLoading: false, isError: false })
    render(<PermissionApproversHint entity="vehicle_booking" />)
    expect(mockUsePermissionApprovers).toHaveBeenCalledWith('vehicle_booking', true)
    expect(screen.getByText('Đặt xe', { selector: 'strong' })).toBeInTheDocument()
    expect(screen.getByText('Duyệt', { selector: 'strong' }).parentElement).toHaveTextContent(
      /quyền Duyệt trên Đặt xe/,
    )
  })

  it('warns that the step will find nobody when no role holds the approve permission', () => {
    mockUsePermissionApprovers.mockReturnValue({ data: [], isLoading: false, isError: false })
    render(<PermissionApproversHint entity="vehicle_booking" />)
    expect(screen.getByText(/Chưa ai giữ quyền này/)).toBeInTheDocument()
  })

  it('lists each holder with every role and scope that grants it', () => {
    mockUsePermissionApprovers.mockReturnValue({
      isLoading: false,
      isError: false,
      data: [
        {
          employee_id: 7,
          code: 'NSU100',
          name: 'Trần Điều Phối',
          roles: [
            { role: 'Điều phối viên (Đặt xe)', scope: 'all', scope_label: 'Tất cả' },
            { role: 'Quản lý điều phối (Đặt xe)', scope: 'company', scope_label: 'Công ty' },
          ],
        },
      ],
    })
    render(<PermissionApproversHint entity="vehicle_booking" />)
    expect(screen.getByText('Hiện có 1 người giữ quyền:')).toBeInTheDocument()
    expect(screen.getByText('Trần Điều Phối')).toBeInTheDocument()
    expect(
      screen.getByText('Điều phối viên (Đặt xe) · Tất cả, Quản lý điều phối (Đặt xe) · Công ty'),
    ).toBeInTheDocument()
    expect(screen.queryByText(/Chưa ai giữ quyền này/)).not.toBeInTheDocument()
  })

  it('falls back to the raw key for an entity without a Vietnamese label', () => {
    mockUsePermissionApprovers.mockReturnValue({ data: undefined, isLoading: true, isError: false })
    render(<PermissionApproversHint entity="khoa_moi" />)
    expect(screen.getByText('khoa_moi', { selector: 'strong' })).toBeInTheDocument()
    expect(screen.getByText('Đang tải người giữ quyền…')).toBeInTheDocument()
  })

  it('says the list failed instead of pretending nobody holds the permission', () => {
    mockUsePermissionApprovers.mockReturnValue({ data: undefined, isLoading: false, isError: true })
    render(<PermissionApproversHint entity="vehicle_booking" />)
    expect(screen.getByText('Không tải được danh sách người giữ quyền.')).toBeInTheDocument()
    expect(screen.queryByText(/Chưa ai giữ quyền này/)).not.toBeInTheDocument()
  })
})
