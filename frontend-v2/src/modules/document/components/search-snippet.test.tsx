import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { SearchSnippet } from './search-snippet'
import type { DocumentSearchHit } from '../types/document-search'

function hit(overrides: Partial<DocumentSearchHit> = {}): DocumentSearchHit {
  return {
    score: 2,
    matched_in: 'body',
    match_label: 'Nội dung',
    //  "đây là hợp đồng lao động chính thức" — "hợp đồng lao động" bắt đầu
    //  đúng tại chỉ số 7 (sau "đây là "), dài 17 ký tự → [7, 24).
    snippet: { text: 'đây là hợp đồng lao động chính thức', highlights: [[7, 24]] },
    ...overrides,
  }
}

describe('SearchSnippet', () => {
  it('không dựng gì khi hit rỗng (metadata-only match, không có đoạn trích)', () => {
    const { container } = render(<SearchSnippet hit={hit({ snippet: null })} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('không dựng gì khi hit là null/undefined', () => {
    const { container: c1 } = render(<SearchSnippet hit={null} />)
    expect(c1).toBeEmptyDOMElement()
    const { container: c2 } = render(<SearchSnippet hit={undefined} />)
    expect(c2).toBeEmptyDOMElement()
  })

  it('dựng nhãn nơi trúng và đoạn chữ tô sáng bằng thẻ <mark>', () => {
    render(<SearchSnippet hit={hit()} />)
    expect(screen.getByText('Nội dung:')).toBeInTheDocument()
    const mark = screen.getByText('hợp đồng lao động')
    expect(mark.tagName).toBe('MARK')
  })

  it('KHÔNG chèn HTML từ đoạn trích — chuỗi có thẻ <script> hiện ra như CHỮ, không thực thi', () => {
    render(
      <SearchSnippet
        hit={hit({
          snippet: { text: '<script>alert(1)</script> nội dung', highlights: [[0, 8]] },
        })}
      />,
    )
    //  React dựng text node bình thường — thẻ giả xuất hiện dưới dạng CHỮ THẤY
    //  ĐƯỢC trong <mark>, không có phần tử <script> thật nào trong DOM.
    expect(document.querySelector('script')).toBeNull()
    expect(screen.getByText('<script>')).toBeInTheDocument()
  })

  it('không dựng nhãn khi match_label rỗng (chỉ có ở khớp file/body)', () => {
    render(<SearchSnippet hit={hit({ match_label: '' })} />)
    expect(screen.queryByText(':')).not.toBeInTheDocument()
  })
})
