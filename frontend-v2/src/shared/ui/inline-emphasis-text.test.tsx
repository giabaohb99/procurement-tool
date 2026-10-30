import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { InlineEmphasisText } from './inline-emphasis-text'

describe('InlineEmphasisText', () => {
  it('shows bot bold as real bold text with no stars left on screen (bao-CR-695)', () => {
    const { container } = render(<InlineEmphasisText text="bấm **Làm tiếp** để nối *phiên*" />)
    expect(container.textContent).toBe('bấm Làm tiếp để nối phiên')
    expect(container.querySelector('strong')?.textContent).toBe('Làm tiếp')
    expect(container.querySelector('em')?.textContent).toBe('phiên')
  })

  it('renders angle brackets as text, never as elements', () => {
    const { container } = render(<InlineEmphasisText text="**<img src=x onerror=alert(1)>**" />)
    expect(container.querySelector('img')).toBeNull()
    expect(container.textContent).toBe('<img src=x onerror=alert(1)>')
  })

  it('renders nothing for an empty string', () => {
    const { container } = render(<InlineEmphasisText text="" />)
    expect(container.textContent).toBe('')
  })
})
