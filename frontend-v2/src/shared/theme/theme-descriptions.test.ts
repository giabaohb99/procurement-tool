import { describe, expect, it } from 'vitest'

import { measureColor } from './color-hue'
import { colorMatchesWord, findFirstColorWord } from './color-words'
import { themePresets } from './theme-presets'

/**
 * HỢP ĐỒNG MÔ TẢ BẢNG MÀU.
 *
 * Người dùng chọn bảng màu bằng cách ĐỌC mô tả — nên mô tả sai màu là dẫn người
 * ta chọn nhầm. Bản mô tả đầu tiên viết theo TÊN bảng màu chứ không mở dữ liệu
 * ra xem, và sai 12/42 chỗ: *Doom 64* ghi "cam lửa" trong khi màu chính là đỏ
 * `#b71c1c`, *Retro Arcade* ghi "xanh ngọc" trong khi màu chính là hồng
 * `#d33682`, *Darkmatter* ghi "tím than" trong khi chế độ sáng là cam trên nền
 * trắng.
 *
 * Hai luật, cả hai kiểm trên CHẾ ĐỘ SÁNG (mô tả nói về diện mạo mặc định):
 *
 * 1. **Từ màu ĐẦU TIÊN của mô tả phải là màu của `primary`.** Mô tả mở đầu bằng
 *    màu gì thì người đọc hiểu đó là màu chủ đạo.
 * 2. **Cụm `nền <từ màu>` phải khớp `background`.**
 *
 * Mô tả không chứa từ màu nào thì bỏ qua luật 1 — nhưng đừng lạm dụng, mô tả
 * không nói màu thì gần như vô dụng với người đang chọn.
 */

/** Bóc từ màu đứng ngay sau chữ "nền", nếu có. */
function findBackgroundClaim(description: string): string | null {
  const match = description.toLowerCase().match(/nền\s+(.{0,20})/)
  return match ? match[1] : null
}

describe('mô tả bảng màu nói đúng màu thật', () => {
  it('từ màu đầu tiên của mô tả khớp màu chính (primary) ở chế độ sáng', () => {
    const wrong: string[] = []

    for (const preset of themePresets) {
      const word = findFirstColorWord(preset.description)
      if (!word) continue

      const primary = preset.light.primary
      if (!primary) {
        wrong.push(`${preset.id}: thiếu light.primary`)
        continue
      }

      if (!colorMatchesWord(primary, word)) {
        const { hue, chroma, lightness } = measureColor(primary)
        wrong.push(
          `${preset.id}: mô tả nói "${word.word}" nhưng primary ${primary} có ` +
            `H=${hue} chroma=${chroma.toFixed(2)} L=${lightness} — «${preset.description}»`,
        )
      }
    }

    expect(wrong).toEqual([])
  })

  it('mô tả nói "nền <màu>" thì nền ở chế độ sáng phải đúng màu đó', () => {
    const wrong: string[] = []

    for (const preset of themePresets) {
      const claim = findBackgroundClaim(preset.description)
      if (!claim) continue

      const word = findFirstColorWord(claim)
      if (!word) continue

      const background = preset.light.background
      if (!background) {
        wrong.push(`${preset.id}: thiếu light.background`)
        continue
      }

      if (!colorMatchesWord(background, word)) {
        const { hue, chroma, lightness } = measureColor(background)
        wrong.push(
          `${preset.id}: mô tả nói nền "${word.word}" nhưng background ${background} có ` +
            `H=${hue} chroma=${chroma.toFixed(2)} L=${lightness} — «${preset.description}»`,
        )
      }
    }

    expect(wrong).toEqual([])
  })

  it('mô tả nào cũng nói được ít nhất một từ màu — mô tả không có màu thì vô dụng lúc chọn', () => {
    const silent = themePresets
      .filter((preset) => !findFirstColorWord(preset.description))
      .map((preset) => `${preset.id}: «${preset.description}»`)

    expect(silent).toEqual([])
  })

  it('không mô tả nào hứa "nền tối" — mọi bảng màu đều có nền tối nên câu đó không phân biệt được gì', () => {
    //  Đo được: nền chế độ tối của cả 42 bảng đều có độ sáng ≤ 19/100. Ghi
    //  "trên nền tối" vào một bảng cụ thể làm người dùng tưởng chỉ bảng đó mới
    //  tối, mà lại còn sai với diện mạo mặc định (chế độ sáng).
    const overclaiming = themePresets
      .filter((preset) => /nền tối/i.test(preset.description))
      .map((preset) => preset.id)

    expect(overclaiming).toEqual([])
  })

  it('nền ở chế độ tối thật sự tối với MỌI bảng màu', () => {
    const notDark = themePresets
      .filter((preset) => measureColor(preset.dark.background ?? '#000000').lightness > 25)
      .map((preset) => `${preset.id}: ${preset.dark.background}`)

    expect(notDark).toEqual([])
  })
})
