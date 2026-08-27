import { ensureVisibleAgainst } from './color-hue'
import type { ThemeModeColors, ThemePresetColors } from './theme-types'

/**
 * Dựng khối CSS của một bảng màu, gồm CẢ hai chế độ nền một lượt.
 *
 * ## Vì sao sinh CSS thay vì ghi `style` thẳng lên `<html>`
 * Ghi biến vào `documentElement.style` thì mỗi lần người dùng bấm Sáng/Tối lại
 * phải chạy JS ghi lại toàn bộ biến — mà `next-themes` chỉ đổi class `.dark`,
 * không báo cho ai cả. Sinh sẵn hai khối `html:root` + `html.dark:root` để CSS
 * tự chọn, JS không phải xen vào lúc đổi chế độ nền; hiệu ứng loang của
 * View Transitions cũng chạy đúng vì màu đổi trong CÙNG một khung hình.
 *
 * ## Vì sao là `html:root` chứ không phải `:root`
 * Độ ưu tiên. `index.css` khai `:root` (0,1,0) và `.dark` (0,1,0); trong chế độ
 * phát triển Vite chèn/ghép lại thẻ style theo thứ tự không đoán trước được, nên
 * dựa vào "khối nào đứng sau thì thắng" là hên xui. `html:root` (0,1,1) và
 * `html.dark:root` (0,2,1) luôn thắng, khỏi phụ thuộc thứ tự.
 */

/** Biến MÀU của shadcn: chép thẳng từ bảng màu, khóa nào thiếu thì bỏ qua. */
const PASSTHROUGH_KEYS = [
  'background',
  'foreground',
  'card',
  'card-foreground',
  'popover',
  'popover-foreground',
  'primary',
  'primary-foreground',
  'secondary',
  'secondary-foreground',
  'muted',
  'muted-foreground',
  'accent',
  'accent-foreground',
  'destructive',
  'destructive-foreground',
  'border',
  'input',
  'ring',
  'chart-1',
  'chart-2',
  'chart-3',
  'chart-4',
  'chart-5',
  'sidebar',
  'sidebar-foreground',
  'sidebar-primary',
  'sidebar-primary-foreground',
  'sidebar-accent',
  'sidebar-accent-foreground',
  'sidebar-border',
  'sidebar-ring',
  //  ⚠️ CỐ Ý KHÔNG có `radius`. Bảng màu chỉ đổi MÀU, không đổi hình dạng.
  //  Bán kính bo góc do `index.css` giữ (0.5rem) và mọi bảng màu dùng chung:
  //  bo góc là một phần của bố cục chứ không phải của bảng màu — đổi nó thì
  //  ô nhập, nút, thẻ và ô của các bảng dòng chứng từ lệch nhau theo từng
  //  lựa chọn giao diện, mà bề rộng cột thì đã cân sẵn theo bán kính hiện tại.
] as const

/**
 * Tỉ lệ trộn của bốn nền hàng bảng, tính theo phần của `--card` giữ lại.
 *
 * Khai riêng vì thẻ chọn bảng màu vẽ lại đúng cái bảng này ở dạng thu nhỏ
 * (`theme-preset-card.tsx`) — hai chỗ tự gõ số thì sớm muộn lệch nhau, và lệch
 * kiểu đó thì bản xem trước nói dối chính cái nó đang xem trước.
 */
export const ROW_MIX = {
  head: 0.88,
  stripe: 0.95,
  hover: 0.82,
  selected: 0.68,
} as const

/**
 * Token RIÊNG của DEGO mà tweakcn không có. Bảng màu nào tự khai thì lấy giá trị
 * khai (bảng màu DEGO khai đủ để giữ nguyên bộ màu gốc đã kiểm mù màu); còn lại
 * suy ra từ chính bảng màu đó bằng `color-mix`, để không bảng màu nào rơi lại
 * màu xanh DEGO trong khi cả trang đã đổi tông.
 *
 * ⚠️ CỐ Ý KHÔNG suy ra `--success` · `--warning` · `--info`: đó là màu NGỮ NGHĨA
 * (đã duyệt / chờ duyệt / thông tin), xanh-lá-là-đã-duyệt phải đúng ở mọi bảng
 * màu. Chúng nằm nguyên trong `index.css` và không bảng màu nào chạm tới.
 *
 * ⚠️ Cũng KHÔNG có `--brand-green`: nó là màu xanh lá trong LOGO DEGO, hiện
 * không component nào dùng (chỉ được khai trong `index.css`). Từng thử map sang
 * `--chart-3` và ở bảng màu Claude nền tối nó ra gần như đen — suy ra một token
 * không ai đọc, để rồi ra màu sai, là lỗ hổng chờ ngày có người dùng tới nó.
 */
const DERIVED_TOKENS: Record<string, string> = {
  //  Nền trang: lệch khỏi `--background` đúng một bậc để thẻ nội dung nổi lên,
  //  KHÔNG lấy `--secondary` (xem chú thích `--canvas` trong `index.css`).
  canvas: 'color-mix(in oklab, var(--background) 95%, var(--foreground))',
  //  Nền các HÀNG của bảng danh sách. Cả năm suy ra từ `--card` (nền hàng lẻ) nên
  //  một cái bảng luôn nằm gọn trong MỘT họ màu; trộn với `--foreground` thì tự
  //  đúng hướng ở cả hai chế độ nền (nền sáng thì tối đi, nền tối thì sáng lên),
  //  khỏi phải khai riêng công thức cho `.dark`.
  //
  //  Hover và hàng đang chọn trộn với `--primary` chứ không với `--foreground`:
  //  đó là phản hồi thao tác, phải nhận ra ngay là "hệ thống đang đáp lại tôi",
  //  nên nó mượn màu nhấn của bảng màu thay vì đậm nhạt thêm một bậc.
  'row-head': `color-mix(in oklab, var(--card) ${ROW_MIX.head * 100}%, var(--foreground))`,
  'row-head-foreground': 'var(--foreground)',
  'row-stripe': `color-mix(in oklab, var(--card) ${ROW_MIX.stripe * 100}%, var(--foreground))`,
  'row-hover': `color-mix(in oklab, var(--card) ${ROW_MIX.hover * 100}%, var(--primary))`,
  'row-selected': `color-mix(in oklab, var(--card) ${ROW_MIX.selected * 100}%, var(--primary))`,
  //  `--navy` là màu CHỮ ĐẬM (hơn trăm chỗ dùng `text-navy`), không phải màu nền
  //  thương hiệu — nên nó đi theo `--foreground`, sáng hay tối đều đọc được.
  navy: 'var(--foreground)',
  'navy-deep': 'color-mix(in oklab, var(--foreground) 88%, var(--background))',
  'teal-dark': 'color-mix(in oklab, var(--primary) 80%, #000)',
  'sky-soft': 'color-mix(in oklab, var(--primary) 55%, #fff)',
  'chart-neutral': 'color-mix(in oklab, var(--muted-foreground) 45%, var(--background))',
  'chart-track': 'color-mix(in oklab, var(--chart-1) 22%, var(--background))',
  'chart-grid': 'color-mix(in oklab, var(--border) 65%, var(--background))',
}

/** Màu cột biểu đồ — nhóm duy nhất bị chuẩn hoá trước khi ghi ra. */
const CHART_KEYS = ['chart-1', 'chart-2', 'chart-3', 'chart-4', 'chart-5'] as const

/**
 * Tỉ số tương phản tối thiểu giữa CỘT biểu đồ và nền thẻ chứa nó.
 *
 * 2:1 là ngưỡng "nhìn thấy được", không phải ngưỡng đọc chữ (4.5:1) — cột là
 * mảng màu đặc lớn chứ không phải nét chữ mảnh. Đặt cao hơn thì phải bóp méo
 * màu của gần hết bảng màu; đặt thấp hơn thì vẫn còn cột chìm.
 */
const CHART_MIN_CONTRAST = 2

/** Dựng các dòng biến cho MỘT chế độ nền. `solidDark` xem chú thích bên dưới. */
function buildVarLines(colors: ThemeModeColors, solidDark: string): string[] {
  const lines: string[] = []
  //  Cột biểu đồ nằm trong THẺ, không nằm trên nền trang — so với `card`.
  const chartBackground = colors.card ?? colors.background

  for (const key of PASSTHROUGH_KEYS) {
    const value = colors[key]
    if (!value) continue

    const isChart = (CHART_KEYS as readonly string[]).includes(key)
    lines.push(
      `  --${key}: ${
        isChart && chartBackground
          ? ensureVisibleAgainst(value, chartBackground, CHART_MIN_CONTRAST)
          : value
      };`,
    )
  }

  for (const [key, formula] of Object.entries(DERIVED_TOKENS)) {
    const value = colors[key as keyof ThemeModeColors]
    lines.push(`  --${key}: ${value ?? formula};`)
  }

  //  Nền navy ĐẶC (ảnh đại diện, lớp phủ, bảng thương hiệu màn đăng nhập) — luôn
  //  là màu TỐI ở cả hai chế độ, vì chữ đè lên nó luôn màu trắng. Lấy màu nền
  //  chế độ tối của chính bảng màu để nó vẫn cùng tông với phần còn lại.
  lines.push(`  --navy-solid: ${colors['navy-solid'] ?? solidDark};`)

  return lines
}

/**
 * Trả về đoạn CSS đầy đủ của bảng màu. Chuỗi rỗng nghĩa là "dùng nguyên
 * `index.css`" — không bảng màu nào hiện trả về vậy, nhưng người gọi nên coi
 * chuỗi rỗng là hợp lệ và chỉ cần gỡ thẻ style đi.
 */
export function buildThemeCss(preset: ThemePresetColors): string {
  const solidDark = preset.dark.background ?? '#0f172a'
  const light = buildVarLines(preset.light, solidDark).join('\n')
  const dark = buildVarLines(preset.dark, solidDark).join('\n')

  return `html:root {\n${light}\n}\n\nhtml.dark:root {\n${dark}\n}\n`
}
