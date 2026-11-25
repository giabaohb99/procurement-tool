import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ImportBatchPurgeDialog } from './import-batch-purge-dialog'

const purgePreview = vi.fn()
const purge = vi.fn()

vi.mock('sonner', () => ({ toast: { error: vi.fn(), success: vi.fn() } }))
vi.mock('../api/import-api', () => ({
  importApi: {
    purgePreview: (...a: unknown[]) => purgePreview(...a),
    purge: (...a: unknown[]) => purge(...a),
  },
}))

const PREVIEW = {
  batch_id: 98,
  module: 4,
  target_label: 'định mức bao bì',
  total: 10,
  untouched: 8,
  edited: 2,
  recomputes_cutoff: false,
}

function renderDialog(onOpenChange = vi.fn()) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <ImportBatchPurgeDialog batchId={98} open onOpenChange={onOpenChange} />
    </QueryClientProvider>,
  )
  return onOpenChange
}

beforeEach(() => {
  purgePreview.mockReset()
  purge.mockReset()
})

describe('ImportBatchPurgeDialog', () => {
  it('hiện số dòng sẽ xóa, tách dòng đã sửa tay, mặc định chỉ xóa phần chưa sửa', async () => {
    purgePreview.mockResolvedValue(PREVIEW)
    purge.mockResolvedValue({ batch_id: 98, deleted: 8, kept_edited: 2, message: 'ok' })
    const onOpenChange = renderDialog()

    expect(await screen.findByText('định mức bao bì', { exact: false })).toBeTruthy()
    expect(screen.getByText(/Có/).textContent).toContain('2')
    const button = screen.getByRole('button', { name: 'Xóa 8 dòng' })
    await userEvent.click(button)

    await waitFor(() => expect(purge).toHaveBeenCalledWith(98, false))
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('tick xóa luôn dòng đã sửa tay thì nút đếm đủ và gửi include_edited', async () => {
    purgePreview.mockResolvedValue(PREVIEW)
    purge.mockResolvedValue({ batch_id: 98, deleted: 10, kept_edited: 0, message: 'ok' })
    renderDialog()

    await userEvent.click(await screen.findByRole('checkbox', { name: 'Xóa luôn dòng đã sửa tay' }))
    await userEvent.click(screen.getByRole('button', { name: 'Xóa 10 dòng' }))

    await waitFor(() => expect(purge).toHaveBeenCalledWith(98, true))
  })

  it('lô không còn dòng nào thì báo và khóa nút xóa', async () => {
    purgePreview.mockResolvedValue({ ...PREVIEW, total: 0, untouched: 0, edited: 0 })
    renderDialog()

    expect(await screen.findByText('Lô này không còn dòng dữ liệu nào để xóa.')).toBeTruthy()
    expect((screen.getByRole('button', { name: 'Xóa' }) as HTMLButtonElement).disabled).toBe(true)
    expect(purge).not.toHaveBeenCalled()
  })

  it('sổ Misa báo mốc sẽ được tính lại', async () => {
    purgePreview.mockResolvedValue({ ...PREVIEW, module: 6, target_label: 'dòng sổ Misa', edited: 0, untouched: 10, recomputes_cutoff: true })
    renderDialog()

    expect(await screen.findByText('Mốc sổ Misa sẽ được tính lại theo các dòng còn lại.')).toBeTruthy()
  })
})
