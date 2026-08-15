import { cn } from '@/shared/utils/cn'
import type { ColumnDropSide } from './types'

interface ColumnDropIndicatorProps {
  /** Cột kéo sẽ chèn vào trước hay sau ô tiêu đề đang chứa vạch này. */
  side: ColumnDropSide
}

/**
 * Vạch báo chỗ sắp thả khi kéo đổi vị trí cột: một sọc dọc nằm ĐÚNG trên ranh
 * giới hai cột, hai đầu có chóp mũi tên nhọn chỉ vào khe sẽ chèn.
 *
 * Vẽ bằng phần tử tuyệt đối chứ không dùng `inset shadow` như trước: bóng đổ chỉ
 * nằm gọn trong ô nên vạch bị lệch hẳn vào một bên khe và không thể vẽ chóp.
 *
 * `z-30` để vạch nổi trên nền của ô liền kề — mọi `<th>` đều `position: relative`
 * nên ô đứng sau trong DOM sẽ phủ lên nửa vạch tràn sang nếu không nâng lớp.
 * Cột ghim (`z-20`) tự tạo ngữ cảnh xếp lớp riêng nên vạch bên trong nó vẫn nằm
 * trong phạm vi cột, đúng ý.
 */
export function ColumnDropIndicator({ side }: ColumnDropIndicatorProps) {
  return (
    <span
      aria-hidden
      className={cn(
        'pointer-events-none absolute inset-y-0 z-30 w-[3px] -translate-x-1/2 rounded-full bg-primary',
        side === 'before' ? 'left-0' : 'left-full',
      )}
    >
      {/*
        Chóp trên/dưới là tam giác dựng bằng viền (`border`) — nhẹ hơn SVG và ăn
        theo `--primary` như thân vạch. Cho tràn ra ngoài ô một chút (`-top-1`,
        `-bottom-1`) để nhìn thấy rõ trên hàng tiêu đề chỉ cao 36px.
      */}
      <span className="absolute -top-1 left-1/2 size-0 -translate-x-1/2 border-x-[5px] border-t-[6px] border-x-transparent border-t-primary" />
      <span className="absolute -bottom-1 left-1/2 size-0 -translate-x-1/2 border-x-[5px] border-b-[6px] border-x-transparent border-b-primary" />
    </span>
  )
}
