import { useEffect, useState } from 'react'

import { resolveDropZone, type DropZone } from './resolve-drop-zone'

/**
 * State + tính VÙNG THẢ của MỘT dòng `TreeView` — tách khỏi `tree-row.tsx`
 * (thuần JSX) để giữ tệp đó dưới 200 dòng theo luật modularization.
 *
 * `dropDefined`/`canDropInto` khác nhau: `dropDefined` là "dòng này CÓ được
 * xét làm đích thả VÀO hay không" (`dropState(node)` khác `undefined`),
 * `canDropInto` là "và có HỢP LỆ hay không" (`=== 'valid'`) — dòng `invalid`
 * vẫn phải `preventDefault` để nhận sự kiện `drop` (JS tự bỏ qua), không dựa
 * vào con trỏ "cấm" mặc định của trình duyệt (không đồng nhất giữa các hệ
 * điều hành).
 */
export function useTreeRowDropZone(dropDefined: boolean, canDropInto: boolean, canReorder: boolean) {
  const dropPossible = dropDefined || canReorder
  const [hoverZone, setHoverZone] = useState<DropZone | null>(null)

  //  An toàn khi kéo kết thúc theo cách không bắn `dragleave` lên đúng dòng
  //  (thả ra ngoài cửa sổ, Esc giữa chừng…) — không thì chỉ báo còn sót lại.
  useEffect(() => {
    if (!dropPossible) return
    function clear() {
      setHoverZone(null)
    }
    window.addEventListener('dragend', clear)
    window.addEventListener('drop', clear)
    return () => {
      window.removeEventListener('dragend', clear)
      window.removeEventListener('drop', clear)
    }
  }, [dropPossible])

  /** Vùng thả tại đúng toạ độ con trỏ hiện tại — gọi lại ở CẢ `dragover` (để vẽ)
   * lẫn `drop` (để quyết định gọi callback nào), không đọc lại `hoverZone`. */
  function resolveZone(event: { currentTarget: HTMLElement; clientY: number }): DropZone | null {
    const rect = event.currentTarget.getBoundingClientRect()
    //  `rect.height = 0` (môi trường test không đo layout thật) → coi như
    //  giữa dòng, tránh chia cho 0 ra `NaN` lan vào so sánh.
    const ratioY = rect.height > 0 ? (event.clientY - rect.top) / rect.height : 0.5
    return resolveDropZone(ratioY, { canDropInto, canReorder })
  }

  return { dropPossible, hoverZone, setHoverZone, resolveZone }
}
