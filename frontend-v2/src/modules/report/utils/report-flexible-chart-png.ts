import { toDateInputValue } from '@/shared/utils/format-date'

/**
 * «Tải ảnh PNG» của biểu đồ linh hoạt (duoc-CR-688): SVG của recharts → ảnh → canvas → PNG.
 *
 * ⚠️ SVG của recharts tô màu bằng `var(--chart-1)`… — đem SVG ra ngoài trang (thành ảnh) là
 * mất bảng CSS nên mọi biến màu thành đen. Phải chép KIỂU ĐÃ TÍNH (`getComputedStyle`) của
 * từng phần tử vào thuộc tính `style` của bản sao trước khi tuần tự hóa.
 */

/** Thuộc tính trình bày cần chép từ kiểu đã tính sang bản sao SVG. */
const INLINE_PROPS = [
  'fill',
  'fill-opacity',
  'stroke',
  'stroke-width',
  'stroke-dasharray',
  'stroke-opacity',
  'opacity',
  'font-family',
  'font-size',
  'font-weight',
  'text-anchor',
  'dominant-baseline',
] as const

const SCALE = 2
const PADDING = 16
const TITLE_HEIGHT = 28
const LEGEND_ROW_HEIGHT = 20

export interface ChartPngLegendItem {
  label: string
  /** Màu CSS bất kỳ (kể cả `var(--chart-1)`) — được giải ra màu thật trước khi vẽ. */
  color: string
}

export interface ChartPngInput {
  /** Khung bọc phần vẽ — hàm lấy `svg.recharts-surface` lớn nhất bên trong. */
  container: HTMLElement
  filename: string
  title: string
  /** Chú giải HTML không nằm trong SVG — vẽ lại thành chữ ở chân ảnh. */
  legend?: ChartPngLegendItem[]
}

/** Tên tệp `bieu-do-<slug>-<từ>-<đến>.png`; chưa có kỳ (đang tải) thì lấy hôm nay. */
export function buildChartPngFilename(
  slug: string,
  period?: { date_from: string; date_to: string },
  today: Date = new Date(),
): string {
  const from = period?.date_from ?? toDateInputValue(today)
  const to = period?.date_to ?? toDateInputValue(today)
  return `bieu-do-${slug}-${from}-${to}.png`
}

function pickLargestSvg(container: HTMLElement): SVGSVGElement | null {
  const svgs = Array.from(container.querySelectorAll<SVGSVGElement>('svg.recharts-surface'))
  let best: SVGSVGElement | null = null
  let bestArea = 0
  for (const svg of svgs) {
    const { width, height } = svg.getBoundingClientRect()
    if (width * height > bestArea) {
      best = svg
      bestArea = width * height
    }
  }
  return best
}

function inlineComputedStyles(source: Element, target: Element) {
  const computed = getComputedStyle(source)
  const style = INLINE_PROPS.map((p) => `${p}:${computed.getPropertyValue(p)}`).join(';')
  target.setAttribute('style', style)
  const sourceChildren = source.children
  const targetChildren = target.children
  for (let i = 0; i < sourceChildren.length; i += 1) {
    const s = sourceChildren[i]
    const t = targetChildren[i]
    if (s && t) inlineComputedStyles(s, t)
  }
}

/** Giải một màu CSS (biến, oklch…) ra màu trình duyệt đã tính, dùng được cho canvas. */
function resolveCssColor(color: string, host: HTMLElement): string {
  const probe = document.createElement('span')
  probe.style.color = color
  host.appendChild(probe)
  const resolved = getComputedStyle(probe).color
  probe.remove()
  return resolved || color
}

/** Nền đặc đầu tiên tính từ khung lên trên — ảnh PNG không được nền trong suốt (dán vào Word ra đen). */
function resolveBackground(el: HTMLElement): string {
  let node: HTMLElement | null = el
  while (node) {
    const bg = getComputedStyle(node).backgroundColor
    if (bg && bg !== 'transparent' && !bg.startsWith('rgba(0, 0, 0, 0')) return bg
    node = node.parentElement
  }
  return '#ffffff'
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('Không dựng được ảnh từ SVG.'))
    img.src = src
  })
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

/** Dựng và tải ảnh PNG. Ném lỗi khi không có SVG nào hoặc trình duyệt từ chối vẽ — chỗ gọi báo toast. */
export async function downloadChartPng({ container, filename, title, legend = [] }: ChartPngInput) {
  const svg = pickLargestSvg(container)
  if (!svg) throw new Error('Không tìm thấy biểu đồ để chụp.')
  const { width, height } = svg.getBoundingClientRect()
  const clone = svg.cloneNode(true) as SVGSVGElement
  inlineComputedStyles(svg, clone)
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  clone.setAttribute('width', String(width))
  clone.setAttribute('height', String(height))

  const svgUrl = URL.createObjectURL(
    new Blob([new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml;charset=utf-8' }),
  )
  try {
    const img = await loadImage(svgUrl)
    const textColor = resolveCssColor('var(--foreground)', container)
    const mutedColor = resolveCssColor('var(--muted-foreground)', container)
    const legendHeight = legend.length * LEGEND_ROW_HEIGHT
    const outW = width + PADDING * 2
    const outH = TITLE_HEIGHT + height + legendHeight + PADDING * 2

    const canvas = document.createElement('canvas')
    canvas.width = outW * SCALE
    canvas.height = outH * SCALE
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Trình duyệt không cho vẽ canvas.')
    ctx.scale(SCALE, SCALE)
    ctx.fillStyle = resolveBackground(container)
    ctx.fillRect(0, 0, outW, outH)
    ctx.fillStyle = textColor
    ctx.font = '600 15px system-ui, sans-serif'
    ctx.textBaseline = 'top'
    ctx.fillText(title, PADDING, PADDING)
    ctx.drawImage(img, PADDING, PADDING + TITLE_HEIGHT, width, height)

    ctx.font = '13px system-ui, sans-serif'
    legend.forEach((item, i) => {
      const y = PADDING + TITLE_HEIGHT + height + i * LEGEND_ROW_HEIGHT + 4
      ctx.fillStyle = resolveCssColor(item.color, container)
      ctx.fillRect(PADDING, y + 3, 10, 10)
      ctx.fillStyle = mutedColor
      ctx.fillText(item.label, PADDING + 16, y + 1)
    })

    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'))
    if (!blob) throw new Error('Trình duyệt không xuất được PNG.')
    triggerDownload(blob, filename)
  } finally {
    URL.revokeObjectURL(svgUrl)
  }
}
