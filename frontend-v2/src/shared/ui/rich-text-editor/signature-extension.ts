import { Node, mergeAttributes } from '@tiptap/core'

import { createSignatureNodeView } from './signature-node-view'

/**
 * CHỮ KÝ ĐẶT TỰ DO TRÊN TỜ GIẤY — như đóng một con dấu.
 *
 * Khác hẳn ảnh thường: ảnh nằm TRONG dòng chảy văn bản và đẩy nội dung xuống,
 * còn chữ ký phải **đè lên chữ** — văn bản hành chính ký đè lên dòng họ tên
 * người ký, không ai chèn một khoảng trắng rồi mới ký vào đó.
 *
 * Vì thế node này vẽ bằng `position: absolute`. Điều đáng nói là nó neo vào
 * **ĐÂU**: một mốc `span.doc-signature-anchor` cao 0px nằm ngay trong dòng chảy,
 * đúng chỗ người dùng chèn — giống hệt cách Word neo ảnh nổi vào một đoạn văn.
 * `left`/`top` là ĐỘ LỆCH so với mốc đó.
 *
 * ⚠️ Cách hiển nhiên hơn — neo thẳng vào tờ giấy `.doc-page` — ĐÃ THỬ VÀ HỎNG.
 * Trình soạn thảo là MỘT tờ giấy dài liền mạch (cao ~15.000px, các trang chỉ là
 * vạch kẻ), còn bản in cắt ra thành 14 thẻ `.doc-page` rời, mỗi thẻ là hộp nội
 * dung 605px đã trừ lề. Cùng một con số `top: 8000px` nghĩa là "trang 8" lúc
 * soạn nhưng là "quá đáy trang" lúc in, và `left` thì lệch thêm nguyên phần lề
 * trái. Mốc neo trôi theo dòng chảy nên hai bên tự khớp, không cần biết bài
 * chia làm mấy trang.
 *
 * Mốc cao 0px nên vẫn không chiếm chỗ, không đụng bộ phân trang.
 *
 * ⚠️ Đây **KHÔNG phải chữ ký pháp lý.** Chữ ký có giá trị pháp lý là bản ghi
 * `tab_signature` ở backend (ghi ai ký phiên bản nào, kèm mã băm nội dung lúc
 * ký). Node này chỉ là hình ảnh đặt lên bản in. Đừng dùng sự có mặt của nó để
 * kết luận văn bản đã được ký.
 *
 * ⚠️ Node **không chiếm chỗ trong dòng chảy** nên không đụng tới bộ phân trang —
 * đây là điểm cộng có chủ ý, xem lỗi phân trang chạy loạn ở
 * `doc/tai-lieu-chuc-nang/15-van-thu-cac-ca-da-kiem.md` §7.3.
 */

/** Bề rộng mặc định lúc chèn (px trên tờ A4 794px). */
export const SIGNATURE_DEFAULT_WIDTH = 180
/** Giới hạn co giãn — nhỏ quá thì không nhìn ra, to quá thì che hết trang. */
export const SIGNATURE_MIN_WIDTH = 48
export const SIGNATURE_MAX_WIDTH = 600

export interface SignatureAttributes {
  src: string
  /** px, tính từ mép TRÁI tờ giấy. */
  left: number
  /** px, tính từ mép TRÊN tờ giấy. */
  top: number
  width: number
  height: number
  /** Độ, 0–359. */
  rotate: number
}

/** Ép một số về khoảng cho phép; giá trị lạ thì trả `fallback`. */
export function clampNumber(value: unknown, min: number, max: number, fallback: number): number {
  const n = typeof value === 'number' ? value : Number.parseFloat(String(value ?? ''))
  if (!Number.isFinite(n)) return fallback
  return Math.min(Math.max(n, min), max)
}

/** Đưa góc xoay về 0–359 (nhận cả số âm và số vượt vòng). */
export function normalizeRotation(value: unknown): number {
  const n = typeof value === 'number' ? value : Number.parseFloat(String(value ?? ''))
  if (!Number.isFinite(n)) return 0
  return ((Math.round(n) % 360) + 360) % 360
}

/** Đọc một số px từ chuỗi `style` (vd `left: 120px`). */
export function readPixels(style: string | null | undefined, name: string): number | null {
  if (!style) return null
  const found = new RegExp(`${name}\\s*:\\s*(-?[\\d.]+)px`, 'i').exec(style)
  if (!found) return null
  const n = Number.parseFloat(found[1])
  return Number.isFinite(n) ? n : null
}

/**
 * Độ lệch tối đa còn được hút về góc vuông.
 *
 * 7° là khoảng mà tay người khó giữ nổi: xoay bằng chuột thì sai số vài độ là
 * chuyện thường, mà chữ ký lệch 3° so với dòng chữ thì nhìn ra ngay. Để rộng
 * hơn (15°) thì mất luôn khả năng đặt chữ ký hơi nghiêng — nhiều người ký
 * nghiêng thật.
 */
export const ROTATE_SNAP_DEGREES = 7

/**
 * Hút góc xoay về bội số của 90° khi đã đủ gần — kéo tới gần góc vuông thì
 * **khựng lại** một nhịp rồi mới đi tiếp.
 *
 * Không hút thì gần như không ai chỉnh được đúng 0° hay 90°, cứ lệch 1–2° và
 * bản in nhìn xộc xệch mà không rõ vì sao.
 */
export function snapToRightAngle(degrees: number, tolerance = ROTATE_SNAP_DEGREES): number {
  const nearest = Math.round(degrees / 90) * 90
  return Math.abs(degrees - nearest) <= tolerance ? normalizeRotation(nearest) : degrees
}

/**
 * Ép một độ lệch để chữ ký KHÔNG lọt ra ngoài tờ giấy.
 *
 * `offset` tính từ mốc neo, còn `anchor` là chỗ mốc neo đứng trong tờ giấy, nên
 * mép chữ ký nằm ở `anchor + offset`. Cần giữ cả đoạn `[anchor+offset,
 * anchor+offset+size]` nằm trong `[0, pageSize]`.
 *
 * Không chặn thì kéo tay một cái là chữ ký trôi sang khung mục lục bên trái,
 * lúc in ra thì mất hẳn — trên màn hình vẫn thấy nên không ai ngờ.
 *
 * Chữ ký to hơn cả tờ giấy thì dí về mép trái/trên chứ không trả khoảng rỗng.
 */
export function clampOffset(
  offset: number,
  anchor: number,
  size: number,
  pageSize: number,
): number {
  const min = -anchor
  const max = pageSize - anchor - size
  if (max < min) return min
  return Math.min(Math.max(offset, min), max)
}

/** Đọc góc xoay từ `transform: rotate(12deg)`. */
export function readRotation(style: string | null | undefined): number {
  if (!style) return 0
  const found = /rotate\(\s*(-?[\d.]+)deg\s*\)/i.exec(style)
  return found ? normalizeRotation(found[1]) : 0
}

/** Dựng chuỗi `style` đặt chữ ký — dùng chung cho trình soạn thảo và bản in. */
export function signatureStyle(attrs: SignatureAttributes): string {
  const parts = [
    'position:absolute',
    `left:${Math.round(attrs.left)}px`,
    `top:${Math.round(attrs.top)}px`,
    `width:${Math.round(attrs.width)}px`,
  ]
  if (attrs.height > 0) parts.push(`height:${Math.round(attrs.height)}px`)
  if (attrs.rotate) parts.push(`transform:rotate(${attrs.rotate}deg)`)
  return parts.join(';')
}

export const SIGNATURE_CLASS = 'doc-signature'
/** Mốc neo cao 0px nằm TRONG dòng chảy; chữ ký đặt lệch so với nó. */
export const SIGNATURE_ANCHOR_CLASS = 'doc-signature-anchor'

export const DocumentSignature = Node.create({
  name: 'documentSignature',
  group: 'block',
  //  `atom`: không có nội dung con, con trỏ không chui vào trong được — người
  //  dùng thao tác với nó bằng chuột chứ không bằng bàn phím.
  atom: true,
  draggable: false,
  selectable: true,

  //  Đọc lại phải THẮNG node ảnh thường. Cả hai cùng nhận thẻ `img`; ProseMirror
  //  xét luật theo thứ tự ưu tiên chứ KHÔNG theo mức cụ thể của bộ chọn, nên để
  //  mặc định (50) thì luật `img[src]` của Image có thể bắt trước và chữ ký mở
  //  lại thành một tấm ảnh nằm giữa dòng chữ.
  priority: 200,

  addAttributes() {
    //  ⚠️ Vị trí, cỡ và góc xoay CHỈ ghi ra trong `style` (xem `renderHTML`).
    //  Để mặc định thì Tiptap tự đổ mỗi thuộc tính thành một attribute HTML và
    //  thẻ ra `<img left="370" top="420" rotate="135">` — attribute không hợp lệ,
    //  trình duyệt bỏ qua, mà bộ lọc XSS phía backend thì có quyền cắt bất cứ lúc
    //  nào. `renderHTML: () => null` tắt đường đổ tự động đó.
    const styleOnly = { renderHTML: () => null }
    return {
      src: { default: '' },
      left: { default: 0, ...styleOnly },
      top: { default: 0, ...styleOnly },
      width: { default: SIGNATURE_DEFAULT_WIDTH, ...styleOnly },
      height: { default: 0, ...styleOnly },
      rotate: { default: 0, ...styleOnly },
    }
  },

  parseHTML() {
    return [
      {
        //  Nhận diện bằng CLASS chứ không bằng thẻ: mọi `<img>` khác vẫn là ảnh
        //  thường. Thiếu chốt này thì mở lại một văn bản có ảnh minh hoạ là mọi
        //  ảnh biến thành chữ ký.
        tag: `span.${SIGNATURE_ANCHOR_CLASS}`,
        getAttrs: (element) => {
          if (!(element instanceof HTMLElement)) return false
          const img = element.querySelector(`img.${SIGNATURE_CLASS}`)
          if (!img) return false
          const style = img.getAttribute('style')
          return {
            src: img.getAttribute('src') || '',
            left: readPixels(style, 'left') ?? 0,
            top: readPixels(style, 'top') ?? 0,
            width: clampNumber(
              readPixels(style, 'width') ?? img.getAttribute('width'),
              SIGNATURE_MIN_WIDTH,
              SIGNATURE_MAX_WIDTH,
              SIGNATURE_DEFAULT_WIDTH,
            ),
            height: readPixels(style, 'height') ?? 0,
            rotate: readRotation(style),
          }
        },
      },
    ]
  },

  renderHTML({ HTMLAttributes, node }) {
    const attrs = node.attrs as unknown as SignatureAttributes
    return [
      'span',
      mergeAttributes(HTMLAttributes, { class: SIGNATURE_ANCHOR_CLASS }),
      [
        'img',
        {
          class: SIGNATURE_CLASS,
          src: attrs.src,
          alt: 'Chữ ký',
          //  Ghi cả `style` lẫn `width`: bộ lọc XSS ở backend cho qua cả hai, và
          //  `width` là đường lùi nếu về sau có nơi nào bỏ `style`.
          style: signatureStyle(attrs),
          width: Math.round(attrs.width),
          draggable: 'false',
        },
      ],
    ]
  },

  addNodeView() {
    //  Nạp muộn để tránh vòng import: node view cần chính hằng số của tệp này.
    return (props) => createSignatureNodeView(this.editor)(props as never)
  },
})
