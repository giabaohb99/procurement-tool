import { Check, ChevronDown } from 'lucide-react'
import { useState } from 'react'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/utils/cn'
import type { WorkLabelField } from '../types/work'
import { chipClass } from '../utils/work-colors'

interface LabelMultiCellProps {
  field: WorkLabelField
  chosen: number[]
  disabled?: boolean
  onChange: (value: number[] | null) => void
}

/**
 * Trường CHỌN NHIỀU thu về vừa MỘT ô bảng ở khung nhìn Danh sách — một **ô chọn
 * nhiều**, cùng dáng với các ô chọn một giá trị ở cột bên cạnh.
 *
 * Vì sao là danh sách thả xuống chứ không phải dải chip bật/tắt (bản trước):
 * cột Tag đứng ngay cạnh Trạng thái · Độ ưu tiên · Kênh — cả ba đều là ô chọn có
 * mũi tên, nên một ô không mũi tên nằm giữa trông như chữ chỉ để đọc, phải bấm
 * thử mới biết là sửa được. Dải chip còn hỏng thêm khi trường khai nhiều giá
 * trị: mười mấy chip bọc trong popover 240px thành một mảng màu, phải dò từng
 * cái xem cái nào đang mờ (= chưa chọn), trong khi một danh sách dọc có dấu tích
 * thì liếc là ra.
 *
 * Dùng `DropdownMenu` chứ không `Select`: Radix `Select` chỉ giữ được MỘT giá
 * trị. Mỗi mục khai `role="menuitemcheckbox"` nên trình đọc màn hình vẫn đọc
 * đúng là chọn-nhiều, và mục phải **chặn `onSelect`** để menu không đóng sau mỗi
 * lần tick — chọn ba giá trị mà phải mở lại menu ba lần là thao tác tệ hơn hẳn
 * dải chip cũ.
 */
export function LabelMultiCell({ field, chosen, disabled, onChange }: LabelMultiCellProps) {
  /*  Bộ đang chọn giữ Ở ĐÂY chứ không đọc thẳng `chosen` mỗi lần tick.

      Menu đứng yên để tick liên tiếp, mà `chosen` chỉ mới lại sau khi máy chủ
      trả lời và bảng nạp lại. Tick hai nhãn nhanh hơn một vòng gọi thì cả hai
      lượt cùng đọc `chosen` CŨ: lượt sau gửi đúng một mình nó và ghi đè lượt
      trước — tick ba nhãn chỉ dính nhãn cuối, mà không có lỗi nào báo.

      Cộng dồn trên bản nháp thì lượt sau luôn mang cả những gì vừa tick.  */
  const [draft, setDraft] = useState(chosen)
  //  Dữ liệu máy chủ đổi (lưu xong, người khác sửa, đổi sang task khác) thì
  //  bản nháp bám theo. So theo NỘI DUNG chứ không theo tham chiếu: mảng được
  //  dựng mới mỗi lần render ở tầng trên, so tham chiếu là đặt lại vô tận.
  const [seen, setSeen] = useState(chosen)
  if (!sameIds(seen, chosen)) {
    setSeen(chosen)
    setDraft(chosen)
  }

  const picked = field.options.filter((o) => draft.includes(o.id))

  function toggle(optionId: number) {
    const next = draft.includes(optionId)
      ? draft.filter((id) => id !== optionId)
      : [...draft, optionId]
    setDraft(next)
    //  Bỏ hết thì gửi `null` chứ không phải mảng rỗng — cùng một nghĩa "bỏ
    //  chọn" với năm kiểu trường kia, khỏi để máy chủ đoán.
    onChange(next.length === 0 ? null : next)
  }

  function clearAll() {
    setDraft([])
    onChange(null)
  }

  /*  Chỉ vẽ MỘT chip rồi dồn phần còn lại vào «+N»: ô rộng 150px mà hai chip
      tiếng Việt là đã tràn, còn cho xuống dòng thì mọi dòng của bảng cao gấp
      đôi. Tên đầy đủ của phần bị dồn nằm ở `title`, và mở menu là thấy hết.  */
  const faces = picked.length ? (
    <span className="flex min-w-0 items-center gap-1">
      <span
        className={cn(
          'truncate rounded px-1.5 py-0.5 text-[11px] font-medium',
          chipClass(picked[0].color),
        )}
      >
        {picked[0].name}
      </span>
      {picked.length > 1 && (
        <span
          title={picked
            .slice(1)
            .map((o) => o.name)
            .join(', ')}
          className="shrink-0 rounded bg-muted px-1 py-0.5 text-[11px] text-muted-foreground"
        >
          +{picked.length - 1}
        </span>
      )}
    </span>
  ) : null

  //  Chỉ xem: bày đúng chip, KHÔNG dựng nút — nút bấm không ăn gì là lừa người
  //  dùng (cùng luật với `task-chip-select`).
  if (disabled) {
    return faces ?? <span className="text-xs text-muted-foreground">—</span>
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label={field.name}
          className={cn(
            'flex h-7 max-w-full items-center gap-1 rounded px-1 text-left',
            'hover:bg-accent/60 dark:hover:bg-accent/60',
            'outline-none focus-visible:ring-2 focus-visible:ring-ring/50',
          )}
        >
          {faces ?? <span className="text-xs text-muted-foreground">Chưa chọn</span>}
          {/*  Mũi tên luôn hiện, không ẩn-hiện theo `hover` như biểu tượng Tag
              cũ: cột này phải nhìn ra là ô CHỌN ngay từ lúc chưa rê chuột, y
              như ba cột chọn nằm cạnh nó. */}
          <ChevronDown className="size-3.5 shrink-0 text-muted-foreground opacity-50" />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="max-h-72 w-56 overflow-y-auto">
        {field.options.length === 0 ? (
          <p className="px-2 py-3 text-center text-sm text-muted-foreground">
            Trường chưa khai giá trị
          </p>
        ) : (
          <>
            {field.options.map((o) => {
              const on = draft.includes(o.id)
              return (
                <DropdownMenuItem
                  key={o.id}
                  role="menuitemcheckbox"
                  aria-checked={on}
                  //  Giữ menu MỞ sau mỗi lần tick — đây là ô chọn nhiều.
                  onSelect={(su) => {
                    su.preventDefault()
                    toggle(o.id)
                  }}
                >
                  <span
                    className={cn(
                      'truncate rounded px-1.5 py-0.5 text-[11px] font-medium',
                      chipClass(o.color),
                    )}
                  >
                    {o.name}
                  </span>
                  {on && <Check className="ml-auto size-4 shrink-0" />}
                </DropdownMenuItem>
              )
            })}

            {draft.length > 0 && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onSelect={(su) => {
                    su.preventDefault()
                    clearAll()
                  }}
                  className="text-muted-foreground"
                >
                  Bỏ chọn hết
                </DropdownMenuItem>
              </>
            )}
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/** Hai bộ id có TRÙNG NHAU không — cùng phần tử là được, không cần cùng thứ tự. */
function sameIds(a: number[], b: number[]): boolean {
  if (a.length !== b.length) return false
  const cua = new Set(a)
  return b.every((id) => cua.has(id))
}
