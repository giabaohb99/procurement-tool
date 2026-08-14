import { Ban, Pipette } from 'lucide-react'

import { COLOR_PALETTE_ROWS } from './editor-options'

interface ColorPaletteProps {
  onPick: (color: string) => void
  onClear: () => void
  /** Chữ trên nút bỏ màu — mỗi chỗ gọi một cách nói ("Bỏ tô nền", "Màu mặc định"). */
  clearLabel: string
}

/**
 * Bảng chọn màu dùng chung: 60 ô màu dựng sẵn + một nút chọn màu tự do.
 *
 * Bày THẲNG trong menu chứ không giấu sau một lớp menu con: đổ màu là việc làm
 * đi làm lại hàng chục lần trong một cái bảng, thêm một nhịp rê chuột nữa là
 * mỗi lần đổi màu mất ba thao tác.
 *
 * `onMouseDown` chặn mặc định ở mọi nút: bấm mà để trình duyệt dời con trỏ ra
 * khỏi vùng soạn thảo là mất luôn vùng đang bôi đen, màu sẽ đổ nhầm chỗ.
 */
export function ColorPalette({ onPick, onClear, clearLabel }: ColorPaletteProps) {
  return (
    <div className="w-max p-1.5">
      <div className="grid grid-cols-10 gap-1">
        {COLOR_PALETTE_ROWS.flat().map((color) => (
          <button
            key={color}
            type="button"
            title={color}
            aria-label={color}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => onPick(color)}
            className="size-4.5 rounded-[3px] border border-black/10 transition-transform hover:scale-115"
            style={{ backgroundColor: color }}
          />
        ))}
      </div>

      <div className="mt-1.5 flex items-center gap-1">
        <button
          type="button"
          onMouseDown={(event) => event.preventDefault()}
          onClick={onClear}
          className="flex flex-1 items-center gap-1.5 rounded px-2 py-1 text-left text-xs text-muted-foreground hover:bg-accent"
        >
          <Ban className="size-3.5" />
          {clearLabel}
        </button>

        {/* Ô chọn màu của trình duyệt nấp sau cái nhãn này: nó là thứ duy nhất
            mở được bảng màu đầy đủ (có cả mã hex) mà không phải tự dựng lại. */}
        <label
          title="Chọn màu tự do"
          onMouseDown={(event) => event.preventDefault()}
          className="flex cursor-pointer items-center gap-1.5 rounded px-2 py-1 text-xs text-muted-foreground hover:bg-accent"
        >
          <Pipette className="size-3.5" />
          Màu khác
          <input
            type="color"
            className="sr-only"
            onChange={(event) => onPick(event.target.value)}
          />
        </label>
      </div>
    </div>
  )
}
