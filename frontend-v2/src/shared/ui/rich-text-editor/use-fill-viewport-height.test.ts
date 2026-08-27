import { describe, expect, it } from 'vitest'

import { fillRemainingHeight } from './use-fill-viewport-height'

describe('fillRemainingHeight', () => {
  it('lấy hết phần còn lại của khung cuộn, chừa một khe ở đáy', () => {
    expect(fillRemainingHeight(725, 354)).toBe(725 - 354 - 12)
  })

  it('không tụt xuống dưới sàn 320px dù khối bị đẩy sát đáy', () => {
    expect(fillRemainingHeight(725, 700)).toBe(320)
    expect(fillRemainingHeight(400, 5000)).toBe(320)
  })

  it('KHÔNG đổi khi khung cuộn bị cuộn — chỗ này từng lặp vô tận', () => {
    //  LỖI ĐÃ XẢY RA (27/08/2026): công thức cũ là `window.innerHeight - top`
    //  với `top` đo theo KHUNG NHÌN, và đo lại mỗi lần có ai cuộn. Vỏ trang cuộn
    //  xuống 33px thì `top` nhỏ đi 33px, khung cao thêm 33px, nội dung dài thêm
    //  33px, lại cuộn được thêm 33px — đo thật trên văn bản 29 trang thì nó cứ
    //  thế nâng mãi, dưới trang giấy cuối là một vùng trắng dài vô tận.
    //
    //  `elementOffset` tính từ đầu NỘI DUNG nên cuộn bao nhiêu cũng ra một số.
    const containerHeight = 725
    const offsetInContent = 354

    const heights = [0, 33, 66, 99, 264, 5000].map(() =>
      fillRemainingHeight(containerHeight, offsetInContent),
    )

    expect(new Set(heights).size).toBe(1)
  })

  it('đổi khi phần NẰM TRÊN đổi chiều cao — băng cảnh báo hiện ra thì khung thấp lại', () => {
    //  Số phải nằm TRÊN sàn 320px, không thì cả hai vế cùng bị kẹp về sàn và
    //  phép kiểm không còn kiểm gì.
    const withoutBanner = fillRemainingHeight(900, 354)
    const withBanner = fillRemainingHeight(900, 354 + 48)
    expect(withoutBanner).toBe(534)
    expect(withBanner).toBe(withoutBanner - 48)
  })
})
