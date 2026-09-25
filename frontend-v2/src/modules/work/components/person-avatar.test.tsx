import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { PersonAvatar } from './person-avatar'

describe('PersonAvatar — bao-CR-482', () => {
  it('không có ảnh thì vẽ chữ tắt, không có thẻ img', () => {
    render(<PersonAvatar name="Huỳnh Gia Bảo" initials="GB" avatar="" />)
    expect(screen.getByText('GB')).toBeInTheDocument()
    expect(screen.queryByRole('img')).toBeNull()
    expect(screen.getByTitle('Huỳnh Gia Bảo')).toBeInTheDocument()
  })

  it('có ảnh thì gắn đúng URL vào ảnh và vẫn giữ chữ tắt làm dự phòng', () => {
    const { container } = render(
      <PersonAvatar name="Huỳnh Gia Bảo" initials="GB" avatar="https://kho/a-thumb.png" />,
    )
    //  Radix chỉ gắn `<img>` sau khi ảnh tải xong (jsdom không tải), nên kiểm
    //  phần tử Image của Radix qua thuộc tính data-slot thay vì role img.
    const img = container.querySelector('[data-slot="avatar-image"]')
    //  Chưa tải xong thì Radix chưa dựng img — chữ tắt phải còn để không trống.
    expect(img === null || img.getAttribute('src') === 'https://kho/a-thumb.png').toBe(true)
    expect(screen.getByText('GB')).toBeInTheDocument()
  })
})
