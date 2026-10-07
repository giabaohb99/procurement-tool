import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { toast } from 'sonner'
import { makeLaborContract } from './labor-contract-fixture'
import { LaborContractRowActions } from './labor-contract-row-actions'

vi.mock('sonner', () => ({ toast: { error: vi.fn(), success: vi.fn(), warning: vi.fn() } }))

const handlers = () => ({
  onEdit: vi.fn(),
  onGenerate: vi.fn(),
  onDownloadDocument: vi.fn(),
  onUploadSigned: vi.fn(),
  onDownloadSigned: vi.fn(),
  onTransition: vi.fn(),
  onDelete: vi.fn(),
})

function renderActions(row = makeLaborContract(), busy = false) {
  const h = handlers()
  render(<LaborContractRowActions row={row} busy={busy} canReadSigned {...h} />)
  return h
}

describe('LaborContractRowActions theo cờ backend', () => {
  it('DRAFT: có Sửa / Sinh tệp / Ký / Hủy / Xóa; chưa có tệp sinh thì KHÔNG có nút tải .docx', () => {
    renderActions()
    expect(screen.getByLabelText('Sửa hợp đồng')).toBeInTheDocument()
    expect(screen.getByLabelText('Sinh tệp hợp đồng')).toBeInTheDocument()
    expect(screen.getByLabelText('Đánh dấu đã ký')).toBeInTheDocument()
    expect(screen.getByLabelText('Hủy hợp đồng')).toBeInTheDocument()
    expect(screen.getByLabelText('Xóa hợp đồng')).toBeInTheDocument()
    expect(screen.queryByLabelText('Tải hợp đồng (.docx)')).not.toBeInTheDocument()
  })

  it('SIGNED: không có Sửa / Sinh / Xóa; có Chấm dứt', () => {
    renderActions(
      makeLaborContract({
        status: 2, effective_status: 2, can_edit: false, can_generate: false, can_delete: false,
        transitions: [4], has_signed_file: true,
      }),
    )
    expect(screen.queryByLabelText('Sửa hợp đồng')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Sinh tệp hợp đồng')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Xóa hợp đồng')).not.toBeInTheDocument()
    expect(screen.getByLabelText('Chấm dứt / thanh lý')).toBeInTheDocument()
    expect(screen.getByLabelText('Xem bản đã ký')).toBeInTheDocument()
    expect(screen.getByLabelText('Thay bản đã ký')).toBeInTheDocument()
  })

  it('tải .docx chỉ hiện khi can_print (đã có tệp VÀ có quyền in), dù has_generated_file = true', () => {
    renderActions(makeLaborContract({ has_generated_file: true, can_print: false }))
    expect(screen.queryByLabelText('Tải hợp đồng (.docx)')).not.toBeInTheDocument()
    expect(screen.getByLabelText('Sinh lại tệp')).toBeInTheDocument()
  })

  it('can_print = true: bấm tải gọi đúng dòng', async () => {
    const row = makeLaborContract({ has_generated_file: true, can_print: true })
    const h = renderActions(row)
    await userEvent.click(screen.getByLabelText('Tải hợp đồng (.docx)'))
    expect(h.onDownloadDocument).toHaveBeenCalledWith(row)
  })

  it('mã trạng thái đích lạ trong transitions bị bỏ qua, không vỡ giao diện', () => {
    renderActions(makeLaborContract({ transitions: [999, 5] }))
    expect(screen.getAllByRole('button').some((b) => b.getAttribute('aria-label') === 'Hủy hợp đồng')).toBe(true)
  })

  it('không cờ nào bật + không bước chuyển -> không có nút nào', () => {
    renderActions(
      makeLaborContract({
        can_edit: false, can_delete: false, can_generate: false, can_print: false,
        can_upload_signed: false, transitions: [],
      }),
    )
    expect(screen.queryAllByRole('button')).toHaveLength(0)
  })

  it('đang bận thì khóa mọi nút', () => {
    renderActions(makeLaborContract(), true)
    for (const b of screen.getAllByRole('button')) expect(b).toBeDisabled()
  })

  it('mọi nút là type="button" (tab nằm trong <form> hồ sơ)', () => {
    renderActions(makeLaborContract({ has_signed_file: true, has_generated_file: true, can_print: true }))
    for (const b of screen.getAllByRole('button')) expect(b).toHaveAttribute('type', 'button')
  })

  it('bấm Ký / Hủy đưa đúng mô tả bước chuyển lên', async () => {
    const row = makeLaborContract()
    const h = renderActions(row)
    await userEvent.click(screen.getByLabelText('Đánh dấu đã ký'))
    expect(h.onTransition).toHaveBeenCalledWith(row, expect.objectContaining({ toStatus: 2 }))
    await userEvent.click(screen.getByLabelText('Hủy hợp đồng'))
    expect(h.onTransition).toHaveBeenLastCalledWith(row, expect.objectContaining({ toStatus: 5 }))
  })
})

describe('chọn bản đã ký', () => {
  const input = () => screen.getByLabelText('Chọn bản đã ký') as HTMLInputElement

  it('tệp hợp lệ -> gọi onUploadSigned', () => {
    const row = makeLaborContract()
    const h = renderActions(row)
    const f = new File([new Uint8Array(5)], 'ky.pdf')
    fireEvent.change(input(), { target: { files: [f] } })
    expect(h.onUploadSigned).toHaveBeenCalledWith(row, f)
  })

  it('tệp sai đuôi -> toast lỗi, KHÔNG gửi', () => {
    const h = renderActions()
    fireEvent.change(input(), { target: { files: [new File([new Uint8Array(5)], 'virus.exe')] } })
    expect(h.onUploadSigned).not.toHaveBeenCalled()
    expect(toast.error).toHaveBeenCalled()
  })

  it('không chọn tệp nào (hủy hộp chọn) -> không làm gì', () => {
    const h = renderActions()
    fireEvent.change(input(), { target: { files: [] } })
    expect(h.onUploadSigned).not.toHaveBeenCalled()
  })
})
