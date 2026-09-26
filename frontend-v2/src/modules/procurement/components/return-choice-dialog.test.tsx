// bao-CR-498 — hộp «Trả về đâu?» trả đúng đích đã chọn và tự đóng.
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ReturnChoiceDialog } from './return-choice-dialog'

describe('ReturnChoiceDialog', () => {
  it('offers both destinations and reports the picked one', async () => {
    const onPick = vi.fn()
    const onOpenChange = vi.fn()
    render(<ReturnChoiceDialog open docLabel="yêu cầu mua hàng" onOpenChange={onOpenChange} onPick={onPick} />)

    expect(screen.getByRole('heading', { name: /trả yêu cầu mua hàng về đâu/i })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /trả phòng lập tự xử lý/i }))
    expect(onPick).toHaveBeenCalledWith('department')
    expect(onOpenChange).toHaveBeenCalledWith(false)

    await userEvent.click(screen.getByRole('button', { name: /trả người lập sửa lại/i }))
    expect(onPick).toHaveBeenLastCalledWith('requester')
  })

  it('cancel closes without picking', async () => {
    const onPick = vi.fn()
    const onOpenChange = vi.fn()
    render(<ReturnChoiceDialog open docLabel="yêu cầu báo giá" onOpenChange={onOpenChange} onPick={onPick} />)
    await userEvent.click(screen.getByRole('button', { name: /^hủy$/i }))
    expect(onPick).not.toHaveBeenCalled()
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
})
