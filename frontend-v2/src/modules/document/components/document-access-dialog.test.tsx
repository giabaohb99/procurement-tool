import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { EFFECT, SUBJECT_KIND, type DocumentAccessDraft } from '../types/document-access'
import { DocumentAccessDialog } from './document-access-dialog'

vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { employee_id: 5, department_id: 2, company_id: 1 } }),
}))
vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({
    data: {
      items: [
        { id: 97, full_name: 'Lý Phó Phòng' },
        { id: 5, full_name: 'Tôi Đang Đăng Nhập' },
      ],
    },
  }),
}))
vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({ data: { items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-roles', () => ({ useRoles: () => ({ data: [] }) }))

function row(doi: Partial<DocumentAccessDraft['values']> = {}): DocumentAccessDraft {
  return {
    subjectLabel: 'Lý Phó Phòng',
    values: {
      subject_kind: SUBJECT_KIND.employee,
      subject_id: 97,
      effect: EFFECT.allow,
      can_read: true,
      can_write: false,
      can_delete: false,
      valid_from: null,
      valid_to: null,
      reason: '',
      ...doi,
    },
  }
}

describe('DocumentAccessDialog', () => {
  //  Trang chi tiết trước 25/08/2026 chỉ có nút THU HỒI: muốn nâng một người từ
  //  «xem» lên «xem · sửa» phải thu hồi rồi chia lại, đổi lấy một dòng đỏ trong
  //  nhật ký cho một việc không phải thu hồi.
  it('mở ở chế độ SỬA thì nạp sẵn đối tượng, bộ quyền và lý do đang có', () => {
    render(
      <DocumentAccessDialog
        open
        onOpenChange={vi.fn()}
        initial={row({ can_write: true, reason: 'Phối hợp rà soát quy chế' })}
        onSubmit={vi.fn()}
      />,
    )

    expect(screen.getByText('Sửa quyền truy cập')).toBeInTheDocument()
    //  Tên hiện ngay trên ô chọn, và chip bên dưới — mở ra là thấy đang sửa ai.
    expect(screen.getAllByText('Lý Phó Phòng').length).toBeGreaterThan(0)
    expect(screen.getByRole('checkbox', { name: /Sửa/ })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: /Xóa/ })).not.toBeChecked()
    expect(screen.getByLabelText('Lý do')).toHaveValue('Phối hợp rà soát quy chế')
    //  Sửa MỘT dòng thì không mời gom thêm cụm khác vào cùng lượt.
    expect(screen.queryByRole('button', { name: /Thêm cụm/ })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Lưu' })).toBeInTheDocument()
  })

  it('khai mới thì mở ra trắng, nút chốt là «Xong»', () => {
    render(<DocumentAccessDialog open onOpenChange={vi.fn()} onSubmit={vi.fn()} />)

    expect(screen.getByText('Chia quyền truy cập')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /Sửa/ })).not.toBeChecked()
    expect(screen.getByRole('button', { name: /Xong/ })).toBeDisabled()
  })

  //  Lỗi người dùng chỉ ra 25/08/2026: chọn chiều «Không cho phép» là băng xanh
  //  «đã bỏ … khỏi danh sách» hiện ngay giữa hộp, trong khi người dùng CHƯA
  //  chọn ai. Câu đó chỉ có nghĩa lúc mở danh sách ra tìm mà không thấy tên
  //  mình, nên nó nằm trong ô chọn chứ không phải ngoài hộp.
  it('không bày băng «tự chặn chính mình» khi chưa mở danh sách chọn', () => {
    render(
      <DocumentAccessDialog
        open
        onOpenChange={vi.fn()}
        initial={row({ effect: EFFECT.deny })}
        onSubmit={vi.fn()}
      />,
    )

    expect(screen.queryByText(/khỏi danh sách/)).not.toBeInTheDocument()
  })
})
