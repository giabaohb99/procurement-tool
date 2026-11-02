import { Maximize, Minus, Plus } from 'lucide-react'
import {
  useCallback,
  useEffect,
  useImperativeHandle,
  useLayoutEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
  type Ref,
} from 'react'
import { flushSync } from 'react-dom'

import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { cn } from '@/shared/utils/cn'

//  Số đo chép theo `ChartCanvas.vue` của ERPNext (hrms/hr/page/organizational_chart).
const MAX_SCALE = 1.5
const ZOOM_STEP = 1.2
const GRID_SIZE = 20
//  Khoảng cách thẻ ↔ khung thông tin, và khoảng tối thiểu tới mép khung vẽ.
const POPOVER_GAP = 12
const EDGE_GAP = 16
//  Nút «N cấp dưới» thò xuống dưới thẻ chừng này.
const TEAM_PILL_DROP = 18
//  Nhấn rồi thả mà dịch ít hơn chừng này là BẤM, không phải kéo.
const CLICK_DISTANCE = 4

interface View {
  x: number
  y: number
  scale: number
}

export interface OrgChartCanvasHandle {
  /** Thu / phóng cho cả sơ đồ vừa khung (không phóng quá 100%). */
  fit: () => void
  /** Về đầu sơ đồ, 100%, căn giữa ngang, nằm dưới thanh tìm. */
  showTop: () => void
  /** Dời khung nhìn cho `element` vào giữa. */
  center: (element: HTMLElement) => void
  /** Chạy `change` (đổi state) rồi giữ `element` đứng yên trên màn hình — mở / thu nhóm không làm thẻ nhảy. */
  keepInPlace: (element: HTMLElement | null, change: () => void) => void
  /** Dời (và thu nhỏ nếu buộc phải) cho mọi phần tử lọt vào tầm nhìn; đã lọt thì đứng yên. */
  reveal: (elements: (HTMLElement | null)[]) => void
  findCard: (id: number) => HTMLElement | null
}

interface OrgChartCanvasProps {
  children: ReactNode
  /** Thanh trên-trái (ô tìm người, chọn pháp nhân / phòng). */
  panel?: ReactNode
  /** Nút thêm ở thanh công cụ dưới-trái, sau nhóm phóng to / thu nhỏ. */
  actions?: ReactNode
  /** Khung thông tin của thẻ đang chọn — đặt cạnh thẻ đó. */
  popover?: ReactNode
  selectedId: number | null
  onDeselect: () => void
  ref?: Ref<OrgChartCanvasHandle>
}

/**
 * Khung vẽ kéo-thả kiểu ERPNext: nền chấm, kéo chuột để dời, cuộn để dời, Ctrl/⌘ + cuộn (hoặc chụm
 * hai ngón) để phóng, phím `+` `-` `0`. Nội dung được dời bằng `transform` nên sơ đồ to cỡ nào
 * cũng không làm trang cuộn.
 */
export function OrgChartCanvas({
  children,
  panel,
  actions,
  popover,
  selectedId,
  onDeselect,
  ref,
}: OrgChartCanvasProps) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const toolbarRef = useRef<HTMLDivElement>(null)
  const popoverRef = useRef<HTMLDivElement>(null)
  const [view, setViewState] = useState<View>({ x: 0, y: 0, scale: 1 })
  //  Bản sao đồng bộ của `view` cho các hàm gọi liền nhau trong cùng một nhịp (zoom rồi dời).
  const viewRef = useRef(view)
  const [dragging, setDragging] = useState(false)

  const setView = useCallback((next: View) => {
    viewRef.current = next
    setViewState(next)
  }, [])

  const fitScale = useCallback(() => {
    const canvas = canvasRef.current
    const content = contentRef.current
    if (!canvas || !content) return 1
    const rect = canvas.getBoundingClientRect()
    return Math.min(1, rect.width / content.offsetWidth, rect.height / content.offsetHeight)
  }, [])

  //  Phóng quanh `point` (mặc định giữa khung) để điểm đó đứng yên dưới con trỏ.
  const zoomTo = useCallback(
    (scale: number, point?: { x: number; y: number }) => {
      const canvas = canvasRef.current
      if (!canvas) return
      const current = viewRef.current
      const next = Math.min(MAX_SCALE, Math.max(fitScale(), scale))
      const rect = canvas.getBoundingClientRect()
      const { x, y } = point ?? { x: rect.width / 2, y: rect.height / 2 }
      setView({
        x: x - ((x - current.x) * next) / current.scale,
        y: y - ((y - current.y) * next) / current.scale,
        scale: next,
      })
    },
    [fitScale, setView],
  )

  const fit = useCallback(() => {
    const canvas = canvasRef.current
    const content = contentRef.current
    if (!canvas || !content) return
    const rect = canvas.getBoundingClientRect()
    const scale = fitScale()
    setView({
      scale,
      x: (rect.width - content.offsetWidth * scale) / 2,
      y: (rect.height - content.offsetHeight * scale) / 2,
    })
  }, [fitScale, setView])

  const panelBottom = () => (panelRef.current ? panelRef.current.offsetTop + panelRef.current.offsetHeight : 0)

  const showTop = useCallback(() => {
    const canvas = canvasRef.current
    const content = contentRef.current
    if (!canvas || !content) return
    const rect = canvas.getBoundingClientRect()
    const padding = parseFloat(getComputedStyle(content).paddingTop) || 0
    setView({
      scale: 1,
      x: (rect.width - content.offsetWidth) / 2,
      y: Math.max(0, panelBottom() + EDGE_GAP - padding),
    })
  }, [setView])

  const center = useCallback(
    (element: HTMLElement) => {
      const canvas = canvasRef.current
      if (!canvas) return
      const rect = canvas.getBoundingClientRect()
      const box = element.getBoundingClientRect()
      const current = viewRef.current
      setView({
        ...current,
        x: current.x + rect.left + rect.width / 2 - (box.left + box.width / 2),
        y: current.y + rect.top + rect.height / 2 - (box.top + box.height / 2),
      })
    },
    [setView],
  )

  const keepInPlace = useCallback(
    (element: HTMLElement | null, change: () => void) => {
      const before = element?.getBoundingClientRect()
      //  Đổi DOM NGAY để đo lại được trong cùng nhịp bấm.
      flushSync(change)
      if (!element || !before || !element.isConnected) return
      const after = element.getBoundingClientRect()
      const current = viewRef.current
      //  Áp ngay để lệnh `reveal` gọi liền sau đo đúng vị trí mới.
      flushSync(() =>
        setView({ ...current, x: current.x + before.left - after.left, y: current.y + before.top - after.top }),
      )
    },
    [setView],
  )

  const reveal = useCallback(
    (elements: (HTMLElement | null)[]) => {
      const canvas = canvasRef.current
      const boxes = elements.filter((el): el is HTMLElement => Boolean(el)).map((el) => el.getBoundingClientRect())
      if (!canvas || boxes.length === 0) return
      const rect = canvas.getBoundingClientRect()
      const area = {
        left: EDGE_GAP,
        right: rect.width - EDGE_GAP,
        top: panelBottom() + EDGE_GAP,
        bottom: (toolbarRef.current ? toolbarRef.current.offsetTop : rect.height) - EDGE_GAP,
      }
      const left = Math.min(...boxes.map((box) => box.left)) - rect.left
      const top = Math.min(...boxes.map((box) => box.top)) - rect.top
      let right = Math.max(...boxes.map((box) => box.right)) - rect.left
      //  Hàng thẻ cuối còn nút «N cấp dưới» thò xuống.
      let bottom = Math.max(...boxes.map((box) => box.bottom)) - rect.top + TEAM_PILL_DROP
      if (left >= area.left && right <= area.right && top >= area.top && bottom <= area.bottom) return

      const room = Math.min((area.right - area.left) / (right - left), (area.bottom - area.top) / (bottom - top))
      if (room < 1) {
        const before = viewRef.current.scale
        zoomTo(before * room, { x: left, y: top })
        right = left + ((right - left) * viewRef.current.scale) / before
        bottom = top + ((bottom - top) * viewRef.current.scale) / before
      }
      const current = viewRef.current
      let dy = 0
      if (top < area.top) dy = area.top - top
      else if (bottom > area.bottom) dy = Math.max(area.bottom - bottom, area.top - top)
      setView({
        ...current,
        x: current.x + Math.max(area.left - left, (area.left + area.right - left - right) / 2),
        y: current.y + dy,
      })
    },
    [setView, zoomTo],
  )

  const findCard = useCallback(
    (id: number) => contentRef.current?.querySelector<HTMLElement>(`[data-node="${id}"]`) ?? null,
    [],
  )

  useImperativeHandle(ref, () => ({ fit, showTop, center, keepInPlace, reveal, findCard }), [
    fit,
    showTop,
    center,
    keepInPlace,
    reveal,
    findCard,
  ])

  //  Khung thông tin: bên phải thẻ nếu vừa, không thì bên trái, không nữa (điện thoại) thì bên dưới.
  //  Ghi thẳng vào style của phần tử (không qua state) để không vẽ lại cả sơ đồ mỗi lần dời.
  const placePopover = useCallback(() => {
    const canvas = canvasRef.current
    const box = popoverRef.current
    if (selectedId === null || !canvas || !box) return
    const card = findCard(selectedId)
    if (!card) {
      onDeselect()
      return
    }
    const rect = canvas.getBoundingClientRect()
    const cardBox = card.getBoundingClientRect()
    const { offsetWidth: width, offsetHeight: height } = box
    const rightSide = cardBox.right - rect.left + POPOVER_GAP
    const leftSide = cardBox.left - rect.left - POPOVER_GAP - width
    let left = rightSide
    let top = cardBox.top - rect.top
    if (rightSide + width > rect.width - EDGE_GAP) {
      if (leftSide >= EDGE_GAP) left = leftSide
      else {
        left = cardBox.left - rect.left
        top = cardBox.bottom - rect.top + TEAM_PILL_DROP + POPOVER_GAP
      }
    }
    left = Math.max(EDGE_GAP, Math.min(left, rect.width - width - EDGE_GAP))
    top = Math.max(EDGE_GAP, Math.min(top, rect.height - height - EDGE_GAP))
    box.style.left = `${left}px`
    box.style.top = `${top}px`
    box.style.visibility = 'visible'
  }, [findCard, onDeselect, selectedId])

  useLayoutEffect(placePopover, [placePopover, view])

  //  Mở / thu một nhóm ở chỗ khác làm thẻ đang chọn dịch đi.
  useEffect(() => {
    const content = contentRef.current
    if (!content) return
    const observer = new ResizeObserver(() => placePopover())
    observer.observe(content)
    return () => observer.disconnect()
  }, [placePopover])

  //  `wheel` phải gắn tay với `passive: false` thì mới chặn được trang cuộn theo.
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const onWheel = (event: WheelEvent) => {
      if ((event.target as HTMLElement).closest('[data-panel]')) return
      event.preventDefault()
      //  Chụm hai ngón trên bàn di chuột tới dưới dạng `wheel` kèm `ctrlKey`.
      if (event.ctrlKey || event.metaKey) {
        const rect = canvas.getBoundingClientRect()
        zoomTo(viewRef.current.scale * Math.exp(-event.deltaY / 100), {
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
        })
        return
      }
      const current = viewRef.current
      setView({ ...current, x: current.x - event.deltaX, y: current.y - event.deltaY })
    }
    canvas.addEventListener('wheel', onWheel, { passive: false })
    return () => canvas.removeEventListener('wheel', onWheel)
  }, [setView, zoomTo])

  const drag = useRef<{ x: number; y: number; fromX: number; fromY: number } | null>(null)
  const pointers = useRef(new Map<number, { x: number; y: number }>())
  const pinch = useRef<{ gap: number; scale: number } | null>(null)
  const fingerGap = ([a, b]: { x: number; y: number }[]) => Math.hypot(a.x - b.x, a.y - b.y)

  const startDrag = (event: ReactPointerEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement
    if (event.button !== 0 || target.closest('button, a, input, [data-panel]')) return
    pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY })
    event.currentTarget.setPointerCapture(event.pointerId)
    if (pointers.current.size === 2) {
      pinch.current = { gap: fingerGap([...pointers.current.values()]), scale: viewRef.current.scale }
      drag.current = null
      return
    }
    drag.current = {
      x: event.clientX - viewRef.current.x,
      y: event.clientY - viewRef.current.y,
      fromX: event.clientX,
      fromY: event.clientY,
    }
    setDragging(true)
  }

  const moveDrag = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!pointers.current.has(event.pointerId)) return
    pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY })
    const canvas = canvasRef.current
    if (pinch.current && pointers.current.size === 2 && canvas) {
      const fingers = [...pointers.current.values()]
      const rect = canvas.getBoundingClientRect()
      zoomTo((pinch.current.scale * fingerGap(fingers)) / pinch.current.gap, {
        x: (fingers[0].x + fingers[1].x) / 2 - rect.left,
        y: (fingers[0].y + fingers[1].y) / 2 - rect.top,
      })
      return
    }
    if (!drag.current) return
    setView({ ...viewRef.current, x: event.clientX - drag.current.x, y: event.clientY - drag.current.y })
  }

  const stopDrag = (event: ReactPointerEvent<HTMLDivElement>) => {
    pointers.current.delete(event.pointerId)
    //  Bấm vào nền (giữa các thẻ) là đóng khung thông tin.
    if (
      drag.current &&
      !pinch.current &&
      Math.hypot(event.clientX - drag.current.fromX, event.clientY - drag.current.fromY) < CLICK_DISTANCE
    ) {
      onDeselect()
    }
    if (pointers.current.size === 0) pinch.current = null
    drag.current = null
    setDragging(false)
  }

  const onKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Escape') return onDeselect()
    if ((event.target as HTMLElement).closest('input')) return
    if (event.key === '+' || event.key === '=') zoomTo(viewRef.current.scale * ZOOM_STEP)
    else if (event.key === '-') zoomTo(viewRef.current.scale / ZOOM_STEP)
    else if (event.key === '0') fit()
    else return
    event.preventDefault()
  }

  //  Thu nhỏ sâu (sơ đồ lớn «Mở hết» ~10%) thì ô lưới 2px làm chấm dồn thành mảng xám: giãn gấp đôi
  //  cho tới khi ô còn ≥ 10px.
  let gridSize = GRID_SIZE * view.scale
  while (gridSize < 10) gridSize *= 2

  return (
    <div
      ref={canvasRef}
      tabIndex={0}
      role="application"
      aria-label="Sơ đồ tổ chức. Kéo để dời, phím cộng / trừ để phóng, 0 để vừa khung."
      className={cn(
        'relative h-full w-full touch-none overflow-hidden bg-card outline-none select-none',
        dragging ? 'cursor-grabbing' : 'cursor-grab',
      )}
      style={{
        backgroundImage:
          'radial-gradient(circle, color-mix(in oklab, var(--muted-foreground) 30%, transparent) 1px, transparent 1.2px)',
        backgroundSize: `${gridSize}px ${gridSize}px`,
        backgroundPosition: `${view.x}px ${view.y}px`,
      }}
      onPointerDown={startDrag}
      onPointerMove={moveDrag}
      onPointerUp={stopDrag}
      onPointerCancel={stopDrag}
      onKeyDown={onKeyDown}
    >
      <div
        ref={contentRef}
        className="absolute top-0 left-0 inline-flex flex-col items-center p-10"
        style={{ transform: `translate(${view.x}px, ${view.y}px) scale(${view.scale})`, transformOrigin: '0 0' }}
      >
        {children}
      </div>

      {selectedId !== null && popover && (
        <div
          key={selectedId}
          ref={popoverRef}
          data-panel
          className="absolute z-10 cursor-auto"
          //  Ẩn tới khi đo xong và đặt chỗ, khỏi nháy ở góc trái trên.
          style={{ visibility: 'hidden' }}
        >
          {popover}
        </div>
      )}

      {panel && (
        <div ref={panelRef} data-panel className="absolute top-4 right-4 left-4 z-20 cursor-auto sm:right-auto">
          {panel}
        </div>
      )}

      <div
        ref={toolbarRef}
        data-panel
        className="absolute bottom-4 left-4 z-20 flex cursor-auto items-center gap-0.5 rounded-lg border bg-card p-1 shadow-sm"
      >
        <IconTooltip label="Thu nhỏ">
          <Button type="button" variant="ghost" size="icon-sm" aria-label="Thu nhỏ" onClick={() => zoomTo(view.scale / ZOOM_STEP)}>
            <Minus />
          </Button>
        </IconTooltip>
        <IconTooltip label="Về 100%">
          <Button type="button" variant="ghost" size="sm" className="min-w-14 tabular-nums" onClick={() => zoomTo(1)}>
            {Math.round(view.scale * 100)}%
          </Button>
        </IconTooltip>
        <IconTooltip label="Phóng to">
          <Button type="button" variant="ghost" size="icon-sm" aria-label="Phóng to" onClick={() => zoomTo(view.scale * ZOOM_STEP)}>
            <Plus />
          </Button>
        </IconTooltip>
        <span aria-hidden className="mx-1 h-4 w-px bg-border" />
        <IconTooltip label="Vừa khung">
          <Button type="button" variant="ghost" size="icon-sm" aria-label="Vừa khung" onClick={fit}>
            <Maximize />
          </Button>
        </IconTooltip>
        {actions}
      </div>
    </div>
  )
}
