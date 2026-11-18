import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { useCardCollapse } from '@/shared/hooks/use-card-collapse'

import { CardCollapseScope, CardCollapseToggle, WithCardCollapse } from './card-collapse'
import { ChartCard } from './chart'
import { FormCard } from './form-card'

function renderCard(withScope: boolean) {
  const card = (
    <FormCard title="Quỹ phép 2026">
      <p>Phép năm còn 10 ngày</p>
    </FormCard>
  )
  return render(withScope ? <CardCollapseScope scope="me">{card}</CardCollapseScope> : card)
}

describe('FormCard collapse (duoc-CR-772)', () => {
  beforeEach(() => localStorage.clear())

  it('has no toggle outside a collapse scope, so other screens stay unchanged', () => {
    renderCard(false)
    expect(screen.queryByRole('button', { name: /Thu gọn|Mở/ })).not.toBeInTheDocument()
    expect(screen.getByText('Phép năm còn 10 ngày')).toBeVisible()
  })

  it('starts open with a chevron up, collapses on click and shows a chevron down to reopen', () => {
    renderCard(true)
    const toggle = screen.getByRole('button', { name: 'Thu gọn Quỹ phép 2026' })
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    fireEvent.click(toggle)
    expect(screen.getByText('Phép năm còn 10 ngày')).not.toBeVisible()
    const reopen = screen.getByRole('button', { name: 'Mở Quỹ phép 2026' })
    expect(reopen).toHaveAttribute('aria-expanded', 'false')

    fireEvent.click(reopen)
    expect(screen.getByText('Phép năm còn 10 ngày')).toBeVisible()
  })

  it('remembers a collapsed card after the page is opened again', () => {
    const { unmount } = renderCard(true)
    fireEvent.click(screen.getByRole('button', { name: 'Thu gọn Quỹ phép 2026' }))
    unmount()

    renderCard(true)
    expect(screen.getByRole('button', { name: 'Mở Quỹ phép 2026' })).toBeInTheDocument()
    expect(screen.getByText('Phép năm còn 10 ngày')).not.toBeVisible()
  })

  it('keeps the card body mounted while collapsed so typed drafts are not lost', () => {
    renderCard(true)
    fireEvent.click(screen.getByRole('button', { name: 'Thu gọn Quỹ phép 2026' }))
    expect(screen.getByText('Phép năm còn 10 ngày')).toBeInTheDocument()
  })
})

/** Thẻ tối giản gọi hook có `forceOpen`, như thẻ Thông tin chung YCBG khi có ô sai. */
function ForcedCard({ forceOpen }: { forceOpen: boolean }) {
  const collapse = useCardCollapse('Thông tin chung', { forceOpen })
  return (
    <section>
      {collapse.collapsible && (
        <CardCollapseToggle title="Thông tin chung" open={collapse.open} onToggle={collapse.toggle} />
      )}
      <p hidden={!collapse.open}>Ô người yêu cầu</p>
    </section>
  )
}

describe('card collapse for Thu mua pages (duoc-CR-780)', () => {
  beforeEach(() => localStorage.clear())

  it('forceOpen shows a card the user collapsed earlier and hides the useless toggle', () => {
    //  Ô sai nằm trong thẻ đang gập thì bấm Lưu chỉ thấy câu báo mà không thấy ô nào.
    localStorage.setItem('erp.section.procurement.survey-request.Thông tin chung', '0')
    const { rerender } = render(
      <CardCollapseScope scope="procurement.survey-request">
        <ForcedCard forceOpen={false} />
      </CardCollapseScope>,
    )
    expect(screen.getByText('Ô người yêu cầu')).not.toBeVisible()

    rerender(
      <CardCollapseScope scope="procurement.survey-request">
        <ForcedCard forceOpen />
      </CardCollapseScope>,
    )
    expect(screen.getByText('Ô người yêu cầu')).toBeVisible()
    expect(screen.queryByRole('button', { name: /Thông tin chung/ })).not.toBeInTheDocument()
  })

  it('keeps the same title independent across document types', () => {
    //  Gập "Thông tin chung" ở YCMH không được kéo theo thẻ cùng tên ở ĐMH.
    render(
      <>
        <CardCollapseScope scope="procurement.purchase-request">
          <FormCard title="Thông tin chung">
            <p>Thân YCMH</p>
          </FormCard>
        </CardCollapseScope>
        <CardCollapseScope scope="procurement.purchase-order">
          <FormCard title="Thông tin chung">
            <p>Thân ĐMH</p>
          </FormCard>
        </CardCollapseScope>
      </>,
    )
    fireEvent.click(screen.getAllByRole('button', { name: 'Thu gọn Thông tin chung' })[0])
    expect(screen.getByText('Thân YCMH')).not.toBeVisible()
    expect(screen.getByText('Thân ĐMH')).toBeVisible()
  })

  it('WithCardCollapse reads the scope for a card built inline in the page body', () => {
    const inline = (
      <WithCardCollapse title="Dòng hàng">
        {(collapse) => (
          <div>
            {collapse.collapsible && (
              <CardCollapseToggle title="Dòng hàng" open={collapse.open} onToggle={collapse.toggle} />
            )}
            <p hidden={!collapse.open}>Bảng dòng</p>
          </div>
        )}
      </WithCardCollapse>
    )
    const { unmount } = render(inline)
    expect(screen.queryByRole('button', { name: /Dòng hàng/ })).not.toBeInTheDocument()
    unmount()

    render(<CardCollapseScope scope="procurement.purchase-order">{inline}</CardCollapseScope>)
    fireEvent.click(screen.getByRole('button', { name: 'Thu gọn Dòng hàng' }))
    expect(screen.getByText('Bảng dòng')).not.toBeVisible()
  })

  it('ChartCard collapses inside a scope and stays as before everywhere else', () => {
    const chart = (
      <ChartCard title="Chi tiêu theo bộ phận" description="Theo đơn đã duyệt">
        <p>Biểu đồ cột</p>
      </ChartCard>
    )
    const { unmount } = render(chart)
    expect(screen.queryByRole('button', { name: /Chi tiêu theo bộ phận/ })).not.toBeInTheDocument()
    unmount()

    render(<CardCollapseScope scope="procurement.dashboard">{chart}</CardCollapseScope>)
    fireEvent.click(screen.getByRole('button', { name: 'Thu gọn Chi tiêu theo bộ phận' }))
    expect(screen.getByText('Biểu đồ cột')).not.toBeVisible()
    //  Gập thì câu mô tả cũng thu theo, chỉ còn tiêu đề.
    expect(screen.queryByText('Theo đơn đã duyệt')).not.toBeInTheDocument()
  })
})
