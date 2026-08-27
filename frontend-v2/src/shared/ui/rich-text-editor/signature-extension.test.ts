import { describe, expect, it } from 'vitest'

import {
  SIGNATURE_ANCHOR_CLASS,
  SIGNATURE_CLASS,
  SIGNATURE_DEFAULT_WIDTH,
  SIGNATURE_MAX_WIDTH,
  SIGNATURE_MIN_WIDTH,
  clampNumber,
  clampOffset,
  normalizeRotation,
  readPixels,
  readRotation,
  ROTATE_SNAP_DEGREES,
  snapToRightAngle,
  signatureStyle,
  type SignatureAttributes,
} from './signature-extension'

function attrs(phan: Partial<SignatureAttributes> = {}): SignatureAttributes {
  return { src: 'x.png', left: 0, top: 0, width: 180, height: 0, rotate: 0, ...phan }
}

describe('clampNumber', () => {
  it('ép về đúng khoảng cho phép', () => {
    expect(clampNumber(1000, SIGNATURE_MIN_WIDTH, SIGNATURE_MAX_WIDTH, 180)).toBe(SIGNATURE_MAX_WIDTH)
    expect(clampNumber(1, SIGNATURE_MIN_WIDTH, SIGNATURE_MAX_WIDTH, 180)).toBe(SIGNATURE_MIN_WIDTH)
  })

  it('đọc được cả chuỗi, vì thuộc tính HTML luôn về dạng chuỗi', () => {
    expect(clampNumber('240', 48, 600, 180)).toBe(240)
  })

  it('giá trị hỏng thì trả về mặc định chứ không trả NaN', () => {
    //  Từng để lọt `NaN` xuống `style` làm chữ ký biến mất không dấu vết.
    expect(clampNumber('rất to', 48, 600, 180)).toBe(180)
    expect(clampNumber(null, 48, 600, 180)).toBe(180)
  })
})

describe('normalizeRotation', () => {
  it('đưa góc âm và góc vượt vòng về 0–359', () => {
    expect(normalizeRotation(-90)).toBe(270)
    expect(normalizeRotation(450)).toBe(90)
    expect(normalizeRotation(360)).toBe(0)
  })

  it('giá trị hỏng thì coi như không xoay', () => {
    expect(normalizeRotation('xoay tí')).toBe(0)
  })
})

describe('readPixels', () => {
  it('đọc đúng số px của từng thuộc tính trong chuỗi style', () => {
    const style = 'position:absolute;left:370px;top:-30px;width:240px'
    expect(readPixels(style, 'left')).toBe(370)
    expect(readPixels(style, 'width')).toBe(240)
  })

  it('đọc được số ÂM — chữ ký hay được kéo lên trên mốc neo', () => {
    expect(readPixels('top:-30px', 'top')).toBe(-30)
  })

  it('không có thì trả null để nơi gọi tự quyết định giá trị thay', () => {
    expect(readPixels('left:10px', 'top')).toBeNull()
    expect(readPixels(null, 'top')).toBeNull()
  })
})

describe('readRotation', () => {
  it('đọc góc từ transform', () => {
    expect(readRotation('transform:rotate(135deg)')).toBe(135)
    expect(readRotation('transform:rotate(-45deg)')).toBe(315)
  })

  it('không có transform thì là 0', () => {
    expect(readRotation('left:10px')).toBe(0)
  })
})

describe('clampOffset', () => {
  //  Tờ A4 rộng 794px; mốc neo đứng ở 100px tính từ mép trái; chữ ký rộng 180px.
  const GIAY = 794
  const NEO = 100
  const RONG = 180

  it('trong tờ giấy thì để nguyên', () => {
    expect(clampOffset(300, NEO, RONG, GIAY)).toBe(300)
  })

  it('kéo quá mép TRÁI thì dừng ngay mép, không lọt ra ngoài', () => {
    //  Đúng lỗi phải vá: kéo sang trái là chữ ký trôi qua khung mục lục, in ra
    //  thì mất hẳn mà trên màn hình vẫn thấy.
    expect(clampOffset(-500, NEO, RONG, GIAY)).toBe(-NEO)
  })

  it('kéo quá mép PHẢI thì mép phải chữ ký dừng đúng mép giấy', () => {
    const lech = clampOffset(9999, NEO, RONG, GIAY)
    expect(NEO + lech + RONG).toBe(GIAY)
  })

  it('sát mép vẫn được phép — không chừa lề thừa', () => {
    expect(clampOffset(-NEO, NEO, RONG, GIAY)).toBe(-NEO)
    expect(clampOffset(GIAY - NEO - RONG, NEO, RONG, GIAY)).toBe(GIAY - NEO - RONG)
  })

  it('chữ ký to hơn cả tờ giấy thì dí về mép, không trả khoảng rỗng', () => {
    //  `max < min`: không có chỗ nào thoả cả hai mép. Không chốt nhánh này thì
    //  Math.min/max trả ngược và chữ ký nhảy ra ngoài phía đối diện.
    expect(clampOffset(0, NEO, 2000, GIAY)).toBe(-NEO)
  })
})

describe('snapToRightAngle', () => {
  it('hút về góc vuông khi đã đủ gần', () => {
    expect(snapToRightAngle(3)).toBe(0)
    expect(snapToRightAngle(87)).toBe(90)
    expect(snapToRightAngle(184)).toBe(180)
    expect(snapToRightAngle(274)).toBe(270)
  })

  it('gần 360° thì về 0 chứ không trả 360', () => {
    //  Trả 360 là `style` ghi ra `rotate(360deg)` — đúng về hình nhưng lệch với
    //  giá trị đã chuẩn hoá 0–359, so sánh ở nơi khác sẽ sai.
    expect(snapToRightAngle(358)).toBe(0)
  })

  it('ngoài khoảng hút thì giữ NGUYÊN góc người dùng đặt', () => {
    //  Nhiều người ký nghiêng thật; hút quá tay là không đặt nghiêng được nữa.
    expect(snapToRightAngle(45)).toBe(45)
    expect(snapToRightAngle(12)).toBe(12)
  })

  it('đúng ngay mép khoảng hút thì vẫn hút, quá một độ thì thôi', () => {
    expect(snapToRightAngle(ROTATE_SNAP_DEGREES)).toBe(0)
    expect(snapToRightAngle(ROTATE_SNAP_DEGREES + 1)).toBe(ROTATE_SNAP_DEGREES + 1)
  })

  it('nới được khoảng hút qua tham số', () => {
    expect(snapToRightAngle(12, 15)).toBe(0)
  })
})

describe('signatureStyle', () => {
  it('luôn đặt tuyệt đối, và ghi ra đúng giá trị vừa đặt', () => {
    const style = signatureStyle(attrs({ left: 360, top: -30, width: 200, height: 80 }))
    expect(style).toContain('position:absolute')
    expect(style).toContain('left:360px')
    expect(style).toContain('top:-30px')
    expect(style).toContain('width:200px')
    expect(style).toContain('height:80px')
  })

  it('chưa biết chiều cao thì KHÔNG ghi height, để ảnh tự giữ tỷ lệ', () => {
    expect(signatureStyle(attrs({ height: 0 }))).not.toContain('height')
  })

  it('không xoay thì không ghi transform — chuỗi style càng ngắn càng ít chỗ hỏng', () => {
    expect(signatureStyle(attrs({ rotate: 0 }))).not.toContain('rotate')
    expect(signatureStyle(attrs({ rotate: 135 }))).toContain('transform:rotate(135deg)')
  })

  it('đọc lại được chính chuỗi mình vừa ghi ra', () => {
    //  Đây là vòng đời thật: node ghi ra style → lưu xuống DB → mở lại parse từ
    //  chính chuỗi đó. Hai đầu lệch nhau là đặt xong thấy một kiểu, mở lại thấy
    //  một kiểu.
    const goc = attrs({ left: 360, top: -30, width: 200, height: 80, rotate: 135 })
    const style = signatureStyle(goc)
    expect(readPixels(style, 'left')).toBe(goc.left)
    expect(readPixels(style, 'top')).toBe(goc.top)
    expect(readPixels(style, 'width')).toBe(goc.width)
    expect(readPixels(style, 'height')).toBe(goc.height)
    expect(readRotation(style)).toBe(goc.rotate)
  })

  it('KHÔNG chèn pointer-events — bản in cần bôi đen được chữ nằm dưới', () => {
    expect(signatureStyle(attrs())).not.toContain('pointer-events')
  })
})

describe('hằng số class', () => {
  it('mốc neo và ảnh mang hai class KHÁC nhau', () => {
    //  Bộ đọc lại nhận diện bằng `span.doc-signature-anchor`. Trùng tên class
    //  là mọi ảnh minh hoạ trong văn bản biến thành chữ ký khi mở lại.
    expect(SIGNATURE_ANCHOR_CLASS).not.toBe(SIGNATURE_CLASS)
  })

  it('bề rộng mặc định nằm trong khoảng cho phép', () => {
    expect(SIGNATURE_DEFAULT_WIDTH).toBeGreaterThanOrEqual(SIGNATURE_MIN_WIDTH)
    expect(SIGNATURE_DEFAULT_WIDTH).toBeLessThanOrEqual(SIGNATURE_MAX_WIDTH)
  })
})
