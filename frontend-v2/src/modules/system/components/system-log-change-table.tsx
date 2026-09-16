import { EyeOff } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

import { CHANGE_OP, type SystemLogChangeEntry } from '../api/system-log-api'
import { changeValueText, tableLabel } from '../utils/system-log-format'

interface SystemLogChangeTableProps {
  changes: SystemLogChangeEntry[]
  /** `false` = người xem thiếu khóa `change_log`, KHÔNG phải «lượt này không đổi gì». */
  canRead: boolean
}

/**
 * Bảng GIÁ TRỊ TRƯỚC / SAU của một lượt gọi (bao-CR-407).
 *
 * Một dòng = MỘT TRƯỜNG (§4.3 của `nhat-ky-va-phien-dang-nhap.md`), gom theo bảng
 * vì một cú bấm Duyệt đụng ba bảng khác nhau và trộn chung thì không đọc ra bảng
 * nào là chứng từ, bảng nào là hệ quả.
 *
 * ⚠️ **Rỗng có hai nghĩa, phải nói ra nghĩa nào.** Mảng rỗng vì lượt gọi không
 * sửa gì, và mảng rỗng vì backend đã lược đi trước khi gửi — không có `canRead`
 * thì hai thứ đó là một, và người đọc kết luận sai về chính dữ liệu họ đang tra.
 */
export function SystemLogChangeTable({ changes, canRead }: SystemLogChangeTableProps) {
  if (!canRead) {
    return (
      <div className="flex items-start gap-2 rounded-lg border border-dashed border-input bg-muted/40 p-4 text-sm text-muted-foreground">
        <EyeOff className="mt-0.5 size-4 shrink-0" />
        <div>
          <p className="font-medium text-foreground">Bạn không được xem giá trị trước/sau</p>
          <p className="mt-0.5">
            Phần này cần khóa quyền <span className="font-mono text-xs">change_log</span>. Lượt gọi
            vẫn có thể đã sửa dữ liệu — đây là thiếu quyền xem, không phải «không đổi gì».
          </p>
        </div>
      </div>
    )
  }

  if (changes.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-input p-4 text-center text-sm text-muted-foreground">
        Lượt gọi này không sửa dữ liệu nào.
      </p>
    )
  }

  //  Gom theo bảng, GIỮ NGUYÊN thứ tự backend trả về (theo id tăng dần = thứ tự
  //  ghi thật). Sắp lại theo bảng chữ cái thì mất trình tự "bảng nào đụng trước".
  const groups: { table: string; rows: SystemLogChangeEntry[] }[] = []
  for (const row of changes) {
    const last = groups.at(-1)
    if (last && last.table === row.table_name) last.rows.push(row)
    else groups.push({ table: row.table_name, rows: [row] })
  }

  return (
    <div className="space-y-4">
      {groups.map((group, groupIndex) => (
        <div key={`${group.table}-${groupIndex}`} className="overflow-hidden rounded-lg border">
          <div className="flex items-center justify-between gap-2 border-b bg-muted/50 px-3 py-2">
            <span className="font-mono text-xs font-semibold">{tableLabel(group.table)}</span>
            <span className="text-xs text-muted-foreground">{group.rows.length} trường</span>
          </div>

          <table className="w-full table-fixed text-sm">
            <thead>
              <tr className="border-b text-xs text-muted-foreground">
                <th className="w-20 px-3 py-1.5 text-left font-medium">Dòng</th>
                <th className="w-44 px-3 py-1.5 text-left font-medium">Trường</th>
                <th className="px-3 py-1.5 text-left font-medium">Trước</th>
                <th className="px-3 py-1.5 text-left font-medium">Sau</th>
              </tr>
            </thead>
            <tbody>
              {group.rows.map((row) => (
                <tr key={row.id} className="border-b last:border-0 align-top">
                  <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                    #{row.row_id}
                  </td>
                  <td className="px-3 py-2">
                    <span className="font-mono text-xs break-all">{row.field}</span>
                    {row.op !== CHANGE_OP.UPDATE && (
                      <span className="ml-1.5 text-xs text-muted-foreground">({row.op_label})</span>
                    )}
                  </td>
                  <ChangeValueCell value={row.before_value} masked={row.is_masked} side="before" />
                  <ChangeValueCell value={row.after_value} masked={row.is_masked} side="after" />
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}

interface ChangeValueCellProps {
  value: string
  masked: boolean
  side: 'before' | 'after'
}

/**
 * Một ô giá trị.
 *
 * Đỏ/xanh chỉ tô khi có chữ THẬT: tô «(trống)» hay «(đã che)» thành đỏ thì hai
 * ghi chú của hệ thống trông như dữ liệu người dùng nhập.
 */
function ChangeValueCell({ value, masked, side }: ChangeValueCellProps) {
  const text = changeValueText(value, masked)
  const isNote = text === '(trống)' || text === '(đã che)'

  return (
    <td className="px-3 py-2">
      <span
        className={cn(
          'break-words text-xs',
          isNote && 'italic text-muted-foreground',
          !isNote && side === 'before' && 'text-destructive line-through decoration-destructive/40',
          !isNote && side === 'after' && 'font-medium text-success',
        )}
        title={isNote ? undefined : value}
      >
        {text}
      </span>
    </td>
  )
}
