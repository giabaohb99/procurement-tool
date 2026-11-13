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
  it('lists every effective concurrent row on its own line, exactly the backend sentence for both kinds (duoc-CR-756)', () => {
    render(
      <ProfileInfoCard
        profile={profile({
          kiem_nhiem: ['Phòng Kế toán (Phó phòng)', 'Công ty SAM GROUP (Giám đốc)', 'Phòng Nhân sự'],
        })}
      />,
    )
    expect(screen.getByText('Phòng Kế toán (Phó phòng)')).toBeInTheDocument()
    expect(screen.getByText('Công ty SAM GROUP (Giám đốc)')).toBeInTheDocument()
    expect(screen.getByText('Phòng Nhân sự')).toBeInTheDocument()
    //  Các câu nằm ở phần tử riêng, không bị nối thành một chuỗi cắt bằng dấu phẩy.
    expect(screen.queryByText(/Phó phòng\), Công ty/)).not.toBeInTheDocument()
  })

  it('says "Chưa cập nhật" when nobody concurrent, and survives a session saved before the field existed', () => {
    const { rerender } = render(<ProfileInfoCard profile={profile({ kiem_nhiem: [] })} />)
    const label = screen.getByText('Kiêm nhiệm')
    expect(label.closest('div')?.parentElement?.textContent).toContain('Chưa cập nhật')

    rerender(<ProfileInfoCard profile={profile({ kiem_nhiem: undefined })} />)
    expect(screen.getByText('Kiêm nhiệm').closest('div')?.parentElement?.textContent).toContain('Chưa cập nhật')
  })

  it('renders two identical sentences without a React key clash (same place listed twice)', () => {
    render(<ProfileInfoCard profile={profile({ kiem_nhiem: ['Công ty B', 'Công ty B'] })} />)
    expect(screen.getAllByText('Công ty B')).toHaveLength(2)
  })
})
