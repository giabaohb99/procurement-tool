import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { FormStepper } from './form-stepper'

const STEPS = [
  { title: 'Thông tin chung' },
  { title: 'Danh sách hàng', description: 'Mã hàng, số lượng' },
  { title: 'Xác nhận' },
] as const

describe('FormStepper', () => {
  it('hiện đủ các bước kèm mô tả', () => {
    render(<FormStepper steps={STEPS} current={0} />)

    expect(screen.getAllByRole('button')).toHaveLength(3)
    expect(screen.getByText('Danh sách hàng')).toBeInTheDocument()
    expect(screen.getByText('Mã hàng, số lượng')).toBeInTheDocument()
  })

  it('chỉ bước ĐÃ QUA mới bấm được; bước đang đứng và bước sau thì không', () => {
    render(<FormStepper steps={STEPS} current={1} onGoTo={vi.fn()} />)

    const [first, second, third] = screen.getAllByRole('button')
    expect(first).toBeEnabled() // đã qua -> quay lại được
    expect(second).toBeDisabled() // đang đứng
    expect(third).toBeDisabled() // chưa tới lượt, dữ liệu bước trước chưa kiểm
  })

  it('không truyền onGoTo thì cả dải chỉ để xem', () => {
    render(<FormStepper steps={STEPS} current={2} />)

    for (const button of screen.getAllByRole('button')) {
      expect(button).toBeDisabled()
    }
  })

  it('bấm bước đã qua thì báo đúng số thứ tự bước đó', async () => {
    const onGoTo = vi.fn()
    render(<FormStepper steps={STEPS} current={2} onGoTo={onGoTo} />)

    await userEvent.click(screen.getAllByRole('button')[0])

    expect(onGoTo).toHaveBeenCalledExactlyOnceWith(0)
  })

  it('bước chưa qua hiện số thứ tự, bước đã qua đổi thành dấu tích', () => {
    render(<FormStepper steps={STEPS} current={1} />)

    // Bước 1 đã qua -> không còn chữ "1"; bước 2 và 3 vẫn là số.
    expect(screen.queryByText('1')).not.toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })
})
