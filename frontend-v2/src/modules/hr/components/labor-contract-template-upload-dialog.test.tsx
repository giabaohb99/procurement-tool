import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type * as CoreApi from '@/core/api'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { LaborContractTemplate } from '../types/labor-contract'
import { LaborContractTemplateUploadDialog } from './labor-contract-template-upload-dialog'

const apiPut = vi.hoisted(() => vi.fn())
vi.mock('@/core/api', async (original) => ({
  ...(await original<typeof CoreApi>()),
  apiPut,
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

const template = { id: 5, name: 'Mẫu thử việc' } as LaborContractTemplate
const docx = new File([new Uint8Array(8)], 'mau.docx')

function renderDialog() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <LaborContractTemplateUploadDialog open onOpenChange={vi.fn()} replacing={template} />
    </QueryClientProvider>,
  )
}

async function pickDocx(file: File) {
  const input = document.querySelector<HTMLInputElement>('input[type="file"]')
  if (!input) throw new Error('thiếu ô chọn tệp')
  await userEvent.upload(input, file)
}

beforeEach(() => {
  // Phải có thân hàm: trả `mockReset()` ra ngoài thì vitest coi đó là hàm dọn dẹp và GỌI LẠI mock.
  apiPut.mockReset()
})

describe('hộp thay tệp mẫu hợp đồng', () => {
  it('nút Thay tệp tắt khi chưa chọn tệp', () => {
    renderDialog()
    expect(screen.getByRole('button', { name: 'Thay tệp' })).toBeDisabled()
  })

  // Lỗi cần chống: biến lạ chỉ hiện ở toast rồi biến mất, người soạn mẫu không còn gì để sửa theo.
  it('lỗi 422 biến lạ: liệt kê từng biến ngay trong hộp kèm gợi ý gõ lại liền một lần', async () => {
    apiPut.mockRejectedValue({
      response: {
        status: 422,
        data: {
          success: false,
          error: { message: 'Mẫu dùng biến ngoài danh mục: ho_ten_sai, luong', details: { unknown: ['ho_ten_sai', 'luong'] } },
        },
      },
    })
    renderDialog()
    await pickDocx(docx)
    await userEvent.click(screen.getByRole('button', { name: 'Thay tệp' }))

    const list = await screen.findByRole('list', { name: 'Biến lạ trong mẫu' })
    expect(list).toHaveTextContent('{{ ho_ten_sai }}')
    expect(list).toHaveTextContent('{{ luong }}')
    expect(screen.getByText(/gõ lại biến liền một lần/)).toBeInTheDocument()
  })

  it('lỗi khác (không có biến lạ): chỉ hiện câu lỗi, không có danh sách biến', async () => {
    apiPut.mockRejectedValue({ response: { status: 422, data: { success: false, error: { message: 'Tệp rỗng.' } } } })
    renderDialog()
    await pickDocx(docx)
    await userEvent.click(screen.getByRole('button', { name: 'Thay tệp' }))

    await waitFor(() => expect(screen.getByText('Tệp rỗng.')).toBeInTheDocument())
    expect(screen.queryByRole('list', { name: 'Biến lạ trong mẫu' })).toBeNull()
  })

  it('tệp sai đuôi bị chặn tại chỗ, không gọi API', async () => {
    renderDialog()
    const input = document.querySelector<HTMLInputElement>('input[type="file"]')
    if (!input) throw new Error('thiếu ô chọn tệp')
    // `applyAccept: false`: giả người dùng ép chọn tệp ngoài bộ lọc của hộp chọn.
    await userEvent.setup({ applyAccept: false }).upload(input, new File(['x'], 'mau.pdf'))

    expect(await screen.findByRole('alert')).toHaveTextContent('Chỉ nhận tệp Word .docx')
    expect(screen.getByRole('button', { name: 'Thay tệp' })).toBeDisabled()
    expect(apiPut).not.toHaveBeenCalled()
  })
})
