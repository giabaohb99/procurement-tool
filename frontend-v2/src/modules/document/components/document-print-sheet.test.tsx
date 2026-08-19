import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { DocumentPrintSheet } from './document-print-sheet'

/**
 * jsdom KHÔNG có bố cục thật: mọi chiều cao đo được đều bằng 0, nên cả bài luôn
 * gom vào một tờ. Vì vậy bài này chỉ canh phần HỢP ĐỒNG của component — nội
 * dung phải ra đúng, lề phải áp đúng, trang đầu không đánh số, chữ chìm hiện
 * khi được yêu cầu. Phần chia trang theo chiều cao đã có bài riêng ở
 * `split-blocks-into-pages.test.ts`.
 */
const HTML = '<p>Điều 1. Nội dung.</p><p>Điều 2. Hiệu lực.</p>'

describe('DocumentPrintSheet', () => {
  it('dựng đủ nội dung thân văn bản', async () => {
    render(<DocumentPrintSheet html={HTML} marginLeftMm={30} marginRightMm={20} />)

    //  Có cả bản ĐO (ẩn) lẫn tờ thật nên mỗi câu xuất hiện hai lần.
    await waitFor(() => expect(screen.getAllByText('Điều 1. Nội dung.').length).toBe(2))
  })

  it('áp đúng lề của bản ghi lên tờ giấy', async () => {
    const { container } = render(
      <DocumentPrintSheet html={HTML} marginLeftMm={35} marginRightMm={15} />,
    )

    await waitFor(() => expect(container.querySelector('.doc-print-sheet')).not.toBeNull())
    const sheet = container.querySelector('.doc-print-sheet') as HTMLElement
    expect(sheet.style.paddingLeft).toBe('35mm')
    expect(sheet.style.paddingRight).toBe('15mm')
  })

  it('không đánh số ở trang đầu — đúng Nghị định 30', async () => {
    const { container } = render(
      <DocumentPrintSheet html={HTML} marginLeftMm={30} marginRightMm={20} />,
    )

    await waitFor(() => expect(container.querySelector('.doc-print-sheet')).not.toBeNull())
    expect(container.querySelector('.doc-print-page-number')).toBeNull()
  })

  it('đóng chữ chìm khi được yêu cầu — tờ giấy rời màn hình là mất trạng thái', async () => {
    render(
      <DocumentPrintSheet
        html={HTML}
        marginLeftMm={30}
        marginRightMm={20}
        watermark="BẢN NHÁP"
      />,
    )

    await waitFor(() => expect(screen.getByText('BẢN NHÁP')).toBeInTheDocument())
  })

  it('báo ra số tờ để trang cha hiện "N trang"', async () => {
    const onLayout = vi.fn()
    render(
      <DocumentPrintSheet
        html={HTML}
        marginLeftMm={30}
        marginRightMm={20}
        onLayout={onLayout}
      />,
    )

    await waitFor(() => expect(onLayout).toHaveBeenCalled())
    expect(onLayout.mock.calls[0][0].pages).toBeGreaterThanOrEqual(1)
  })
})
