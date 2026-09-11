import { useCallback, useLayoutEffect, useRef, useState } from 'react'

/**
 * Bậc ưu tiên của một lệnh trên thanh công cụ.
 *
 * `medium` = nhóm hay dùng (canh lề), chỉ thu vào menu khi thanh đã rất hẹp.
 * `wide` = nhóm thỉnh thoảng mới cần (chỉ số trên/dưới, thụt lề, trích dẫn…),
 * thu vào menu trước tiên.
 */
export type ToolbarTier = 'medium' | 'wide'

/**
 * Bề rộng tối thiểu của THANH CÔNG CỤ (px) để mỗi bậc còn được đứng ngoài.
 *
 * Đo theo bề rộng thật của thanh chứ không theo bề rộng màn hình: cùng một máy,
 * menu trái thu hay mở đã làm lệch mất ~256px, nên lấy mốc theo màn hình là đoán
 * sai. Quy ra máy thật (menu trái đang mở):
 *  - 13" (1280–1440px): thanh còn ~980–1140px → giữ canh lề ngoài, phần còn lại
 *    gom vào menu "Thêm" để thanh vẫn gọn MỘT hàng.
 *  - 15,6" trở lên (1600–1920px): thanh ~1300–1660px → bày hết ra ngoài.
 */
const TIER_MIN_WIDTH: Record<ToolbarTier, number> = {
  medium: 1120,
  wide: 1360,
}

/**
 * Dưới mốc này thanh đổi hẳn HÌNH DẠNG, không chỉ thu bớt nút: chỉ còn mục lục ·
 * hoàn tác · làm lại · mức phóng, mọi lệnh định dạng dọn vào tấm `⋮` (xem
 * `EditorFormatPopover`).
 *
 * ⚠️ **Thu bớt nút KHÔNG cứu được khổ điện thoại.** Hai bậc trên chỉ đụng tới 11
 * lệnh khai ở `collapsible-toolbar-commands`; phần còn lại — bốn ô chọn (phóng ·
 * kiểu đoạn · phông · cỡ) — **một mình đã ~440px** vì bề rộng của chúng bị ghim
 * theo nhãn dài nhất (xem bảng số đo ở `toolbar-style-selects`). Trên thanh 358px
 * thì có thu hết 11 lệnh kia vào menu «Thêm» vẫn còn tràn ba hàng. Nên mốc này
 * không phải "bậc thứ ba", nó là một bố cục khác.
 *
 * **640px** chứ không phải 768px của `useIsMobile`: đây đo bề rộng THẬT của thanh
 * chứ không phải của màn hình — cùng một máy, menu trái thu hay mở đã lệch ~256px.
 * Máy tính hẹp nhất còn dùng thanh đầy đủ là ~900px thanh, nên 640 nằm giữa hai
 * thế giới mà không chạm bên nào.
 */
const COMPACT_MAX_WIDTH = 640

/**
 * Đo bề rộng thanh công cụ để quyết định lệnh nào đứng ngoài, lệnh nào thu vào
 * menu "Thêm".
 *
 * Dùng `ResizeObserver` + `useLayoutEffect` thay cho `@media`/container query:
 * menu thu gọn nằm trong portal (ngoài cây DOM của thanh) nên container query
 * không với tới được, mà đo trước khi vẽ thì cũng không thấy cảnh nút hiện ra
 * rồi biến mất ở khung hình đầu tiên.
 */
export function useToolbarDensity() {
  const ref = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(0)

  useLayoutEffect(() => {
    const node = ref.current
    if (!node) return

    // So sánh trước khi set: `ResizeObserver` bắn liên tục lúc kéo cửa sổ, set
    // đúng giá trị cũ chỉ tổ vẽ lại vô ích.
    const measure = () =>
      setWidth((current) => (current === node.clientWidth ? current : node.clientWidth))

    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  const fits = useCallback((tier: ToolbarTier) => width >= TIER_MIN_WIDTH[tier], [width])

  //  ⚠️ `width > 0` để KHÔNG rơi vào chế độ gọn ở lượt vẽ đầu. `useLayoutEffect`
  //  đo sau lượt render đầu tiên, nên trước khi đo xong `width` là `0` — thiếu vế
  //  này thì máy tính cũng nháy một nhịp thanh gọn rồi mới bung ra thanh đầy đủ.
  const compact = width > 0 && width < COMPACT_MAX_WIDTH

  return { ref, fits, compact }
}
