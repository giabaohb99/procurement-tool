import { useCallback, useEffect, useRef, useState } from 'react'

import { linkTypeFromSides, type LinkSide } from '../utils/gantt-links'

/**
 * Kéo tạo MŨI TÊN PHỤ THUỘC trên Gantt (B-15).
 *
 * Dùng `pointerdown/move/up` thô chứ không qua dnd-kit — cùng khung đang có một
 * `DndContext` lo việc kéo NGÀY, nhét thêm một loại kéo mang nghĩa khác hẳn vào
 * đó thì `onDragEnd` phải đoán xem cú thả vừa rồi là dời lịch hay nối việc, và
 * đoán nhầm là **ghi đè ngày của một việc thật**.
 *
 * KIỂU phụ thuộc suy ra từ hai đầu người dùng chạm vào, đúng lối DHTMLX:
 *
 * | Rời ở | Tới ở | Kiểu |
 * | ----- | ----- | ---- |
 * | cuối  | đầu   | FS   |
 * | đầu   | đầu   | SS   |
 * | cuối  | cuối  | FF   |
 * | đầu   | cuối  | SF   |
 *
 * Đích không cần trúng đúng cái chấm nhỏ: thả vào NỬA nào của thanh đích thì
 * tính là đầu ấy. Bắt trúng chấm 12px sau khi đã rê qua nửa màn hình là kiểu
 * thao tác chỉ chuột xịn mới làm nổi.
 */

export interface GanttLinkDraft {
  fromTaskId: number
  fromSide: LinkSide
  /** Vị trí con trỏ trong hệ tọa độ của vùng các hàng (px). */
  x: number
  y: number
  /** Việc đang bị nhắm làm đích, `null` = con trỏ đang ở chỗ trống. */
  targetTaskId: number | null
}

interface Options {
  /** Vùng CÁC HÀNG (không gồm tiêu đề) — mốc quy đổi tọa độ con trỏ. */
  areaRef: React.RefObject<HTMLDivElement | null>
  onCreate: (values: {
    predecessor_id: number
    successor_id: number
    link_type: number
  }) => void
}

export function useGanttLinkDraft({ areaRef, onCreate }: Options) {
  const [draft, setDraft] = useState<GanttLinkDraft | null>(null)
  //  Bản mới nhất của cú kéo, đọc được TỨC THÌ trong trình xử lý `pointerup`.
  //  Đọc `draft` từ state ở đó là đọc ảnh chụp của lần vẽ trước — thả ra là
  //  không có gì xảy ra, mà chỉ thỉnh thoảng, nên rất khó lần ra.
  const latest = useRef<GanttLinkDraft | null>(null)

  const start = useCallback(
    (taskId: number, side: LinkSide, event: React.PointerEvent) => {
      const rect = areaRef.current?.getBoundingClientRect()
      if (!rect) return
      const next: GanttLinkDraft = {
        fromTaskId: taskId,
        fromSide: side,
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
        targetTaskId: null,
      }
      latest.current = next
      setDraft(next)
    },
    [areaRef],
  )

  //  Chỉ hỏi CÓ ĐANG KÉO KHÔNG, không phụ thuộc vào chính `draft`: `draft` đổi
  //  ở mỗi nhịp chuột, nên phụ thuộc nó là cứ mỗi nhịp lại gỡ ra gắn lại bốn
  //  trình nghe của `window`.
  const dangKeo = draft !== null

  useEffect(() => {
    if (!dangKeo) return

    function move(event: PointerEvent) {
      const rect = areaRef.current?.getBoundingClientRect()
      const from = latest.current
      if (!rect || !from) return
      const hit = hitTest(event.clientX, event.clientY, from.fromTaskId)
      const next: GanttLinkDraft = {
        ...from,
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
        targetTaskId: hit?.taskId ?? null,
      }
      latest.current = next
      setDraft(next)
    }

    function finish(event: PointerEvent) {
      const from = latest.current
      latest.current = null
      setDraft(null)
      if (!from) return

      const hit = hitTest(event.clientX, event.clientY, from.fromTaskId)
      if (!hit) return
      onCreate({
        predecessor_id: from.fromTaskId,
        successor_id: hit.taskId,
        link_type: linkTypeFromSides(from.fromSide, hit.side),
      })
    }

    function cancel(event: KeyboardEvent) {
      if (event.key !== 'Escape') return
      latest.current = null
      setDraft(null)
    }

    //  Nghe ở `window`: con trỏ chạy ra ngoài khung biểu đồ giữa chừng là
    //  chuyện thường (kéo tới việc nằm dưới đáy màn hình), nghe ở khung thì mất
    //  luôn cú `pointerup` và cú kéo treo lại mãi.
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', finish)
    window.addEventListener('pointercancel', finish)
    window.addEventListener('keydown', cancel)
    return () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', finish)
      window.removeEventListener('pointercancel', finish)
      window.removeEventListener('keydown', cancel)
    }
  }, [dangKeo, areaRef, onCreate])

  return { draft, start }
}

/**
 * Thanh nằm dưới con trỏ, và con trỏ đang ở NỬA nào của nó.
 *
 * Dò theo `data-task-id` chứ KHÔNG theo `data-gantt-bar`: hai mép kéo đổi ngày
 * là ANH EM của thanh và nằm ĐÈ lên nó, mà thanh của một việc chỉ có hạn thì
 * rộng đúng một ngày — 16px ở mức Tuần, tức hai cái mép 7px phủ gần kín. Dò
 * theo thanh thì thả vào giữa những việc như thế (phần lớn dữ liệu thật!) luôn
 * trượt, và trượt IM LẶNG: người dùng thấy mình thả trúng nhưng không có mũi
 * tên nào hiện ra.
 */
function hitTest(
  clientX: number,
  clientY: number,
  fromTaskId: number,
): { taskId: number; side: LinkSide } | null {
  const el = document.elementFromPoint(clientX, clientY)
  const hit = el?.closest<HTMLElement>('[data-task-id]')
  if (!hit) return null

  const taskId = Number(hit.dataset.taskId)
  //  Nối một việc vào chính nó là vòng lặp ngắn nhất có thể; máy chủ cũng chặn,
  //  nhưng chặn ở đây thì người dùng không phải ăn một toast đỏ cho một cú kéo
  //  hiển nhiên là lỡ tay.
  if (!taskId || taskId === fromTaskId) return null

  //  Nửa trái hay nửa phải thì đo trên chính THANH, không đo trên cái mép vừa
  //  chạm: mép phải rộng 7px nằm ở cuối thanh, lấy nó làm mốc thì "nửa trái của
  //  mép" vẫn là nửa PHẢI của thanh.
  const bar =
    document.querySelector<HTMLElement>(`[data-gantt-bar][data-task-id="${taskId}"]`) ?? hit
  const rect = bar.getBoundingClientRect()
  return { taskId, side: clientX < rect.left + rect.width / 2 ? 'start' : 'end' }
}
