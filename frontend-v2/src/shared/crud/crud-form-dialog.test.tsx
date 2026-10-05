import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CrudFormDialog } from './crud-form-dialog'
import type { CrudConfig, CrudRecord } from './types'

const apiDelete = vi.fn()
const apiPost = vi.fn()
const apiPatch = vi.fn()
let canDelete = true

vi.mock('@/core/api', () => ({
  apiGet: vi.fn(),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPatch: (...args: unknown[]) => apiPatch(...args),
  apiDelete: (...args: unknown[]) => apiDelete(...args),
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (_entity: string, action: string) => (action === 'delete' ? canDelete : true),
    canAny: () => true,
  }),
}))

interface Row extends CrudRecord {
  id: number
  name: string
}

const BASE: CrudConfig<Row> = {
  entity: 'work_schedule',
  title: 'Gán lịch làm việc',
  unitLabel: 'dòng gán lịch',
  apiPath: '/api/work-schedule-assignments',
  storageKey: 'test.assignments',
  columns: [],
  listRoute: '/hr/work-schedule-assignments',
  openFormOnRowClick: true,
  getItemName: (r) => r.name,
  formFields: [{ name: 'name', label: 'Tên' }],
}

function build(config: CrudConfig<Row>, item: Row | null, onOpenChange = vi.fn()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <CrudFormDialog open onOpenChange={onOpenChange} config={config} item={item} />
    </QueryClientProvider>,
  )
  return onOpenChange
}

beforeEach(() => {
  vi.clearAllMocks()
  canDelete = true
  apiDelete.mockResolvedValue(null)
})

describe('CrudFormDialog — nút Xóa trong popup Sửa', () => {
  //  Lỗi 05/10/2026: màn Gán lịch mở popup khi bấm dòng và không có trang chi tiết,
  //  nên trước khi có cờ `deleteInForm` thì không có chỗ nào trên giao diện để xóa dòng.
  it('deletes the record from the edit popup and closes it when the flag is on', async () => {
    const onOpenChange = build({ ...BASE, deleteInForm: true }, { id: 7, name: 'Quản trị viên' })

    await userEvent.click(screen.getByRole('button', { name: 'Xóa' }))
    const alert = await screen.findByRole('alertdialog')
    expect(within(alert).getByText(/Quản trị viên/)).toBeInTheDocument()
    await userEvent.click(within(alert).getByRole('button', { name: 'Xóa' }))

    await waitFor(() => expect(apiDelete).toHaveBeenCalledWith('/api/work-schedule-assignments/7'))
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
    expect(apiPatch).not.toHaveBeenCalled()
  })

  it('keeps existing popups unchanged when the flag is off', () => {
    build(BASE, { id: 7, name: 'x' })
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
  })

  it('never offers delete while creating a new record', () => {
    build({ ...BASE, deleteInForm: true }, null)
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
  })

  it('hides delete from users without the delete permission', () => {
    canDelete = false
    build({ ...BASE, deleteInForm: true }, { id: 7, name: 'x' })
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
  })

  it('cancelling the confirmation deletes nothing and saves nothing', async () => {
    build({ ...BASE, deleteInForm: true }, { id: 7, name: 'x' })
    await userEvent.click(screen.getByRole('button', { name: 'Xóa' }))
    const alert = await screen.findByRole('alertdialog')
    await userEvent.click(within(alert).getByRole('button', { name: 'Hủy' }))
    expect(apiDelete).not.toHaveBeenCalled()
    expect(apiPatch).not.toHaveBeenCalled()
    expect(apiPost).not.toHaveBeenCalled()
  })
})
