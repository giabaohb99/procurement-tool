import { render, screen } from '@testing-library/react'
import { toast } from 'sonner'
import { describe, expect, it, vi } from 'vitest'

import { Toaster } from './sonner'

//  `next-themes` không có provider trong test — chỉ cần nó trả về một theme.
vi.mock('next-themes', () => ({ useTheme: () => ({ theme: 'light' }) }))

/**
 * Dựng Toaster rồi bắn MỘT bóng thông báo, trả về thẻ toaster.
 *
 * Phải có bóng thật: sonner không vẽ gì cả khi hàng đợi rỗng, nên
 * `[data-sonner-toaster]` chưa tồn tại — hỏi ngay sau `render` là hỏi hụt.
 */
async function dungVoiMotBong(props: Parameters<typeof Toaster>[0] = {}) {
  render(<Toaster closeButton {...props} />)
  toast('Không xuất được danh sách. Thử lọc bớt rồi xuất lại.')
  const text = await screen.findByText(/Không xuất được danh sách/)

  const thanh = document.querySelector('[data-sonner-toaster]')
  if (!(thanh instanceof HTMLElement)) throw new Error('không dựng được thẻ toaster')
  return { thanh, khung: text.closest('[data-sonner-toast]') }
}

describe('Toaster', () => {
  it('nút đóng nằm bên PHẢI và ở TRONG khung, không phải góc trái treo ra ngoài', async () => {
    //  Khách báo 25/08/2026: nút X của bóng thông báo treo lơ lửng ngoài khung,
    //  góc trên bên trái, đè lên thanh trên cùng của trang.
    //  Mặc định của sonner (đo được trong trình duyệt) là:
    //    --toast-close-button-start: 0 · --toast-close-button-end: unset
    //    --toast-close-button-transform: translate(-35%, -35%)
    //  tức bám mép TRÁI rồi kéo ngược RA NGOÀI. Đảo lại: bỏ `start`, ghim
    //  `end: 0`, và transform phải kéo VÀO TRONG (x âm = sang trái, y dương =
    //  xuống dưới) chứ không được âm cả hai như bản gốc.
    const { thanh } = await dungVoiMotBong()

    expect(thanh.style.getPropertyValue('--toast-close-button-start').trim()).toBe('unset')
    expect(thanh.style.getPropertyValue('--toast-close-button-end').trim()).toBe('0')

    const transform = thanh.style.getPropertyValue('--toast-close-button-transform')
    const [x, y] = [...transform.matchAll(/(-?\d+(?:\.\d+)?)%/g)].map((m) => Number(m[1]))
    expect(x).toBeLessThan(0) //  kéo sang TRÁI, vào trong khung
    expect(y).toBeGreaterThan(0) //  kéo XUỐNG, vào trong khung
  })

  it('chừa lề phải cho nút đóng, kẻo chữ chạy xuống dưới nút', async () => {
    const { khung } = await dungVoiMotBong()
    //  `!` (important) là cố ý, không phải thói quen xấu: luật gốc của sonner là
    //  `[data-sonner-toast][data-styled="true"]` — đặc tả 0,2,0, cao hơn một lớp
    //  Tailwind thường, mà lớp tiện ích lại còn nằm trong `@layer` nên thua cả
    //  luật không-lớp. Bỏ dấu `!` đi là lề biến mất và chữ chui xuống dưới nút X.
    expect(khung?.className).toMatch(/\bpr-9!/)
  })

  it('props của bên gọi vẫn thắng — `style` riêng không bị ba biến kia nuốt', async () => {
    //  `{...props}` từng đứng CUỐI nên nó ghi đè trọn gói `style` và
    //  `toastOptions` của chính component này. Nay props đứng trước và hai thứ
    //  đó được trộn tay; bài này giữ cho lần dọn sau không lỡ tay đảo lại.
    const { thanh } = await dungVoiMotBong({ style: { '--width': '420px' } as React.CSSProperties })

    expect(thanh.style.getPropertyValue('--width').trim()).toBe('420px')
    expect(thanh.style.getPropertyValue('--toast-close-button-end').trim()).toBe('0')
  })
})
