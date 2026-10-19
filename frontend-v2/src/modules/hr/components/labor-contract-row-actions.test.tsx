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

const trigger = () => screen.getByRole('button', { name: /Thao tác với hợp đồng/ })

/** Mở menu «⋯» rồi trả về CHỮ của các mục (theo đúng thứ tự hiện). */
async function openMenu() {
  await userEvent.click(trigger())
  return (await screen.findAllByRole('menuitem')).map((m) => m.textContent)
}

//  duoc-CR-633: thao tác là MỘT nút «⋯» mở menu icon + chữ, chia nhóm Xem / Soạn / Trạng thái, Xóa cuối.
describe('LaborContractRowActions theo cờ backend', () => {
  it('DRAFT: menu có Sửa / Sinh tệp / Tải lên bản ký / Ký / Hủy / Xóa; chưa có tệp sinh thì KHÔNG có tải .docx', async () => {
    renderActions()
    expect(await openMenu()).toEqual([
      'Sửa hợp đồng', 'Sinh tệp hợp đồng', 'Tải lên bản đã ký', 'Đánh dấu đã ký', 'Hủy hợp đồng', 'Xóa hợp đồng',
    ])
  })

  it('menu chia nhóm có tiêu đề Soạn / Trạng thái; Xóa đứng cuối, tô đỏ', async () => {
    renderActions()
    await openMenu()
    expect(screen.getByText('Soạn')).toBeInTheDocument()
    expect(screen.getByText('Trạng thái')).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Xóa hợp đồng' })).toHaveAttribute('data-variant', 'destructive')
  })

  it('SIGNED: không có Sửa / Sinh / Xóa; có Xem bản ký, Thay bản ký, Chấm dứt', async () => {
    renderActions(
      makeLaborContract({
        status: 2, effective_status: 2, can_edit: false, can_generate: false, can_delete: false,
        transitions: [4], has_signed_file: true,
      }),
    )
    const items = await openMenu()
    expect(items).toEqual(['Xem bản đã ký', 'Thay bản đã ký', 'Chấm dứt / thanh lý'])
  })

  it('tải .docx chỉ hiện khi can_print, dù has_generated_file = true', async () => {
    renderActions(makeLaborContract({ has_generated_file: true, can_print: false }))
    const items = await openMenu()
    expect(items).not.toContain('Tải hợp đồng (.docx)')
    expect(items).toContain('Sinh lại tệp')
  })

  it('can_print = true: chọn tải gọi đúng dòng', async () => {
    const row = makeLaborContract({ has_generated_file: true, can_print: true })
    const h = renderActions(row)
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: 'Tải hợp đồng (.docx)' }))
    expect(h.onDownloadDocument).toHaveBeenCalledWith(row)
  })

  it('mã trạng thái đích lạ trong transitions bị bỏ qua, không vỡ giao diện', async () => {
    renderActions(makeLaborContract({ transitions: [999, 5] }))
    expect(await openMenu()).toContain('Hủy hợp đồng')
  })

  it('không cờ nào bật + không bước chuyển -> không dựng nút nào', () => {
    renderActions(
      makeLaborContract({
        can_edit: false, can_delete: false, can_generate: false, can_print: false,
        can_upload_signed: false, transitions: [],
      }),
    )
    expect(screen.queryAllByRole('button')).toHaveLength(0)
  })

  it('đang bận thì khóa nút Thao tác', () => {
    renderActions(makeLaborContract(), true)
    expect(trigger()).toBeDisabled()
  })

  it('nút Thao tác là type="button" (tab nằm trong <form> hồ sơ)', () => {
    renderActions(makeLaborContract({ has_signed_file: true, has_generated_file: true, can_print: true }))
    expect(trigger()).toHaveAttribute('type', 'button')
  })

  it('chọn Ký / Hủy đưa đúng mô tả bước chuyển lên', async () => {
    const row = makeLaborContract()
    const h = renderActions(row)
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: 'Đánh dấu đã ký' }))
    expect(h.onTransition).toHaveBeenCalledWith(row, expect.objectContaining({ toStatus: 2 }))
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: 'Hủy hợp đồng' }))
    expect(h.onTransition).toHaveBeenLastCalledWith(row, expect.objectContaining({ toStatus: 5 }))
  })

  it('chọn Sửa / Xóa gọi đúng callback với đúng dòng', async () => {
    const row = makeLaborContract()
    const h = renderActions(row)
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: 'Sửa hợp đồng' }))
    expect(h.onEdit).toHaveBeenCalledWith(row)
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: 'Xóa hợp đồng' }))
    expect(h.onDelete).toHaveBeenCalledWith(row)
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

  it('mục «Tải lên bản đã ký» mở hộp chọn tệp', async () => {
    renderActions()
    const click = vi.spyOn(input(), 'click')
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: 'Tải lên bản đã ký' }))
    expect(click).toHaveBeenCalled()
  })
})

describe('Mục «Mở bản lưu trữ ở Văn bản» (duoc-CR-629)', () => {
  const label = 'Mở bản lưu trữ ở Văn bản'

  it('can_open_document + document_id>0: có mục, mở tab mới tới đúng văn bản', async () => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null)
    renderActions(makeLaborContract({ can_open_document: true, document_id: 12 }))
    expect((await openMenu())[0]).toBe(label)
    await userEvent.click(screen.getByRole('menuitem', { name: label }))
    expect(open).toHaveBeenCalledWith(expect.stringContaining('/12'), '_blank', 'noopener')
    open.mockRestore()
  })

  it('không có quyền mở: không có mục', async () => {
    renderActions(makeLaborContract({ can_open_document: false, document_id: 12 }))
    expect(await openMenu()).not.toContain(label)
  })

  it('document_id = 0: không có mục dù có quyền', async () => {
    renderActions(makeLaborContract({ can_open_document: true, document_id: 0 }))
    expect(await openMenu()).not.toContain(label)
  })
})
