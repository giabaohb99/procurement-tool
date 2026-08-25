import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { EFFECT, SUBJECT_KIND, type DocumentAccessDraft } from '../types/document-access'
import { AccessGroupEditDialog } from './document-access-group-dialog'

function dong(doi: Partial<DocumentAccessDraft['values']> = {}, ten = 'Lý Phó Phòng'): DocumentAccessDraft {
  return {
    subjectLabel: ten,
    values: {
      subject_kind: SUBJECT_KIND.employee,
      subject_id: 97,
      effect: EFFECT.deny,
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

describe('AccessGroupEditDialog', () => {
  //  Lỗi người dùng chỉ ra 24/08/2026: bấm «Sửa» để xem lại đã cho những ai,
  //  được làm gì, hạn tới bao giờ — hộp mở ra TRẮNG TRƠN y như khai mới, và bấm
  //  «Áp cho cả cụm» là ghi đè hết bằng giá trị trắng đó.
  it('mở ra là thấy ĐÚNG bộ quyền đang áp, không phải form trắng', () => {
    render(
      <AccessGroupEditDialog
        open
        onOpenChange={vi.fn()}
        deny
        rows={[dong({ can_write: true, reason: 'Phối hợp rà soát quy chế' })]}
        onApply={vi.fn()}
      />,
    )

    expect(screen.getByRole('checkbox', { name: /Sửa/ })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: /Xóa/ })).not.toBeChecked()
    expect(screen.getByDisplayValue('Phối hợp rà soát quy chế')).toBeVisible()
  })

  it('hiện luôn ĐANG ÁP CHO AI — con số "3 đối tượng" không đủ để rà lại trước khi ghi đè', () => {
    render(
      <AccessGroupEditDialog
        open
        onOpenChange={vi.fn()}
        deny
        rows={[dong({}, 'Lý Phó Phòng'), dong({ subject_id: 98 }, 'Hồ Quyền Trưởng Phòng')]}
        onApply={vi.fn()}
      />,
    )

    expect(screen.getByText('Đang áp cho')).toBeVisible()
    expect(screen.getByText('Lý Phó Phòng')).toBeVisible()
    expect(screen.getByText('Hồ Quyền Trưởng Phòng')).toBeVisible()
    expect(screen.getByText(/Áp cho cả 2 đối tượng/)).toBeVisible()
  })

  it('gọi cụm là «không cho phép», cùng một chữ với nút chọn và tên cụm bên ngoài', () => {
    render(
      <AccessGroupEditDialog open onOpenChange={vi.fn()} deny rows={[dong()]} onApply={vi.fn()} />,
    )
    expect(screen.getByText('Sửa quyền cụm không cho phép')).toBeVisible()
  })
})
