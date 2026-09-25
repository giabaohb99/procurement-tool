import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { LoadMoreTasks } from './load-more-tasks'

describe('LoadMoreTasks — bao-CR-483', () => {
  it('không còn gì để tải thì không dựng gì', () => {
    const { container } = render(<LoadMoreTasks remaining={0} loading={false} onLoadMore={() => {}} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('hiện đúng số còn lại và bấm là gọi tải thêm', async () => {
    const onLoadMore = vi.fn()
    render(<LoadMoreTasks remaining={120} loading={false} onLoadMore={onLoadMore} />)
    await userEvent.click(screen.getByRole('button', { name: 'Tải thêm 120 việc' }))
    expect(onLoadMore).toHaveBeenCalledTimes(1)
  })

  it('đang tải thì khóa nút, không cho bấm chồng', () => {
    render(<LoadMoreTasks remaining={5} loading onLoadMore={() => {}} />)
    expect(screen.getByRole('button')).toBeDisabled()
    expect(screen.getByText('Đang tải…')).toBeInTheDocument()
  })
})
