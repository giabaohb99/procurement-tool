// bao-CR-496 — chọn bộ lọc đã lưu là trang về ĐÚNG trạng thái đó; lưu / cập nhật / xóa đi qua API.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CustomsSavedFilterBar } from './customs-saved-filter-bar'

const api = {
  list: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  remove: vi.fn(),
}
vi.mock('../../api/customs-saved-filter-api', () => ({
  fetchCustomsSavedFilters: () => api.list(),
  createCustomsSavedFilter: (b: unknown) => api.create(b),
  updateCustomsSavedFilter: (id: number, b: unknown) => api.update(id, b),
  deleteCustomsSavedFilter: (id: number) => api.remove(id),
  fetchCustomsBatchRows: vi.fn(),
  fetchCustomsBatchRowSummary: vi.fn(),
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: () => Promise.resolve(true) }))

const NAMES = ['q', 'hs_code', 'origin'] as const
const SAVED = [
  { id: 7, name: 'Abamectin 3.6 EC', params: 'q=abamectin+3.6&origin=CN', is_shared: false, updated_at: null },
  { id: 8, name: 'HS 3808', params: 'hs_code=3808', is_shared: false, updated_at: null },
]

function mount(currentParams = '', onApply = vi.fn()) {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <CustomsSavedFilterBar currentParams={currentParams} filterNames={NAMES} onApply={onApply} />
    </QueryClientProvider>,
  )
  return onApply
}

beforeEach(() => {
  vi.clearAllMocks()
  api.list.mockResolvedValue({ items: SAVED, max_per_user: 50 })
})

describe('CustomsSavedFilterBar — bao-CR-496', () => {
  it('picking a saved filter applies its params and NULLS the filters it does not carry', async () => {
    const onApply = mount('hs_code=3808')
    await userEvent.click(await screen.findByRole('combobox', { name: /bộ lọc đã lưu/i }))
    await userEvent.click(await screen.findByRole('option', { name: 'Abamectin 3.6 EC' }))
    expect(onApply).toHaveBeenCalledWith({ q: 'abamectin 3.6', hs_code: null, origin: 'CN' })
  })

  it('save button is disabled when nothing is filtered, and saving posts the current params', async () => {
    mount('')
    expect(await screen.findByRole('button', { name: /lưu bộ lọc này/i })).toBeDisabled()
  })

  it('saves the current params under the typed name', async () => {
    api.create.mockResolvedValue({ id: 9, name: 'Mới', params: 'q=x', is_shared: false, updated_at: null })
    mount('q=x')
    await userEvent.click(await screen.findByRole('button', { name: /lưu bộ lọc này/i }))
    await userEvent.type(screen.getByLabelText('Tên bộ lọc'), '  Mới  ')
    await userEvent.click(screen.getByRole('button', { name: /^lưu$/i }))
    await waitFor(() => expect(api.create).toHaveBeenCalledWith({ name: 'Mới', params: 'q=x' }))
  })

  it('shows «Cập nhật» only when the selected filter differs from what is applied, then overwrites it', async () => {
    api.update.mockResolvedValue({ ...SAVED[1], params: 'hs_code=3808&origin=IN' })
    mount('hs_code=3808&origin=IN')
    await userEvent.click(await screen.findByRole('combobox', { name: /bộ lọc đã lưu/i }))
    await userEvent.click(await screen.findByRole('option', { name: 'HS 3808' }))
    await userEvent.click(screen.getByRole('button', { name: /cập nhật/i }))
    await waitFor(() =>
      expect(api.update).toHaveBeenCalledWith(8, { params: 'hs_code=3808&origin=IN' }),
    )
  })

  it('hides «Cập nhật» when the applied params equal the saved ones (order/page noise ignored)', async () => {
    mount('origin=CN&q=abamectin+3.6')
    await userEvent.click(await screen.findByRole('combobox', { name: /bộ lọc đã lưu/i }))
    await userEvent.click(await screen.findByRole('option', { name: 'Abamectin 3.6 EC' }))
    expect(screen.queryByRole('button', { name: /cập nhật/i })).toBeNull()
  })

  it('deletes the selected filter after confirmation', async () => {
    api.remove.mockResolvedValue(null)
    mount('hs_code=3808')
    await userEvent.click(await screen.findByRole('combobox', { name: /bộ lọc đã lưu/i }))
    await userEvent.click(await screen.findByRole('option', { name: 'HS 3808' }))
    await userEvent.click(screen.getByRole('button', { name: /xóa bộ lọc HS 3808/i }))
    await waitFor(() => expect(api.remove).toHaveBeenCalledWith(8))
  })

  it('blocks saving at the per-user cap', async () => {
    api.list.mockResolvedValue({ items: SAVED, max_per_user: 2 })
    mount('q=x')
    await screen.findByRole('combobox', { name: /bộ lọc đã lưu/i })
    await waitFor(() => expect(screen.getByRole('button', { name: /lưu bộ lọc này/i })).toBeDisabled())
  })
})
