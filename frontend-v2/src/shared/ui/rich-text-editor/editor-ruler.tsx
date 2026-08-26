import { useRef } from 'react'

import { cn } from '@/shared/utils/cn'
import { cmMarks, PX_PER_CM, RULER_SNAP_PX } from './ruler-metrics'
import { usePageOffset } from './use-page-offset'

/** Chừa lại ít nhất ngần này cho vùng gõ chữ, không cho hai lề bóp chết nhau. */
const MIN_TEXT_WIDTH = 200

export interface PageMargins {
  left: number
  right: number
}

interface EditorRulerProps {
  pageWidth: number
  /** Lề mặc định (px) hai bên — bấm đúp vào con trượt là về lại mốc này. */
  defaultMargins: PageMargins
  margins: PageMargins
  /** Gọi liên tục trong lúc kéo — chỉ để VẼ lại trang giấy theo tay. */
  onChange: (margins: PageMargins) => void
  /**
   * Gọi MỘT LẦN khi người dùng buông tay (thả chuột, nhấn phím, bấm đúp về
   * mặc định) — đây mới là lúc trang cha ghi xuống bản ghi.
   *
   * Tách khỏi `onChange` vì trước đây trang cha phải tự hẹn giờ 600ms để gom
   * nhịp kéo, mà hẹn giờ thì sinh ra khe hở: kéo xong bấm ngay «In / Xuất PDF»
   * là bản in đọc lề CŨ, còn chuyển tab trong khoảng đó là mất luôn thay đổi.
   */
  onCommit?: (margins: PageMargins) => void
  /** Mức phóng của trang, để quy khoảng chuột kéo về px thật của trang giấy. */
  zoom: number
  /** Thẻ trang giấy — thước bám theo đúng vị trí của nó. */
  page: HTMLElement | null
}

/**
 * THƯỚC KẺ NGANG, kiểu Google Docs.
 *
 * Hai con trượt hai đầu kéo được để đổi LỀ TRÁI / LỀ PHẢI của trang: văn bản
 * hành chính mỗi nơi quy định một kiểu lề, mà đây là thứ duy nhất trong thể
 * thức không gõ được từ bàn phím.
 *
 * Kéo hết bề ngang khung soạn thảo (qua cả cột mục lục) và dính liền dưới thanh
 * công cụ: thước là một phần của thanh lệnh chứ không phải của tờ giấy, cuộn
 * xuống trang thứ ba vẫn phải với tới được.
 *
 * Chỉ làm lề ngang: lề trên/dưới là số liệu để chia trang (xem `PaginationPlus`
 * trong `rich-text-editor.tsx`), đổi bừa là số trang tính ra sai.
 */
export function EditorRuler({
  pageWidth,
  defaultMargins,
  margins,
  onChange,
  onCommit,
  zoom,
  page,
}: EditorRulerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  // Giữ mốc lúc bắt đầu kéo trong ref: đọc `margins` trong hàm nghe chuột sẽ
  // dính giá trị cũ của lần render đã đóng băng.
  const dragRef = useRef<{ side: keyof PageMargins; startX: number; startValue: number }>(null)
  //  Giá trị mới nhất trong lúc kéo — lúc thả tay, `margins` trong closure vẫn
  //  là giá trị của lần render bắt đầu kéo, ghi theo nó là ghi hụt cả cú kéo.
  const latestRef = useRef<PageMargins>(margins)
  // Chỉ theo trục NGANG: thước này chỉ cần biết mép trái tờ giấy nằm ở đâu,
  // báo cả vị trí dọc thì cuộn xuống là nó vẽ lại theo từng khung hình cho
  // không.
  const offset = usePageOffset(page, containerRef, zoom, 'x')

  function clamp(side: keyof PageMargins, value: number) {
    const other = side === 'left' ? margins.right : margins.left
    return Math.min(Math.max(value, 0), pageWidth - other - MIN_TEXT_WIDTH)
  }

  function startDrag(side: keyof PageMargins, event: React.PointerEvent) {
    event.preventDefault()
    dragRef.current = { side, startX: event.clientX, startValue: margins[side] }

    const move = (moveEvent: PointerEvent) => {
      const drag = dragRef.current
      if (!drag) return
      // Lề phải lớn lên khi kéo sang TRÁI, nên đảo dấu. Chia cho `zoom` vì
      // chuột đi trên màn hình đã phóng, còn lề tính theo px thật của trang.
      const direction = drag.side === 'left' ? 1 : -1
      const delta = ((moveEvent.clientX - drag.startX) / zoom) * direction
      const next = Math.round((drag.startValue + delta) / RULER_SNAP_PX) * RULER_SNAP_PX
      const ke = { ...margins, [drag.side]: clamp(drag.side, next) }
      latestRef.current = ke
      onChange(ke)
    }

    const stop = () => {
      if (dragRef.current) onCommit?.(latestRef.current)
      dragRef.current = null
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', stop)
    }

    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', stop)
  }

  function nudge(side: keyof PageMargins, steps: number) {
    const ke = { ...margins, [side]: clamp(side, margins[side] + steps * RULER_SNAP_PX) }
    onChange(ke)
    onCommit?.(ke)
  }

  /** Bấm đúp con trượt: về lề mặc định — cũng là một lần buông tay. */
  function reset(side: keyof PageMargins, value: number) {
    const ke = { ...margins, [side]: value }
    onChange(ke)
    onCommit?.(ke)
  }

  const leftCm = margins.left / PX_PER_CM
  // Mọi số đo bên dưới là px THẬT của trang giấy, phải nhân `zoom` mới ra px
  // trên màn hình — thước không nằm trong khung đã phóng như trang giấy.
  const at = (value: number) => value * zoom

  return (
    <div
      ref={containerRef}
      className="relative h-7 overflow-hidden border-b bg-muted/40 select-none"
    >
      {/* Dải thước nằm đúng chỗ tờ giấy (đo bằng `usePageOffset`), phần thừa hai
          bên để trống nền xám như Google Docs. */}
      <div
        className="absolute top-1 h-5"
        style={{ left: offset.left, width: at(pageWidth) }}
      >
        {/* Không viền quanh dải thước: đặt cạnh viền thanh công cụ và mép tờ
            giấy, thêm một khung nữa là ba đường kẻ song song chồng nhau. */}
        <div className="absolute inset-0 rounded-sm bg-card" />

        {/* Hai đầu tô xám = phần lề: nhìn ra ngay chữ được phép chạy tới đâu. */}
        <div
          className="absolute inset-y-0 left-0 rounded-l-sm bg-muted"
          style={{ width: at(margins.left) }}
        />
        <div
          className="absolute inset-y-0 right-0 rounded-r-sm bg-muted"
          style={{ width: at(margins.right) }}
        />

        {cmMarks(pageWidth).map((cm) => (
          <span
            key={cm}
            aria-hidden
            className="absolute top-1/2 text-[9px] leading-none text-muted-foreground"
            style={{ left: at(cm * PX_PER_CM), transform: 'translate(-50%, -50%)' }}
          >
            {/* Số đếm từ MÉP LỀ TRÁI ra hai phía (giống Google Docs), nên chỗ
                bắt đầu gõ chữ luôn là vạch 0 — khỏi trừ nhẩm. */}
            {Math.abs(Math.round(cm - leftCm)) || ''}
          </span>
        ))}

        {cmMarks(pageWidth)
          .slice(0, -1)
          .map((cm) => (
            <span
              key={`half-${cm}`}
              aria-hidden
              className="absolute top-1/2 h-1 w-px -translate-y-1/2 bg-border"
              style={{ left: at((cm + 0.5) * PX_PER_CM) }}
            />
          ))}

        <MarginHandle
          side="left"
          offset={at(margins.left)}
          valueCm={margins.left / PX_PER_CM}
          onPointerDown={(event) => startDrag('left', event)}
          onReset={() => reset('left', defaultMargins.left)}
          onNudge={(steps) => nudge('left', steps)}
        />
        <MarginHandle
          side="right"
          offset={at(margins.right)}
          valueCm={margins.right / PX_PER_CM}
          onPointerDown={(event) => startDrag('right', event)}
          onReset={() => reset('right', defaultMargins.right)}
          onNudge={(steps) => nudge('right', steps)}
        />
      </div>
    </div>
  )
}

interface MarginHandleProps {
  side: keyof PageMargins
  /** Khoảng cách tới mép trang, tính bằng px MÀN HÌNH (đã nhân zoom). */
  offset: number
  valueCm: number
  onPointerDown: (event: React.PointerEvent) => void
  onReset: () => void
  onNudge: (steps: number) => void
}

/** Con trượt hình tam giác ở mép lề — kéo, bấm đúp để về mặc định, hoặc ←/→. */
function MarginHandle({
  side,
  offset,
  valueCm,
  onPointerDown,
  onReset,
  onNudge,
}: MarginHandleProps) {
  const label = side === 'left' ? 'Lề trái' : 'Lề phải'

  return (
    <button
      type="button"
      title={`${label} ${valueCm.toFixed(2)} cm — kéo để chỉnh, bấm đúp để về mặc định`}
      aria-label={`${label} ${valueCm.toFixed(2)} cm`}
      onPointerDown={onPointerDown}
      onDoubleClick={onReset}
      onKeyDown={(event) => {
        if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return
        event.preventDefault()
        // Phím mũi tên luôn hiểu theo hướng NHÌN THẤY trên thước: sang phải là
        // con trượt chạy sang phải, dù lề phải đo ngược từ mép trang vào.
        const toRight = event.key === 'ArrowRight'
        onNudge(side === 'left' ? (toRight ? 1 : -1) : toRight ? -1 : 1)
      }}
      className={cn(
        'absolute -bottom-1 flex h-3 w-4 cursor-col-resize items-end justify-center',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring',
        side === 'left' ? '-translate-x-1/2' : 'translate-x-1/2',
      )}
      style={side === 'left' ? { left: offset } : { right: offset }}
    >
      {/* Tam giác trỏ xuống, dựng bằng viền — nhẹ hơn kéo cả một icon vào. */}
      <span
        aria-hidden
        className="size-0 border-x-[5px] border-t-[7px] border-x-transparent border-t-primary"
      />
    </button>
  )
}
