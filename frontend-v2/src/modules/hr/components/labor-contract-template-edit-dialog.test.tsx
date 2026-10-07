// duoc-CR-606 — hộp «Sửa thông tin» mẫu: tên · loại HĐ · ghi chú (PATCH). Chặn ở `@/core/api`.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'
import type { LaborContractTemplate } from '../types/labor-contract'
import { LaborContractTemplateEditDialog } from './labor-contract-template-edit-dialog'

const patches: { url: string; body: unknown }[] = []
let release: () => void = () => {}
vi.mock('@/core/api', async (importOriginal) => ({
  ...(await importOriginal<typeof CoreApi>()),
  apiPatch: (url: string, body: unknown) => {
    patches.push({ url, body })
    return new Promise((resolve) => {
      release = () => resolve({ id: 7 })
    })
  },
}))

const template: LaborContractTemplate = {
  id: 7, company_id: 1, company_name: 'Công ty A', company_code: 'CTA', contract_type: 2, name: 'Mẫu 12 tháng',
  note: 'cũ', original_filename: 'mau.docx', file_size: 2048, placeholders: [], is_active: true,
  created_at: '2026-10-01T03:00:00', created_by_name: 'HR', contract_count: 0,
}

function build(onOpenChange = vi.fn()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <LaborContractTemplateEditDialog template={template} onOpenChange={onOpenChange} />
    </QueryClientProvider>,
  )
  return onOpenChange
}

beforeEach(() => {
  patches.length = 0
})

describe('LaborContractTemplateEditDialog', () => {
  it('prefills the current values and sends trimmed name and note, never the company', async () => {
    const onOpenChange = build()
    expect(screen.getByLabelText(/Tên mẫu/)).toHaveValue('Mẫu 12 tháng')
    fireEvent.change(screen.getByLabelText(/Tên mẫu/), { target: { value: '  Mẫu 24 tháng  ' } })
    fireEvent.change(screen.getByLabelText('Ghi chú'), { target: { value: '  dùng cho kỹ sư ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(patches).toHaveLength(1))
    expect(patches[0]).toEqual({
      url: '/api/labor-contract-templates/7',
      body: { name: 'Mẫu 24 tháng', contract_type: 2, note: 'dùng cho kỹ sư' },
    })
    release()
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('blocks an empty or whitespace-only name without calling the API', async () => {
    build()
    fireEvent.change(screen.getByLabelText(/Tên mẫu/), { target: { value: '   ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByText('Nhập tên mẫu')).toBeInTheDocument()
    expect(patches).toHaveLength(0)
  })

  it('blocks a name longer than the 200-character column', async () => {
    build()
    fireEvent.change(screen.getByLabelText(/Tên mẫu/), { target: { value: 'x'.repeat(201) } })
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByText('Tên tối đa 200 ký tự')).toBeInTheDocument()
    expect(patches).toHaveLength(0)
  })

  //  `disabled={isPending}` chỉ đúng ở lượt render sau — bấm liền tay phải vẫn ra MỘT request.
  it('sends a single request when Save is double-clicked', async () => {
    build()
    const save = screen.getByRole('button', { name: 'Lưu' })
    fireEvent.click(save)
    fireEvent.click(save)
    await waitFor(() => expect(patches).toHaveLength(1))
    await new Promise((r) => setTimeout(r, 20))
    expect(patches).toHaveLength(1)
    release()
  })
})
