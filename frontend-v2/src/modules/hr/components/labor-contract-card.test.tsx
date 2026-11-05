import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { formatMoney } from '@/shared/utils/format-money'
import { LaborContractCard } from './labor-contract-card'
import { makeLaborContract } from './labor-contract-fixture'

vi.mock('sonner', () => ({ toast: { error: vi.fn(), success: vi.fn(), warning: vi.fn() } }))

function handlers() {
  return {
    onEdit: vi.fn(),
    onGenerate: vi.fn(),
    onDownloadDocument: vi.fn(),
    onUploadSigned: vi.fn(),
    onDownloadSigned: vi.fn(),
    onTransition: vi.fn(),
    onDelete: vi.fn(),
  }
}

describe('LaborContractCard', () => {
  it('số HĐ lên đầu, mã hệ thống ở dòng phụ, kèm trạng thái, loại · chức danh, hiệu lực', () => {
    render(<LaborContractCard row={makeLaborContract()} busy={false} canReadSigned {...handlers()} />)

    expect(screen.getByText('01/2026/HDLD')).toBeInTheDocument()
    expect(screen.getByText('HDLD-0001')).toBeInTheDocument()
    expect(screen.getByText('Nháp')).toBeInTheDocument()
    expect(screen.getByText('Xác định thời hạn · Chuyên viên')).toBeInTheDocument()
    expect(screen.getByText('Hiệu lực: 01/01/2026 – 31/12/2026')).toBeInTheDocument()
  })

  it('chưa có số HĐ thì mã lên dòng đầu và KHÔNG in lần thứ hai', () => {
    render(<LaborContractCard row={makeLaborContract({ contract_no: '' })} busy={false} canReadSigned {...handlers()} />)
    expect(screen.getAllByText('HDLD-0001')).toHaveLength(1)
  })

  //  Lương in ĐỦ chữ số như cột Lương cơ bản của bảng — rút gọn "15 tr" là mất đồng lẻ.
  it('lương bày nguyên số, không rút gọn', () => {
    render(
      <LaborContractCard row={makeLaborContract({ base_salary: 15_250_500 })} busy={false} canReadSigned {...handlers()} />,
    )
    expect(screen.getByText(formatMoney(15_250_500))).toBeInTheDocument()
  })

  it('hợp đồng không thời hạn nói "Từ ..." thay vì khoảng hai đầu', () => {
    render(<LaborContractCard row={makeLaborContract({ end_date: null })} busy={false} canReadSigned {...handlers()} />)
    expect(screen.getByText('Hiệu lực: Từ 01/01/2026')).toBeInTheDocument()
  })

  it('nút "⋯" theo sang thẻ: mở được menu và gọi đúng hàm của bảng', async () => {
    const user = userEvent.setup()
    const h = handlers()
    const row = makeLaborContract()
    render(<LaborContractCard row={row} busy={false} canReadSigned {...h} />)

    await user.click(screen.getByRole('button', { name: /Thao tác với hợp đồng/ }))
    await user.click(await screen.findByRole('menuitem', { name: 'Sửa hợp đồng' }))
    expect(h.onEdit).toHaveBeenCalledWith(row)
  })

  it('đang chạy lệnh trên dòng thì nút thao tác bị khóa', () => {
    render(<LaborContractCard row={makeLaborContract()} busy canReadSigned {...handlers()} />)
    expect(screen.getByRole('button', { name: /Thao tác với hợp đồng/ })).toBeDisabled()
  })
})
