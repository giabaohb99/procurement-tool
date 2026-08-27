import type { Editor } from '@tiptap/core'
import type { Node as ProseMirrorNode } from '@tiptap/pm/model'
import { NodeSelection } from '@tiptap/pm/state'

import {
  SIGNATURE_CLASS,
  SIGNATURE_MAX_WIDTH,
  SIGNATURE_MIN_WIDTH,
  clampNumber,
  clampOffset,
  normalizeRotation,
  signatureStyle,
  snapToRightAngle,
  type SignatureAttributes,
} from './signature-extension'

/**
 * Ba thao tác chuột trên một chữ ký đã đặt: KÉO · CO GIÃN · XOAY.
 *
 * ⚠️ Mọi phép tính đều phải chia cho HỆ SỐ PHÓNG. Trình soạn thảo phóng tờ giấy
 * bằng `zoom`, nên 10px con trỏ đi được trên màn hình ở mức 150% chỉ tương ứng
 * ~6,7px trên tờ giấy. Lấy thẳng `clientX` mà không quy đổi thì chữ ký chạy
 * nhanh hơn tay ở mức phóng lớn và chậm hơn tay ở mức nhỏ.
 *
 * Hệ số đọc bằng cách so bề rộng thật (`getBoundingClientRect`, đã tính `zoom`)
 * với bề rộng bố cục (`offsetWidth`, chưa tính) — không đọc CSS để khỏi phải
 * đoán đơn vị.
 */

type DragMode = 'move' | 'resize' | 'rotate'
/** Góc đang được kéo; góc đối diện đứng yên. */
type Corner = 'nw' | 'ne' | 'sw' | 'se'

//  Node view dựng bằng DOM thuần nên không gắn được component `lucide-react`.
//  Đây là ĐÚNG nét vẽ của `rotate-cw` và `trash-2` trong lucide, chép sang dạng
//  đường path — vẫn cùng một bộ biểu tượng với phần còn lại của giao diện.
const ICON_ROTATE = '<path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>'
//  Hai mũi tên chéo của lucide. Mỗi góc lấy đúng trục chéo của CHÍNH NÓ, nhìn là
//  biết kéo theo hướng nào.
//
//  ⚠️ Đọc kỹ toạ độ chứ đừng đoán theo tên: `move-diagonal` vẽ đường
//  (19,5)→(5,19), tức trục ↗↙ (NE–SW); còn `move-diagonal-2` vẽ (5,5)→(19,19),
//  tức trục ↖↘ (NW–SE). Trước đây gán ngược hai cái, thành ra góc trên-trái đeo
//  mũi tên của trục kia — bốn núm chỉ chéo nhau trông rất lạ.
const ICON_RESIZE_NWSE =
  '<path d="M19 13v6h-6"/><path d="M5 11V5h6"/><path d="m5 5 14 14"/>'
const ICON_RESIZE_NESW =
  '<path d="M11 19H5v-6"/><path d="M13 5h6v6"/><path d="M19 5 5 19"/>'

const ICON_DELETE =
  '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>' +
  '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6"/><path d="M14 11v6"/>'

/** Một biểu tượng SVG cùng bộ nét với `lucide-react`. */
function drawIcon(path: string): string {
  return (
    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ` +
    `stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${path}</svg>`
  )
}

/** Một nút nhỏ trong cụm trên, biểu tượng vẽ bằng SVG. */
function createToolButton(label: string, path: string): HTMLButtonElement {
  const el = document.createElement('button')
  el.type = 'button'
  el.className = 'doc-signature-tool'
  el.title = label
  el.setAttribute('aria-label', label)
  el.innerHTML = drawIcon(path)
  return el
}

/** Hệ số phóng đang áp lên tờ giấy. `1` khi không phóng. */
function readZoomScale(page: HTMLElement): number {
  const rect = page.getBoundingClientRect()
  if (!page.offsetWidth || !rect.width) return 1
  return rect.width / page.offsetWidth
}

export function createSignatureNodeView(editor: Editor) {
  return (props: { node: ProseMirrorNode; getPos: () => number | undefined }) => {
    const { node, getPos } = props

    //  Mốc neo nằm TRONG dòng chảy, cao 0px — cùng vai với `span.doc-signature-anchor`
    //  mà `renderHTML` ghi ra, nên chỗ đặt lúc soạn và lúc in trùng khít.
    const dom = document.createElement('span')
    dom.className = 'doc-signature-anchor'

    const frame = document.createElement('span')
    frame.className = 'doc-signature-holder'
    frame.setAttribute('data-signature', 'true')

    const img = document.createElement('img')
    img.className = SIGNATURE_CLASS
    img.alt = 'Chữ ký'
    img.draggable = false

    //  BỐN GÓC đều co giãn được, đúng thói quen của Word/Google Docs: kéo góc
    //  nào thì góc ĐỐI DIỆN đứng yên. Chỉ một núm ở góc dưới phải như trước thì
    //  muốn nới sang trái phải kéo giãn rồi kéo dời lại, hai thao tác cho một ý.
    const CORNERS = ['nw', 'ne', 'sw', 'se'] as const
    const cornerHandles = new Map<HTMLElement, Corner>()
    for (const corner of CORNERS) {
      const el = document.createElement('span')
      el.className = `doc-signature-handle doc-signature-handle--${corner}`
      el.title = 'Kéo để phóng to / thu nhỏ'
      const diagonal = corner === 'nw' || corner === 'se' ? ICON_RESIZE_NWSE : ICON_RESIZE_NESW
      el.innerHTML = drawIcon(diagonal)
      cornerHandles.set(el, corner)
    }

    //  Xoay và xoá gom thành MỘT cụm ở giữa mép trên — hai việc "làm gì với cả
    //  chữ ký này", khác hẳn bốn núm góc là "chỉnh hình dạng". Tách cụm ra thì
    //  không ai nhầm núm xoay với núm co giãn nữa.
    const toolbar = document.createElement('span')
    toolbar.className = 'doc-signature-toolbar'
    //  Con trỏ không được rơi vào ProseMirror qua cụm này.
    //  Gắn sau khi `on` được khai; xem cuối hàm.

    const rotateButton = createToolButton('Xoay chữ ký', ICON_ROTATE)
    rotateButton.classList.add('doc-signature-tool--rotate')
    const deleteButton = createToolButton('Bỏ chữ ký', ICON_DELETE)
    toolbar.append(rotateButton, deleteButton)

    frame.append(img, toolbar, ...cornerHandles.keys())
    dom.append(frame)

    let attrs = { ...(node.attrs as unknown as SignatureAttributes) }

    //  ⚠️ PHẢI GỠ ĐƯỢC MỌI TRÌNH NGHE khi node bị bỏ.
    //
    //  Mỗi trình nghe ở đây là một bao đóng ôm lấy `editor`. Không gỡ thì rời
    //  trang xong cả trình soạn thảo vẫn nằm lại trong bộ nhớ cùng cây DOM đã
    //  tách — đo được: văn bản KHÔNG chữ ký thì thu hồi sạch, văn bản CÓ chữ ký
    //  thì `editor` và nút DOM vẫn sống sau khi ép dọn rác.
    const goBoTrinhNghe: Array<() => void> = []
    function on<K extends keyof HTMLElementEventMap>(
      el: HTMLElement,
      loai: K,
      fn: (e: HTMLElementEventMap[K]) => void,
    ) {
      el.addEventListener(loai, fn)
      goBoTrinhNghe.push(() => el.removeEventListener(loai, fn))
    }

    /** Dừng cú kéo đang dở (nếu có) — đặt lúc bắt đầu kéo, gọi lúc thả hoặc huỷ. */
    let dungCuKeo: (() => void) | null = null

    function render() {
      img.src = attrs.src
      //  Cùng một hàm dựng `style` với lúc ghi ra HTML — hai chỗ tính khác nhau
      //  là đặt xong thấy một kiểu, mở lại thấy một kiểu.
      frame.setAttribute('style', signatureStyle(attrs))
      img.setAttribute('style', 'width:100%;height:100%;display:block')
      //  XOAY NGƯỢC LẠI đúng bằng góc của chữ ký: cụm nút nằm trong khung nên
      //  mặc định nó quay theo, ký nghiêng 180° là hai biểu tượng lộn ngược và
      //  nút xoay rơi xuống dưới đáy. Bù lại thì cụm luôn nằm ngang, đọc được.
      toolbar.style.transform = `translateX(-50%) rotate(${-attrs.rotate}deg)`
    }

    /**
     * Đo chỗ mốc neo đứng trong tờ giấy rồi ép chữ ký nằm gọn bên trong.
     *
     * Đo lại mỗi lần ghi chứ không đo một lần lúc bắt đầu kéo: gõ thêm chữ hay
     * đổi lề là mốc neo trôi đi, số đo cũ thành sai.
     */
    function clampInsidePage() {
      const page = dom.closest<HTMLElement>('.doc-page')
      if (!page) return
      const scale = readZoomScale(page)
      const pageRect = page.getBoundingClientRect()
      const anchorRect = dom.getBoundingClientRect()
      const anchorX = (anchorRect.left - pageRect.left) / scale
      const anchorY = (anchorRect.top - pageRect.top) / scale
      //  Chiều cao chưa chốt (ảnh đang tải) thì lấy tạm bề rộng — thà chặn hơi
      //  chặt một nhịp còn hơn cho lọt ra ngoài rồi mới kéo lại.
      const height = attrs.height > 0 ? attrs.height : attrs.width
      attrs = {
        ...attrs,
        left: Math.round(clampOffset(attrs.left, anchorX, attrs.width, pageRect.width / scale)),
        top: Math.round(clampOffset(attrs.top, anchorY, height, pageRect.height / scale)),
      }
    }

    function applyAttrs(next: Partial<SignatureAttributes>) {
      attrs = { ...attrs, ...next }
      clampInsidePage()
      render()
      const pos = getPos()
      if (typeof pos !== 'number') return
      editor.view.dispatch(editor.view.state.tr.setNodeMarkup(pos, undefined, { ...attrs }))
    }

    function startGesture(mode: DragMode, event: PointerEvent, corner: Corner = 'se') {
      event.preventDefault()
      event.stopPropagation()
      const page = frame.closest<HTMLElement>('.doc-page')
      if (!page) return
      const scale = readZoomScale(page)
      const start = { x: event.clientX, y: event.clientY, ...attrs }

      //  Tâm chữ ký trên màn hình — mốc để tính góc khi xoay.
      const o = frame.getBoundingClientRect()
      const center = { x: o.left + o.width / 2, y: o.top + o.height / 2 }
      const startAngle = Math.atan2(event.clientY - center.y, event.clientX - center.x)

      const onMove = (e: PointerEvent) => {
        const dx = (e.clientX - start.x) / scale
        const dy = (e.clientY - start.y) / scale

        if (mode === 'move') {
          applyAttrs({ left: Math.round(start.left + dx), top: Math.round(start.top + dy) })
          return
        }
        if (mode === 'resize') {
          //  Giữ nguyên tỷ lệ: chữ ký méo thì nhìn ra ngay là ảnh bị kéo.
          const ratio = start.height > 0 ? start.height / start.width : 0
          //  Kéo góc TRÁI thì đi sang phải là THU NHỎ, nên đảo dấu.
          const direction = corner === 'nw' || corner === 'sw' ? -1 : 1
          const nextWidth = clampNumber(
            start.width + direction * dx, SIGNATURE_MIN_WIDTH, SIGNATURE_MAX_WIDTH, start.width)
          const nextHeight = ratio ? Math.round(nextWidth * ratio) : start.height
          //  GIỮ GÓC ĐỐI DIỆN ĐỨNG YÊN: kéo góc trái thì mép phải phải nằm im,
          //  nên `left` bù đúng phần bề rộng vừa đổi. Không bù thì chữ ký vừa
          //  giãn vừa trượt, kéo một cái là lệch khỏi dòng tên người ký.
          const shiftLeft = corner === 'nw' || corner === 'sw' ? start.width - nextWidth : 0
          const shiftTop = corner === 'nw' || corner === 'ne' ? start.height - nextHeight : 0
          applyAttrs({
            width: Math.round(nextWidth),
            height: ratio ? nextHeight : 0,
            left: Math.round(start.left + shiftLeft),
            top: Math.round(start.top + shiftTop),
          })
          return
        }
        const angle = Math.atan2(e.clientY - center.y, e.clientX - center.x)
        const turned = normalizeRotation(start.rotate + ((angle - startAngle) * 180) / Math.PI)
        const snapped = snapToRightAngle(turned)
        //  Đánh dấu lúc đang bị hút để tô đậm viền — không có phản hồi nào thì
        //  người dùng tưởng chuột đơ chứ không biết là đã ăn vào góc vuông.
        frame.classList.toggle('is-snapped', snapped !== turned)
        applyAttrs({ rotate: snapped })
      }

      const onEnd = () => {
        window.removeEventListener('pointermove', onMove)
        window.removeEventListener('pointerup', onEnd)
        frame.classList.remove('is-dragging')
        frame.classList.remove('is-snapped')
        dungCuKeo = null
      }
      dungCuKeo = onEnd
      frame.classList.add('is-dragging')
      window.addEventListener('pointermove', onMove)
      window.addEventListener('pointerup', onEnd)
    }

    /** Chọn chính node này — có chọn thì bộ núm mới hiện ra. */
    function selectSelf() {
      const pos = getPos()
      if (typeof pos !== 'number') return
      const { state } = editor.view
      //  Bấm vào chữ ký PHẢI tự chọn nó. Trước đây bộ núm hiện theo rê chuột,
      //  nên lướt qua là hiện, mà lướt qua thì chưa chắc đã định làm gì.
      //  `preventDefault` ở nhánh kéo chặn mất đường chọn sẵn có của
      //  ProseMirror, nên phải tự đặt vùng chọn ở đây.
      editor.view.dispatch(state.tr.setSelection(NodeSelection.create(state.doc, pos)))
    }

    //  Con trỏ không được rơi vào ProseMirror qua cụm nút.
    on(toolbar, 'mousedown', (e) => e.preventDefault())

    on(frame, 'pointerdown', (e) => {
      if (!editor.isEditable) return
      if (e.target !== img && e.target !== frame) return
      selectSelf()
      startGesture('move', e)
    })
    for (const [el, corner] of cornerHandles) {
      on(el, 'pointerdown', (e) => {
        if (!editor.isEditable) return
        selectSelf()
        startGesture('resize', e, corner)
      })
    }
    on(rotateButton, 'pointerdown', (e) => {
      if (!editor.isEditable) return
      selectSelf()
      startGesture('rotate', e)
    })
    on(deleteButton, 'click', (e) => {
      e.preventDefault()
      const pos = getPos()
      if (typeof pos !== 'number') return
      editor.view.dispatch(editor.view.state.tr.delete(pos, pos + 1))
    })

    render()
    //  Ảnh chưa biết chiều cao thật cho tới khi tải xong; chốt tỷ lệ ngay lúc đó
    //  để lần co giãn đầu tiên không làm méo.
    on(img, 'load', () => {
      if (attrs.height > 0 || !img.naturalWidth) return
      applyAttrs({ height: Math.round((attrs.width * img.naturalHeight) / img.naturalWidth) })
    })

    return {
      dom,
      //  Không cho ProseMirror vẽ lại phần trong: DOM của node do chính đây dựng.
      ignoreMutation: () => true,
      update: (next: ProseMirrorNode) => {
        if (next.type.name !== 'documentSignature') return false
        attrs = { ...(next.attrs as unknown as SignatureAttributes) }
        render()
        return true
      },
      selectNode: () => frame.classList.add('is-selected'),
      deselectNode: () => frame.classList.remove('is-selected'),
      destroy: () => {
        //  Bị bỏ ngay giữa lúc đang kéo thì hai trình nghe trên `window` còn treo,
        //  và chúng ôm cả `editor`.
        dungCuKeo?.()
        for (const goBo of goBoTrinhNghe) goBo()
        goBoTrinhNghe.length = 0
        //  Bỏ luôn ảnh: `src` dạng data-uri có thể nặng vài trăm KB.
        img.removeAttribute('src')
        frame.replaceChildren()
        dom.replaceChildren()
      },
    }
  }
}
