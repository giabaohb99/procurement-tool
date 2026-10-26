import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { assistantApi } from '../api/assistant-api'
import type { ApprovalProposal } from '../types/assistant'
import { ApprovalProposalCard } from './approval-proposal-card'

/**
 * Thẻ xác nhận duyệt / từ chối qua Trợ lý web (kh-AI2-7) — tầng GHI có xác nhận.
 *
 * Chỗ dễ lủng:
 * - Nút phải nói đúng việc: đề xuất TỪ CHỐI mà nút ghi «Xác nhận duyệt» là người dùng duyệt nhầm.
 * - Bấm đúp ra hai lượt duyệt (chặng 1 rồi chặng 2 nếu người đó duyệt cả hai) — chặn bằng ref, không chỉ `disabled`.
 * - Phiếu đổi trạng thái từ lúc đề xuất (409): token cũ vô dụng, thẻ phải bảo hỏi lại AI và gỡ nút xác nhận.
 * - Không có nút duyệt hàng loạt: một thẻ một phiếu.
 */

vi.mock('../api/assistant-api', () => ({
  assistantApi: { confirmApproval: vi.fn() },
}))

const confirmMock = vi.mocked(assistantApi.confirmApproval)

const approve: ApprovalProposal = {
  kind: 'approval_proposal',
  action: 'approve',
  entity: 'vehicle_booking',
  entity_label: 'Phiếu đặt xe',
  code: 'DX00031',
  summary: [
    { label: 'Mã', value: 'DX00031' },
    { label: 'Người đặt', value: 'Trần Văn A' },
    { label: 'Mục đích', value: 'Đi gặp khách' },
  ],
  note: '',
  step: 'chặng 1',
  confirm_token: 'tok',
  url: '/hr/vehicle-bookings/31',
}

const reject: ApprovalProposal = { ...approve, action: 'reject', note: 'Trùng lịch xe' }

function build(proposal: ApprovalProposal, onDismiss = vi.fn()) {
  render(
    <MemoryRouter>
      <ApprovalProposalCard proposal={proposal} onDismiss={onDismiss} />
    </MemoryRouter>,
  )
  return { onDismiss }
}

function conflict() {
  return Object.assign(new Error('Request failed with status code 409'), {
    isAxiosError: true,
    response: { status: 409, data: { success: false, error: { code: 'CONFLICT', message: 'Phiếu đã đổi trạng thái' } } },
  })
}

beforeEach(() => {
  confirmMock.mockReset()
})

describe('ApprovalProposalCard', () => {
  it('shows the document summary and an approve button, saying nothing is approved yet', () => {
    build(approve)

    expect(screen.getByText(/Đề xuất duyệt Phiếu đặt xe DX00031/)).toBeInTheDocument()
    expect(screen.getByText('Trần Văn A')).toBeInTheDocument()
    expect(screen.getByText('Đi gặp khách')).toBeInTheDocument()
    expect(screen.getByText(/chặng 1/)).toBeInTheDocument()
    expect(screen.getByText(/chưa được duyệt/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Xác nhận duyệt/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Xác nhận từ chối/ })).not.toBeInTheDocument()
    //  Một thẻ một phiếu: đúng hai nút, không có nút nào khác (duyệt tất cả…).
    expect(screen.getAllByRole('button')).toHaveLength(2)
  })

  it('a reject proposal says reject on the button and shows the reason', () => {
    build(reject)

    expect(screen.getByText(/Đề xuất từ chối Phiếu đặt xe DX00031/)).toBeInTheDocument()
    expect(screen.getByText('Trùng lịch xe')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Xác nhận từ chối/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Xác nhận duyệt/ })).not.toBeInTheDocument()
  })

  it('confirms once with the token even on a double click, then reports the decision with a link', async () => {
    let resolve: (v: Awaited<ReturnType<typeof assistantApi.confirmApproval>>) => void = () => {}
    confirmMock.mockImplementation(() => new Promise((r) => (resolve = r)))
    build(approve)

    const button = screen.getByRole('button', { name: /Xác nhận duyệt/ })
    await userEvent.dblClick(button)
    expect(confirmMock).toHaveBeenCalledTimes(1)
    expect(confirmMock).toHaveBeenCalledWith('tok')

    resolve({ entity: 'vehicle_booking', entity_label: 'Phiếu đặt xe', code: 'DX00031', approved: true,
      updated_fields: ['Đã duyệt qua AI'], url: '/hr/vehicle-bookings/31' })
    expect(await screen.findByText(/Đã duyệt Phiếu đặt xe DX00031/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mở phiếu' })).toBeInTheDocument()
  })

  it('reports a rejection as rejected, not approved', async () => {
    confirmMock.mockResolvedValue({ entity: 'vehicle_booking', entity_label: 'Phiếu đặt xe', code: 'DX00031',
      approved: false, updated_fields: ['Đã từ chối qua AI'], url: '/hr/vehicle-bookings/31' })
    build(reject)

    await userEvent.click(screen.getByRole('button', { name: /Xác nhận từ chối/ }))
    expect(await screen.findByText(/Đã từ chối Phiếu đặt xe DX00031/)).toBeInTheDocument()
  })

  it('on 409 says the document changed, asks to ask the AI again, and drops the confirm button', async () => {
    confirmMock.mockRejectedValue(conflict())
    build(approve)

    await userEvent.click(screen.getByRole('button', { name: /Xác nhận duyệt/ }))
    expect(await screen.findByText(/Phiếu đã thay đổi, hỏi lại AI/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Xác nhận duyệt/ })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Bỏ qua/ })).toBeInTheDocument()
  })

  it('on another error shows the server message and lets the user try again', async () => {
    confirmMock.mockRejectedValueOnce(
      Object.assign(new Error('x'), {
        isAxiosError: true,
        response: { status: 400, data: { success: false, error: { code: 'BAD', message: 'Đề xuất đã hết hạn' } } },
      }),
    )
    build(approve)

    await userEvent.click(screen.getByRole('button', { name: /Xác nhận duyệt/ }))
    expect(await screen.findByText('Đề xuất đã hết hạn')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Xác nhận duyệt/ })).toBeEnabled()
  })

  it('Bỏ qua dismisses without calling the server', async () => {
    const { onDismiss } = build(approve)

    await userEvent.click(screen.getByRole('button', { name: /Bỏ qua/ }))
    expect(onDismiss).toHaveBeenCalledTimes(1)
    expect(confirmMock).not.toHaveBeenCalled()
  })
})
