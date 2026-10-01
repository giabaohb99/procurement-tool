import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { BulkDeleteButton } from './bulk-delete-button'

// bao-CR-547 — nút «Xóa đã chọn (n)»: không có gì chọn thì không dựng; xóa lỗi thì giữ hộp.
describe('BulkDeleteButton', () => {
  it('renders nothing when nothing is selected', () => {
    render(<BulkDeleteButton count={0} unitLabel="phiếu Nháp" onConfirm={vi.fn()} />)
    expect(screen.queryByRole('button', { name: /Xóa đã chọn/ })).toBeNull()
  })

  it('asks before deleting and only deletes after confirming', async () => {
    const onConfirm = vi.fn().mockResolvedValue(undefined)
    render(<BulkDeleteButton count={3} unitLabel="phiếu Nháp" onConfirm={onConfirm} />)

    await userEvent.click(screen.getByRole('button', { name: 'Xóa đã chọn (3)' }))
    expect(screen.getByText('Xóa 3 phiếu Nháp đã chọn?')).toBeInTheDocument()
    expect(onConfirm).not.toHaveBeenCalled()

    await userEvent.click(screen.getByRole('button', { name: 'Xóa 3 phiếu Nháp' }))
    expect(onConfirm).toHaveBeenCalledTimes(1)
    await waitFor(() => expect(screen.queryByText('Xóa 3 phiếu Nháp đã chọn?')).toBeNull())
  })

  it('cancel closes without deleting', async () => {
    const onConfirm = vi.fn()
    render(<BulkDeleteButton count={2} unitLabel="đơn Nháp" onConfirm={onConfirm} />)
    await userEvent.click(screen.getByRole('button', { name: 'Xóa đã chọn (2)' }))
    await userEvent.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(onConfirm).not.toHaveBeenCalled()
  })

  it('keeps the dialog open when the server refuses the batch', async () => {
    //  Backend từ chối cả lô (lọt phiếu không Nháp) — toast nói lý do, hộp giữ nguyên để đọc.
    const onConfirm = vi.fn().mockRejectedValue(new Error('400'))
    render(<BulkDeleteButton count={2} unitLabel="phiếu Nháp" onConfirm={onConfirm} />)
    await userEvent.click(screen.getByRole('button', { name: 'Xóa đã chọn (2)' }))
    await userEvent.click(screen.getByRole('button', { name: 'Xóa 2 phiếu Nháp' }))
    await waitFor(() => expect(onConfirm).toHaveBeenCalled())
    expect(screen.getByText('Xóa 2 phiếu Nháp đã chọn?')).toBeInTheDocument()
  })
})
