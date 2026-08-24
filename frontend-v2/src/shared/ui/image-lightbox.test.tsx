import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ImageLightbox, type LightboxImage } from './image-lightbox'

const IMAGES: LightboxImage[] = [
  { url: 'a.png', name: 'Ảnh A' },
  { url: 'b.png', name: 'Ảnh B' },
  { url: 'c.png', name: 'Ảnh C' },
]

afterEach(cleanup)

describe('ImageLightbox', () => {
  it('hiện bộ đếm theo vị trí đang xem (1-based)', () => {
    render(
      <ImageLightbox
        images={IMAGES}
        index={0}
        open
        onOpenChange={vi.fn()}
        onIndexChange={vi.fn()}
      />,
    )
    expect(screen.getByText('1/3')).toBeInTheDocument()
  })

  it('bấm "Ảnh sau" thì báo vị trí kế tiếp', async () => {
    const onIndexChange = vi.fn()
    render(
      <ImageLightbox
        images={IMAGES}
        index={0}
        open
        onOpenChange={vi.fn()}
        onIndexChange={onIndexChange}
      />,
    )
    await userEvent.click(screen.getByRole('button', { name: 'Ảnh sau' }))
    expect(onIndexChange).toHaveBeenCalledWith(1)
  })

  it('ở ảnh đầu bấm "Ảnh trước" thì vòng về ảnh cuối', async () => {
    const onIndexChange = vi.fn()
    render(
      <ImageLightbox
        images={IMAGES}
        index={0}
        open
        onOpenChange={vi.fn()}
        onIndexChange={onIndexChange}
      />,
    )
    // Lỗi hay gặp: quá đầu không vòng lại mà kẹt ở 0 (hoặc ra -1).
    await userEvent.click(screen.getByRole('button', { name: 'Ảnh trước' }))
    expect(onIndexChange).toHaveBeenCalledWith(2)
  })

  it('chỉ một ảnh thì ẩn nút chuyển', () => {
    render(
      <ImageLightbox
        images={[IMAGES[0]]}
        index={0}
        open
        onOpenChange={vi.fn()}
        onIndexChange={vi.fn()}
      />,
    )
    expect(screen.queryByRole('button', { name: 'Ảnh sau' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Ảnh trước' })).not.toBeInTheDocument()
  })
})
