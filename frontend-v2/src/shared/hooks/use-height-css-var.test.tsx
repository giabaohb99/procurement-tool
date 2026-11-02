import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { useHeightCssVar } from './use-height-css-var'

function Probe({ show }: { show: boolean }) {
  const ref = useHeightCssVar('--probe-h')
  return <div data-testid="parent">{show && <div ref={ref}>đầu trang</div>}</div>
}

describe('useHeightCssVar', () => {
  it('writes the height onto the parent even when the element appears after the first render', () => {
    //  Màn chi tiết dựng cụm tiêu đề SAU khi dữ liệu tải xong — `useRef` + effect sẽ hụt.
    const { getByTestId, rerender } = render(<Probe show={false} />)
    expect(getByTestId('parent').style.getPropertyValue('--probe-h')).toBe('')

    rerender(<Probe show />)
    //  jsdom không dàn trang nên chiều cao là 0, nhưng biến phải có mặt và đúng đơn vị.
    expect(getByTestId('parent').style.getPropertyValue('--probe-h')).toBe('0px')
  })

  it('removes the variable when the element goes away, so a stale offset never lingers', () => {
    const { getByTestId, rerender } = render(<Probe show />)
    expect(getByTestId('parent').style.getPropertyValue('--probe-h')).toBe('0px')

    rerender(<Probe show={false} />)
    expect(getByTestId('parent').style.getPropertyValue('--probe-h')).toBe('')
  })
})
