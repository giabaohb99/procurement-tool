// duoc-CR-606 — khung «Chèn biến». Danh mục chặn ở `@/core/api`; lọc + gom nhóm chạy THẬT.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'
import { LaborContractPlaceholderInsertPanel } from './labor-contract-placeholder-insert-panel'

vi.mock('@/core/api', async (importOriginal) => ({
  ...(await importOriginal<typeof CoreApi>()),
  apiGet: async () => [
    { key: 'ho_ten', label: 'Họ và tên', group: 'Người lao động', example: 'Nguyễn Văn A' },
    { key: 'luong_co_ban', label: 'Lương cơ bản', group: 'Lương', example: '15.000.000' },
    { key: 'luong_co_ban_bang_chu', label: 'Lương cơ bản bằng chữ', group: 'Lương', example: '' },
  ],
}))

function build(onInsert = vi.fn(), disabled = false) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <LaborContractPlaceholderInsertPanel onInsert={onInsert} disabled={disabled} />
    </QueryClientProvider>,
  )
  return onInsert
}

describe('LaborContractPlaceholderInsertPanel', () => {
  it('groups variables and inserts the exact token of the clicked one', async () => {
    const onInsert = build()
    expect(await screen.findByText('Người lao động')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Chèn biến Lương cơ bản bằng chữ' }))
    expect(onInsert).toHaveBeenCalledWith('{{ luong_co_ban_bang_chu }}')
  })

  it('finds variables without Vietnamese accents and says so when nothing matches', async () => {
    build()
    await screen.findByText('Người lao động')
    fireEvent.change(screen.getByRole('textbox', { name: 'Tìm biến' }), { target: { value: 'LUONG' } })
    expect(screen.queryByRole('button', { name: 'Chèn biến Họ và tên' })).toBeNull()
    expect(screen.getAllByRole('button', { name: /Chèn biến Lương/ })).toHaveLength(2)
    fireEvent.change(screen.getByRole('textbox', { name: 'Tìm biến' }), { target: { value: 'không có' } })
    expect(screen.getByText('Không có biến nào khớp «không có».')).toBeInTheDocument()
  })

  //  Bấm khi trình soạn chưa dựng xong thì không có chỗ chèn — nút phải khóa, không âm thầm nuốt.
  it('disables every variable while the editor is not ready', async () => {
    const onInsert = build(vi.fn(), true)
    const button = await screen.findByRole('button', { name: 'Chèn biến Họ và tên' })
    expect(button).toBeDisabled()
    fireEvent.click(button)
    expect(onInsert).not.toHaveBeenCalled()
  })
})
