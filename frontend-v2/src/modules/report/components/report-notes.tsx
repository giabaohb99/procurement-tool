import { ChevronDown, Info } from 'lucide-react'
import { useState } from 'react'

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/shared/ui/collapsible'
import { cn } from '@/shared/utils/cn'

interface ReportNotesProps {
  /** `response.notes` — nguyên văn backend, tầng này không được lược bớt câu nào. */
  notes: string[]
}

/**
 * Lưu ý CÁCH TÍNH của một trang báo cáo — GẤP SẴN thành một dòng.
 *
 * Trước 01/10/2026 khối này mở sẵn, nằm chắn ngay trên thẻ KPI: thứ đầu tiên
 * người mở trang thấy là ba dòng chữ kỹ thuật ("nhóm theo loại CHÍNH của
 * đơn…"), đại ca chê xấu. Các câu này vẫn bắt buộc phải có (giải thích vì sao
 * hai con số cạnh nhau không bằng nhau) nên chỉ gấp lại, không bỏ — dòng gấp
 * ghi rõ có bao nhiêu lưu ý để người cần biết vẫn thấy chỗ mở.
 */
export function ReportNotes({ notes }: ReportNotesProps) {
  const [open, setOpen] = useState(false)
  if (notes.length === 0) return null

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="text-xs text-muted-foreground">
      <CollapsibleTrigger className="flex cursor-pointer items-center gap-1.5 rounded-sm hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none">
        <Info className="size-3.5 shrink-0" aria-hidden />
        <span>Cách tính số liệu ({notes.length} lưu ý)</span>
        <ChevronDown
          className={cn('size-3.5 transition-transform', open && 'rotate-180')}
          aria-hidden
        />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <ul className="mt-2 flex list-disc flex-col gap-1 rounded-md border bg-muted/40 py-2 pr-3 pl-7 leading-relaxed">
          {notes.map((note, index) => (
            <li key={index}>{note}</li>
          ))}
        </ul>
      </CollapsibleContent>
    </Collapsible>
  )
}
