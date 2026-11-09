import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ReportItemProgressCard } from './report-item-progress-card'

const baseProps = {
  name: 'Kali nitrat KNO₃ 99%',
  docCount: 6,
  doneCount: 2,
  progress: <div role="progressbar" aria-label="2/6" />,
  expiry: <span>12/11/2026</span>,
}

describe('ReportItemProgressCard', () => {
  it('shows the item name, counts, progress bar and nearest expiry', () => {
    render(<ReportItemProgressCard {...baseProps} onToggle={() => {}} />)

    expect(screen.getByText('Kali nitrat KNO₃ 99%')).toBeInTheDocument()
    expect(screen.getByText('6 hồ sơ · 2 đã xong')).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
    expect(screen.getByText('12/11/2026')).toBeInTheDocument()
  })

  it('toggles through a real button that reports its expanded state', () => {
    const onToggle = vi.fn()
    const { rerender } = render(
      <ReportItemProgressCard {...baseProps} onToggle={onToggle}>
        <p>Hồ sơ của dòng</p>
      </ReportItemProgressCard>,
    )

    const toggle = screen.getByRole('button', { name: /Kali nitrat/ })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText('Hồ sơ của dòng')).toBeNull()

    fireEvent.click(toggle)
    expect(onToggle).toHaveBeenCalledTimes(1)

    rerender(
      <ReportItemProgressCard {...baseProps} open onToggle={onToggle}>
        <p>Hồ sơ của dòng</p>
      </ReportItemProgressCard>,
    )
    expect(screen.getByRole('button', { name: /Kali nitrat/ })).toHaveAttribute(
      'aria-expanded',
      'true',
    )
    expect(screen.getByText('Hồ sơ của dòng')).toBeInTheDocument()
  })

  it('action buttons and the expanded detail sit outside the toggle button', () => {
    render(
      <ReportItemProgressCard
        {...baseProps}
        open
        onToggle={() => {}}
        actions={<button type="button">Xóa cụm</button>}
      >
        <button type="button">Sửa hồ sơ</button>
      </ReportItemProgressCard>,
    )

    //  Lồng nút trong nút là HTML sai, và trên máy cảm ứng hai vùng chạm đè nhau.
    expect(screen.getByRole('button', { name: 'Xóa cụm' }).parentElement?.closest('button')).toBeNull()
    expect(screen.getByRole('button', { name: 'Sửa hồ sơ' }).parentElement?.closest('button')).toBeNull()
  })

  it('the total row has no toggle at all', () => {
    render(<ReportItemProgressCard {...baseProps} name="Tổng cả phiếu" />)

    expect(screen.getByText('Tổng cả phiếu')).toBeInTheDocument()
    expect(screen.queryByRole('button')).toBeNull()
  })

  it('an item without any document still reads "0 hồ sơ · 0 đã xong"', () => {
    render(<ReportItemProgressCard {...baseProps} docCount={0} doneCount={0} onToggle={() => {}} />)

    expect(screen.getByText('0 hồ sơ · 0 đã xong')).toBeInTheDocument()
  })
})
