import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { BreadcrumbPageLabelContext } from './breadcrumb-page-label'
import { PageHeader } from './page-header'

/** duoc-CR-714: tiêu đề lặp đúng chữ cuối breadcrumb thì ẩn khỏi mắt, vẫn còn `<h1>` cho trình đọc màn hình. */
function renderWith(label: string | null, ui: React.ReactNode) {
  return render(<BreadcrumbPageLabelContext.Provider value={label}>{ui}</BreadcrumbPageLabelContext.Provider>)
}

describe('PageHeader + breadcrumb', () => {
  it('visually hides a title equal to the breadcrumb page (case/space-insensitive) but keeps the h1', () => {
    renderWith('Chức vụ', <PageHeader title=" chức VỤ " description="Mô tả vẫn hiện" />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveClass('sr-only')
    expect(screen.getByText('Mô tả vẫn hiện')).toBeVisible()
  })

  it('keeps a different title visible, and keeps it outside a module layout (no label)', () => {
    renderWith('Chức vụ', <PageHeader title="Trưởng phòng" />)
    expect(screen.getByRole('heading', { level: 1 })).not.toHaveClass('sr-only')
    renderWith(null, <PageHeader title="Chức vụ" />)
    expect(screen.getAllByRole('heading', { level: 1 })[1]).not.toHaveClass('sr-only')
  })

  it('never hides a JSX title (it carries badges / status next to the name)', () => {
    renderWith('Chức vụ', <PageHeader title={<span>Chức vụ</span>} />)
    expect(screen.getByRole('heading', { level: 1 })).not.toHaveClass('sr-only')
  })

  it('hides a non-duplicate title when the header row carries sub-tabs (duoc-CR-753), still keeping the h1', () => {
    renderWith('Loại nghỉ và ngày lễ', <PageHeader title="Loại nghỉ" hideTitle description="Tab con" />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveClass('sr-only')
    expect(screen.getByText('Tab con')).toBeVisible()
  })
})
