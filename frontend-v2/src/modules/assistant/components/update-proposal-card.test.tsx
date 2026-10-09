import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { assistantApi } from '../api/assistant-api'
import type { UpdateProposal } from '../types/assistant'
import { UpdateProposalCard } from './update-proposal-card'

//  Chặn gọi API thật: mock ở tầng api của module (không mock axios).
vi.mock('../api/assistant-api', () => ({
  assistantApi: { confirmUpdate: vi.fn() },
}))

const confirmMock = vi.mocked(assistantApi.confirmUpdate)

const base: UpdateProposal = {
  kind: 'update_proposal',
  entity: 'purchase_request',
  entity_label: 'Yêu cầu mua hàng (YCMH)',
  code: 'YCMH00012',
  doc_status_label: 'Nháp',
  changes: [{ field: 'purpose', label: 'Mục đích', old: 'Mua giấy A4', new: 'Mua giấy A5' }],
  confirm_token: 'tok',
  url: '/procurement/purchase-requests/12',
}

function build(proposal: UpdateProposal) {
  render(
    <MemoryRouter>
      <UpdateProposalCard proposal={proposal} onDismiss={vi.fn()} />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  confirmMock.mockReset()
})

describe('UpdateProposalCard', () => {
  it('a delete proposal says delete on the button, not edit', () => {
    //  AI-0006: thẻ xóa đi chung thẻ sửa — nút ghi "Xác nhận sửa" thì người dùng
    //  tưởng chỉ đổi một trường, bấm xong mất cả phiếu.
    build({ ...base, action: 'delete', changes: [] })

    expect(screen.getByRole('button', { name: /Xác nhận xóa/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Xác nhận sửa/ })).not.toBeInTheDocument()
    expect(screen.getByText(/Phiếu chưa bị xóa/)).toBeInTheDocument()
  })

  it('an edit proposal keeps the edit wording and the old/new list', () => {
    build(base)

    expect(screen.getByRole('button', { name: /Xác nhận sửa/ })).toBeInTheDocument()
    expect(screen.getByText('Mua giấy A5')).toBeInTheDocument()
  })

  it('after a confirmed delete it offers no link to the deleted document', async () => {
    confirmMock.mockResolvedValue({
      entity: 'purchase_request',
      entity_label: 'Yêu cầu mua hàng (YCMH)',
      code: 'YCMH00012',
      updated_fields: ['Đã xóa phiếu'],
      deleted: true,
      url: '',
    })
    const nguoi = userEvent.setup()
    build({ ...base, action: 'delete', changes: [] })

    await nguoi.click(screen.getByRole('button', { name: /Xác nhận xóa/ }))

    expect(await screen.findByText(/Đã xóa Yêu cầu mua hàng/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Mở phiếu' })).not.toBeInTheDocument()
    expect(confirmMock).toHaveBeenCalledWith('tok')
  })

  it('a failed confirm keeps the card so the user can read it again', async () => {
    confirmMock.mockRejectedValue(new Error('hết hạn'))
    const nguoi = userEvent.setup()
    build({ ...base, action: 'delete', changes: [] })

    await nguoi.click(screen.getByRole('button', { name: /Xác nhận xóa/ }))

    expect(await screen.findByRole('button', { name: /Xác nhận xóa/ })).toBeEnabled()
    expect(screen.queryByText(/Đã xóa/)).not.toBeInTheDocument()
  })
})
