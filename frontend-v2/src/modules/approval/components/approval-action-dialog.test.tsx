import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { ApprovalActionDialog } from './approval-action-dialog'
import type { MyTask } from '../types/approval'

//  Hộp thoại gọi mutation qua TanStack Query — thay bằng hàm giả để bài kiểm chỉ
//  nói về HÀNH VI của hộp thoại, không nói về mạng.
const mutate = vi.fn()
vi.mock('../hooks/use-approvals', () => ({
  useApprovalAction: () => ({ mutate, isPending: false }),
}))

const VIEC: MyTask = {
  id: 1,
  instance_id: 7,
  node_seq: 1,
  node_name: 'Trưởng bộ phận duyệt',
  order_no: 1,
  assignee_employee_id: 4,
  assignee_name: 'Trưởng bộ phận (Demo)',
  status: 2,
  status_label: 'Đang chờ',
  due_at: null,
  decided_at: null,
  entity: 'document',
  entity_id: 196,
  entity_code: '',
  entity_title: 'Tờ trình phê duyệt kế hoạch số hóa',
  started_by_name: 'Quản trị viên',
  instance_status: 1,
  on_behalf_of_id: null,
  on_behalf_of_name: '',
  delegation_id: null,
  is_overdue: false,
}

function mo() {
  return render(
    <MemoryRouter>
      <ApprovalActionDialog task={VIEC} open onOpenChange={vi.fn()} />
    </MemoryRouter>,
  )
}

describe('ApprovalActionDialog', () => {
  it('chỉ có MỘT nút xác nhận, và nhãn của nó đổi theo việc đang chọn', async () => {
    //  Bản cũ bày bốn việc thành bốn cái NÚT, nên thẻ «Duyệt» đang chọn trông y
    //  hệt nút «Duyệt» ở chân hộp thoại: một hộp thoại có hai nút xanh cùng tên,
    //  người dùng không biết cái nào mới thật sự ký.
    const user = userEvent.setup()
    mo()

    expect(screen.getByRole('button', { name: 'Duyệt phiếu' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Duyệt' })).not.toBeInTheDocument()

    await user.click(screen.getByRole('radio', { name: /Trả lại/ }))

    expect(screen.getByRole('button', { name: 'Trả lại người nộp' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Duyệt phiếu' })).not.toBeInTheDocument()
  })

  it('mỗi việc tự mang câu hậu quả của nó — từ chối khác trả lại', () => {
    //  Gộp hai việc này làm một là người duyệt bấm nhầm và người nộp mất cả phiếu.
    mo()

    expect(screen.getByText('Phiếu dừng hẳn — phải làm phiếu mới.')).toBeInTheDocument()
    expect(
      screen.getByText('Phiếu còn sống — người nộp sửa rồi gửi lại.'),
    ).toBeInTheDocument()
  })

  it('từ chối mà chưa nêu lý do thì khóa nút và nói rõ vì sao', async () => {
    const user = userEvent.setup()
    mo()

    await user.click(screen.getByRole('radio', { name: /Từ chối/ }))
    const nut = screen.getByRole('button', { name: 'Từ chối phiếu' })

    expect(nut).toBeDisabled()
    expect(screen.getByText(/Phải nêu lý do/)).toBeInTheDocument()

    await user.type(screen.getByLabelText(/Lý do/), 'Thiếu căn cứ pháp lý')

    expect(nut).toBeEnabled()
  })

  it('duyệt thì không bắt nhập ý kiến', () => {
    mo()

    expect(screen.getByRole('button', { name: 'Duyệt phiếu' })).toBeEnabled()
    expect(screen.getByText(/không bắt buộc/)).toBeInTheDocument()
  })
})
