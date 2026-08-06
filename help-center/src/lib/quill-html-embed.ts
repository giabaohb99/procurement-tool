import { Quill } from 'react-quill'

// Blot "mã nhúng" cho Quill — cho phép dán NGUYÊN đoạn code nhà cung cấp đưa
// (<div> + <iframe> + <script> của Guideflow, Google Sheets, Canva...).
//
// Vì sao phải bọc iframe srcdoc thay vì chèn thẳng HTML:
//   1. Quill chỉ giữ những format đã đăng ký -> thẻ/thuộc tính lạ bị lột sạch khi dán vào editor.
//   2. Nội dung bài render bằng dangerouslySetInnerHTML, mà <script> chèn qua innerHTML thì
//      trình duyệt KHÔNG chạy — script của nhà cung cấp sẽ nằm im.
// Đưa cả đoạn code vào `srcdoc` của một iframe giải quyết cả hai: trình duyệt dựng một tài liệu
// con hoàn chỉnh nên script chạy được, đồng thời CSS/JS của bên thứ ba bị nhốt trong iframe.
//
// Mã gốc lưu ở thuộc tính `data-embed` (base64) để mở lại bài vẫn dựng lại được và sửa được.

const BlockEmbed = Quill.import('blots/block/embed') as any

/** Quyền tối thiểu để embed thương mại chạy được. Nội dung do quản trị viên tự dán nên tin được. */
const SANDBOX = 'allow-scripts allow-same-origin allow-popups allow-forms allow-presentation'

export interface HtmlEmbedValue {
  /** Mã nhúng gốc người dùng dán vào. */
  code: string
  /** Chiều cao cố định (px). Bỏ trống = khung 16:9 co theo bề ngang cột nội dung. */
  height?: number | null
}

/** Bọc mã nhúng thành một trang HTML tối giản để nạp vào `srcdoc`. */
export function embedSrcDoc(code: string): string {
  return '<!doctype html><html><head><meta charset="utf-8">'
    + '<meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<base target="_blank">'
    + '<style>html,body{margin:0;padding:0;overflow:hidden;height:100%}'
    + 'body>*{max-width:100%}iframe{display:block;width:100%;height:100%;border:0}</style>'
    + `</head><body>${code}</body></html>`
}

/** base64 chịu được tiếng Việt (btoa thuần chỉ nhận latin1). */
function encode(text: string): string {
  const bytes = new TextEncoder().encode(text)
  let binary = ''
  bytes.forEach((b) => { binary += String.fromCharCode(b) })
  return btoa(binary)
}

function decode(data: string): string {
  try {
    const binary = atob(data)
    return new TextDecoder().decode(Uint8Array.from(binary, (c) => c.charCodeAt(0)))
  } catch {
    return ''
  }
}

/** Dựng lại phần nhìn thấy được (iframe srcdoc) từ mã gốc đang lưu ở data-embed. */
function renderFrame(node: HTMLElement): void {
  const code = decode(node.getAttribute('data-embed') || '')
  const height = parseInt(node.getAttribute('data-embed-height') || '', 10)

  const frame = document.createElement('iframe')
  frame.className = 'hc-embed-frame'
  frame.setAttribute('sandbox', SANDBOX)
  frame.setAttribute('loading', 'lazy')
  frame.srcdoc = embedSrcDoc(code)
  if (Number.isFinite(height) && height > 0) {
    frame.style.height = `${height}px`
    frame.style.aspectRatio = 'auto'
  }

  node.textContent = ''
  node.appendChild(frame)
}

class HtmlEmbedBlot extends BlockEmbed {
  static blotName = 'htmlEmbed'
  static tagName = 'DIV'
  static className = 'hc-embed'

  static create(value: HtmlEmbedValue): HTMLElement {
    const node = super.create() as HTMLElement
    node.setAttribute('data-embed', encode(value.code || ''))
    if (value.height) node.setAttribute('data-embed-height', String(value.height))
    // Không cho gõ vào bên trong khối nhúng — chỉ chọn/xóa cả khối
    node.setAttribute('contenteditable', 'false')
    renderFrame(node)
    return node
  }

  static value(node: HTMLElement): HtmlEmbedValue {
    const height = parseInt(node.getAttribute('data-embed-height') || '', 10)
    return {
      code: decode(node.getAttribute('data-embed') || ''),
      height: Number.isFinite(height) && height > 0 ? height : null,
    }
  }
}

let registered = false

/** Đăng ký blot mã nhúng (gọi được nhiều lần). */
export function registerHtmlEmbed(): void {
  if (registered) return
  Quill.register(HtmlEmbedBlot as any, true)
  registered = true
}

export type ParsedEmbed =
  | { kind: 'iframe'; src: string }
  | { kind: 'html'; code: string }

/** Chỉ cho nhúng qua http(s) — chặn javascript:/data: lọt vào src iframe. */
function isSafeUrl(url: string): boolean {
  try {
    return /^https?:$/.test(new URL(url, window.location.href).protocol)
  } catch {
    return false
  }
}

/**
 * Phân loại mã người dùng dán:
 * - `iframe` — dán URL nhúng hoặc đúng 1 thẻ <iframe> không kèm gì khác (YouTube, Guideflow,
 *   Google Sheets/Drive...). Chèn thẳng bằng embed `video` sẵn có của Quill cho nhẹ.
 * - `html`   — đoạn code phức tạp (có <script>, nhiều thẻ) -> phải bọc iframe srcdoc.
 * Trả null nếu không nhận ra nội dung nhúng nào.
 */
export function parseEmbedCode(raw: string): ParsedEmbed | null {
  const code = raw.trim()
  if (!code) return null

  if (/^https?:\/\/\S+$/i.test(code)) {
    return isSafeUrl(code) ? { kind: 'iframe', src: code } : null
  }

  const doc = new DOMParser().parseFromString(code, 'text/html')
  const iframes = doc.body.querySelectorAll('iframe')
  const hasScript = doc.body.querySelector('script') !== null

  if (iframes.length === 1 && !hasScript && !doc.body.textContent?.trim()) {
    const src = iframes[0].getAttribute('src') || ''
    if (isSafeUrl(src)) return { kind: 'iframe', src }
  }

  if (!doc.body.firstElementChild) return null
  return { kind: 'html', code }
}
