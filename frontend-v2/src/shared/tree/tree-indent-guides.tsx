import type { CSSProperties } from 'react'

/** Bề ngang một cấp thụt lề — khớp ô chevron 16px của dòng tổ tiên. */
const INDENT_STEP_PX = 16

/**
 * Số cấp thụt lề TỐI ĐA được vẽ. Cây thư mục văn bản sâu tới 100 cấp
 * (26/09/2026): thụt đủ 100 cấp là 1600px trong khung 200-480px — từ khoảng cấp
 * 8 tên thư mục bị ép còn 0 ký tự, dòng khớp tìm kiếm nằm lệch ngoài khung.
 * Sâu hơn trần thì dòng đứng yên ở trần và ghi `+n` cấp bị giấu; đường dẫn
 * đầy đủ vẫn có ở tooltip của dòng. Chọn 6 vì đo trên khung mặc định 288px:
 * trần 12 (192px) vẫn để tên thư mục cấp 9 trở đi còn 0 ký tự.
 */
const MAX_VISIBLE_INDENT_LEVELS = 6

interface TreeIndentGuidesProps {
  /** Số cấp thụt lề — 0 (gốc) không vẽ gì. */
  depth: number
  /**
   * Đậm hơn — dòng ĐANG CHỌN kẻ đường gióng đậm để mắt bám theo nhánh dễ hơn.
   * Đơn giản hoá có chủ đích: chỉ đậm đường gióng của CHÍNH dòng đang chọn,
   * không kẻ liền một mạch xuống hết các dòng con cháu cùng nhánh.
   */
  bold: boolean
}

/**
 * Đường gióng thụt lề dọc — mỗi cấp một vạch 1px kẻ tại tâm ô 16px để thẳng
 * hàng với chevron của dòng tổ tiên ở cấp đó.
 *
 * ⚠️ Vẽ bằng MỘT span có nền lặp, KHÔNG phải một span mỗi cấp (26/09/2026):
 * bản cũ dựng 2 phần tử DOM mỗi cấp, cây 100 cấp mở hết ra 104 dòng mà mang
 * ~10.000 phần tử chỉ để kẻ vạch — mỗi phím gõ vào ô lọc cây khóa giao diện
 * 200-560ms vì React phải đối chiếu lại toàn bộ. Nay mỗi dòng tối đa 2 phần tử
 * bất kể sâu bao nhiêu.
 */
export function TreeIndentGuides({ depth, bold }: TreeIndentGuidesProps) {
  if (depth <= 0) return null
  const visibleLevels = Math.min(depth, MAX_VISIBLE_INDENT_LEVELS)
  const hiddenLevels = depth - visibleLevels
  const lineColor = bold
    ? 'color-mix(in oklab, var(--muted-foreground) 50%, transparent)'
    : 'var(--border)'
  const center = INDENT_STEP_PX / 2
  const style: CSSProperties = {
    width: visibleLevels * INDENT_STEP_PX,
    backgroundImage: `linear-gradient(to right, transparent ${center - 0.5}px, ${lineColor} ${center - 0.5}px, ${lineColor} ${center + 0.5}px, transparent ${center + 0.5}px)`,
    backgroundSize: `${INDENT_STEP_PX}px 100%`,
    backgroundRepeat: 'repeat-x',
  }
  return (
    <>
      <span
        data-tree-indent-guide
        data-tree-indent-levels={visibleLevels}
        aria-hidden
        className="h-6 shrink-0"
        style={style}
      />
      {hiddenLevels > 0 && (
        <span
          aria-hidden
          title={`Sâu thêm ${hiddenLevels} cấp`}
          className="shrink-0 rounded bg-muted px-1 text-[10px] leading-4 text-muted-foreground tabular-nums"
        >
          +{hiddenLevels}
        </span>
      )}
    </>
  )
}
