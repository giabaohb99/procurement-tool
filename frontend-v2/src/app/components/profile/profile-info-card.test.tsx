import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { AuthUser } from '@/core/auth/auth-types'
import { ProfileInfoCard } from './profile-info-card'

//  Hộp đổi mật khẩu có bài kiểm riêng; ở đây chỉ kiểm khối Hồ sơ nhân sự.
vi.mock('./change-password-dialog', () => ({ ChangePasswordDialog: () => null }))

function profile(over: Partial<AuthUser> = {}): AuthUser {
  return {
    id: 1,
    email: 'a@dego.vn',
    full_name: 'Nguyễn Văn A',
    emp_code: 'NSU001',
    company_name: 'Công ty A',
    department_name: 'Phòng Thu mua',
    position: 'Chuyên viên',
    role_name: 'Nhân viên',
    ...over,
  } as AuthUser
}

describe('ProfileInfoCard — kiêm nhiệm', () => {
  it('lists every effective concurrent role on its own line with company and position', () => {
    render(
      <ProfileInfoCard
        profile={profile({
          kiem_nhiem: ['Phòng Kế toán — Công ty B (Phó phòng)', 'Phòng Nhân sự — Công ty C'],
        })}
      />,
    )
    expect(screen.getByText('Phòng Kế toán — Công ty B (Phó phòng)')).toBeInTheDocument()
    expect(screen.getByText('Phòng Nhân sự — Công ty C')).toBeInTheDocument()
    //  Hai câu nằm ở hai phần tử riêng, không bị nối thành một chuỗi cắt bằng dấu phẩy.
    expect(screen.queryByText(/Phó phòng\), Phòng Nhân sự/)).not.toBeInTheDocument()
  })

  it('says "Chưa cập nhật" when nobody concurrent, and survives a session saved before the field existed', () => {
    const { rerender } = render(<ProfileInfoCard profile={profile({ kiem_nhiem: [] })} />)
    const label = screen.getByText('Kiêm nhiệm')
    expect(label.closest('div')?.parentElement?.textContent).toContain('Chưa cập nhật')

    rerender(<ProfileInfoCard profile={profile({ kiem_nhiem: undefined })} />)
    expect(screen.getByText('Kiêm nhiệm').closest('div')?.parentElement?.textContent).toContain('Chưa cập nhật')
  })

  it('renders two identical sentences without a React key clash (same place listed twice)', () => {
    render(<ProfileInfoCard profile={profile({ kiem_nhiem: ['Phòng X — Công ty B', 'Phòng X — Công ty B'] })} />)
    expect(screen.getAllByText('Phòng X — Công ty B')).toHaveLength(2)
  })
})
