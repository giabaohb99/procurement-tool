/**
 * Đo màu để KIỂM mô tả bảng màu có nói đúng màu thật không.
 *
 * Sinh ra vì mô tả tiếng Việt của 42 bảng màu ban đầu viết theo TÊN bảng màu
 * chứ không theo màu thật, và sai thật: `doom-64` ghi "cam lửa" trong khi màu
 * chính là đỏ `#b71c1c`, `retro-arcade` ghi "xanh ngọc" trong khi màu chính là
 * hồng `#d33682`. Người dùng chọn theo mô tả, nên mô tả sai là chọn nhầm.
 *
 * Mọi màu trong `theme-presets.ts` đều là HEX (bảng `vercel` vốn dùng `oklch`
 * đã được quy về hex) nên ở đây chỉ cần đọc hex — không kéo thêm thư viện màu.
 */

export interface ColorMetrics {
  /** Góc màu 0–359. Vô nghĩa khi `chroma` gần 0. */
  hue: number
  /**
   * Độ rực, 0–1, đo bằng `(max − min) / 255` của ba kênh RGB.
   *
   * CỐ Ý không dùng độ bão hòa HSL: ở hai đầu sáng/tối HSL thổi phồng con số vô
   * lý — `#f8fafc` (gần như trắng, lệch kênh đúng 4/255) ra S = 40%, đủ để một
   * phép kiểm "màu này có trung tính không" trả lời sai.
   */
  chroma: number
  /** Độ sáng 0–100, theo HSL. */
  lightness: number
}

/** Đọc `#rgb` hoặc `#rrggbb` thành ba kênh 0–255. Sai định dạng thì ném lỗi. */
export function parseHexColor(value: string): [number, number, number] {
  const raw = value.trim().replace(/^#/, '')
  const full = raw.length === 3 ? raw.replace(/./g, (c) => c + c) : raw
  if (!/^[0-9a-fA-F]{6}$/.test(full)) {
    throw new Error(`Màu không phải hex hợp lệ: "${value}"`)
  }
  return [
    parseInt(full.slice(0, 2), 16),
    parseInt(full.slice(2, 4), 16),
    parseInt(full.slice(4, 6), 16),
  ]
}

export function measureColor(value: string): ColorMetrics {
  const [r, g, b] = parseHexColor(value)
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const delta = max - min

  let hue = 0
  if (delta !== 0) {
    if (max === r) hue = ((g - b) / delta) % 6
    else if (max === g) hue = (b - r) / delta + 2
    else hue = (r - g) / delta + 4
    hue *= 60
    if (hue < 0) hue += 360
  }

  return {
    hue: Math.round(hue),
    chroma: delta / 255,
    lightness: Math.round(((max + min) / 2 / 255) * 100),
  }
}

/**
 * Dưới ngưỡng này coi là KHÔNG có màu (xám / đen / trắng / đơn sắc).
 *
 * 0.06 chọn theo dữ liệu thật: `#f8fafc` và `#eff1f5` (nền gần trắng của
 * *Clean Slate* và *Catppuccin*) nằm dưới, còn `#7c9082` (xanh xô thơm của
 * *Sage Garden*, lệch kênh 0.078) nằm trên — đúng như mắt nhìn.
 */
export const NEUTRAL_CHROMA_MAX = 0.06

export function isNeutral(value: string): boolean {
  return measureColor(value).chroma <= NEUTRAL_CHROMA_MAX
}

/** Độ chói tương đối theo WCAG, 0–1. */
export function relativeLuminance(value: string): number {
  const [r, g, b] = parseHexColor(value).map((channel) => {
    const s = channel / 255
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

/** Tỉ số tương phản WCAG giữa hai màu, 1 (trùng nhau) → 21 (đen/trắng). */
export function contrastRatio(a: string, b: string): number {
  const la = relativeLuminance(a)
  const lb = relativeLuminance(b)
  const [hi, lo] = la > lb ? [la, lb] : [lb, la]
  return (hi + 0.05) / (lo + 0.05)
}

function hslToHex(hue: number, saturation: number, lightness: number): string {
  const s = saturation / 100
  const l = lightness / 100
  const c = (1 - Math.abs(2 * l - 1)) * s
  const x = c * (1 - Math.abs(((hue / 60) % 2) - 1))
  const m = l - c / 2
  const sector = Math.floor(((hue % 360) + 360) % 360 / 60)
  const rgb = [
    [c, x, 0],
    [x, c, 0],
    [0, c, x],
    [0, x, c],
    [x, 0, c],
    [c, 0, x],
  ][sector]
  return (
    '#' +
    rgb
      .map((channel) => Math.round((channel + m) * 255).toString(16).padStart(2, '0'))
      .join('')
  )
}

/** Độ bão hoà HSL (0–100). Chỉ dùng để DỰNG LẠI màu, không dùng để phán "có màu không". */
function hslSaturation(value: string): number {
  const [r, g, b] = parseHexColor(value)
  const max = Math.max(r, g, b) / 255
  const min = Math.min(r, g, b) / 255
  const l = (max + min) / 2
  if (max === min) return 0
  return ((max - min) / (1 - Math.abs(2 * l - 1))) * 100
}

/**
 * Kéo `color` sáng lên hoặc tối đi cho tới khi nổi được trên `background`.
 *
 * GIỮ NGUYÊN góc màu và độ bão hoà — chỉ đổi độ sáng, nên cột biểu đồ vẫn đúng
 * tông của bảng màu, chỉ là nhìn thấy được.
 *
 * Cần cái này vì nhiều bảng màu nhập về có cột biểu đồ chìm hẳn vào nền thẻ:
 * *Caffeine* mất 3/4 cột ở nền sáng (`#ffdfb5`, `#e8e8e8`, `#ffe6c4` trên thẻ
 * `#fcfcfc`), *Claude* mất 2 cột ở CẢ hai chế độ nền. Biểu đồ chi phí theo tháng
 * ở Tổng quan Thu mua khi đó chỉ còn một cột nhìn thấy được.
 */
export function ensureVisibleAgainst(
  color: string,
  background: string,
  minRatio = 2,
): string {
  if (contrastRatio(color, background) >= minRatio) return color

  const { hue } = measureColor(color)
  const saturation = hslSaturation(color)
  const startLightness = measureColor(color).lightness
  //  Nền sáng thì dìm màu xuống, nền tối thì đẩy màu lên. Đi theo hướng nào cho
  //  tương phản tăng — đi ngược là càng lúc càng chìm.
  const step = relativeLuminance(background) > 0.5 ? -2 : 2

  for (let lightness = startLightness + step; lightness >= 0 && lightness <= 100; lightness += step) {
    const candidate = hslToHex(hue, saturation, lightness)
    if (contrastRatio(candidate, background) >= minRatio) return candidate
  }

  //  Không có độ sáng nào đạt: rơi về đen hoặc trắng, tuỳ nền.
  return step < 0 ? '#000000' : '#ffffff'
}

/**
 * Trộn hai màu hex theo tỉ lệ, dùng cho BẢN XEM TRƯỚC của thẻ chọn bảng màu.
 *
 * `baseRatio` là phần của `base` (0–1), giống hệt cú pháp
 * `color-mix(in oklab, base <baseRatio>%, tint)` mà `build-theme-css.ts` sinh ra.
 *
 * ⚠️ Đây là phép XẤP XỈ: trộn trong không gian tuyến tính (bỏ gamma rồi trộn rồi
 * bọc gamma lại) chứ không trộn trong oklab như trình duyệt. Chấp nhận được vì
 * chỗ dùng là một hình 128px trên thẻ chọn, không phải màu vẽ ra màn hình thật —
 * màu thật do CSS `color-mix` tính. Lệch chủ yếu ở sắc, độ sáng thì gần khít.
 */
export function mixHexColors(base: string, tint: string, baseRatio: number): string {
  const toLinear = (channel: number) => {
    const value = channel / 255
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
  }
  const toSrgb = (value: number) => {
    const encoded = value <= 0.0031308 ? value * 12.92 : 1.055 * value ** (1 / 2.4) - 0.055
    return Math.round(Math.min(1, Math.max(0, encoded)) * 255)
  }

  const baseChannels = parseHexColor(base)
  const tintChannels = parseHexColor(tint)
  const ratio = Math.min(1, Math.max(0, baseRatio))

  const mixed = baseChannels.map((channel, index) =>
    toSrgb(toLinear(channel) * ratio + toLinear(tintChannels[index]) * (1 - ratio)),
  )

  return `#${mixed.map((channel) => channel.toString(16).padStart(2, '0')).join('')}`
}
