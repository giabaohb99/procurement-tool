// duoc-CR-612 — hàng cuối «+ Thêm hồ sơ» của dạng «Bảng» trong khối Báo cáo thực hiện.
import { Loader2, Plus } from 'lucide-react'
import { useState } from 'react'

import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { SearchSelect } from '@/shared/ui/search-select'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { TableCell, TableRow } from '@/shared/ui/table'
import type { ReportDocPayload } from '../../api/survey-request-report-api'
import { REPORT_DOC_IDLE } from '../../types/survey-request-report'
import { cn } from '@/shared/utils/cn'
import { COMMON_ITEM_VALUE, STICKY_CELL, type SelectOption } from './survey-report-doc-sheet-layout'

interface ReportDocSheetAddRowProps {
  /** Số cột ô nút «Thêm» trải ra — phần còn lại của bảng sau 5 cột đầu. */
  restColSpan: number
  phaseOptions: SelectOption[]
  itemOptions: SelectOption[]
  defaultAssigneeId: number
  busy: boolean
  onCreate: (payload: ReportDocPayload) => Promise<unknown>
}

/**
 * Hàng cuối «+ Thêm hồ sơ»: gõ tên, (đổi giai đoạn / dòng hàng nếu cần), Enter là thêm — các ô
 * còn lại sửa ngay trên hàng vừa hiện. Giữ nguyên giai đoạn / dòng hàng sau mỗi lần
 * thêm để nhập liền tay nhiều hồ sơ cùng chỗ.
 */
export function ReportDocSheetAddRow({
  restColSpan,
  phaseOptions,
  itemOptions,
  defaultAssigneeId,
  busy,
  onCreate,
}: ReportDocSheetAddRowProps) {
  const [phaseId, setPhaseId] = useState(phaseOptions[0]?.value ?? '')
  const [itemId, setItemId] = useState(COMMON_ITEM_VALUE)
  const [title, setTitle] = useState('')
  const [pending, setPending] = useState(false)
  //  Enter liên tiếp / bấm đúp không được ra hai hồ sơ trùng (bẫy duoc-CR-317).
  const once = useSingleFlight()

  //  Giai đoạn đang chọn bị xóa (hoặc chưa có lúc mount) thì rơi về giai đoạn đầu.
  const effectivePhaseId = phaseOptions.some((option) => option.value === phaseId)
    ? phaseId
    : (phaseOptions[0]?.value ?? '')
  const effectiveItemId = itemOptions.some((option) => option.value === itemId)
    ? itemId
    : COMMON_ITEM_VALUE
  const trimmed = title.trim()

  const submit = () => {
    //  Kiểm rỗng TRƯỚC khi giữ khóa: Enter vào ô trống không được chiếm lượt (dù chỉ một
    //  nhịp) của lần Enter hợp lệ ngay sau đó.
    if (!trimmed || !effectivePhaseId || busy) return
    return once(async () => {
      setPending(true)
      try {
        await onCreate({
          title: trimmed,
          description: '',
          phase_id: Number(effectivePhaseId),
          item_id: Number(effectiveItemId) || 0,
          required: true,
          status: REPORT_DOC_IDLE,
          file_note: '',
          result: '',
          depends: [],
          start_date: '',
          expires_at: '',
          planned_date: '',
          assignee_id: defaultAssigneeId,
        })
        setTitle('')
      } catch {
        //  Lỗi đã có toast của lớp API chung; GIỮ chữ trong ô để bấm lại, không bắt gõ lại.
      } finally {
        setPending(false)
      }
    })
  }

  return (
    <TableRow className="hover:bg-transparent">
      <TableCell className={cn('bg-card px-2 py-2 text-muted-foreground', STICKY_CELL[0])}>
        <Plus className="size-4" />
      </TableCell>
      <TableCell className={cn('bg-card', STICKY_CELL[1])} />
      {/* Tên đứng ở cột ghim, cùng chỗ với tên các hồ sơ phía trên — gõ tên trước,
          giai đoạn / dòng hàng điền sẵn bên phải, đổi được. */}
      <TableCell className={cn('bg-card px-2 py-1.5', STICKY_CELL[2])}>
        <Input
          value={title}
          maxLength={255}
          placeholder="Tên hồ sơ mới, Enter để thêm…"
          aria-label="Tên hồ sơ mới"
          className="h-7 text-xs"
          onChange={(event) => setTitle(event.target.value)}
          onKeyDown={(event) => {
            //  Enter chốt chữ của bộ gõ tiếng Việt (`isComposing`) không phải Enter «thêm».
            if (event.nativeEvent.isComposing) return
            if (event.key === 'Enter') {
              event.preventDefault()
              void submit()
            }
          }}
        />
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <Select value={effectivePhaseId} onValueChange={setPhaseId}>
          <SelectTrigger
            size="sm"
            aria-label="Giai đoạn của hồ sơ mới"
            className="h-7 w-full px-2 text-xs"
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {phaseOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <SearchSelect
          size="sm"
          wrap
          value={effectiveItemId}
          onChange={(value) => setItemId(value || COMMON_ITEM_VALUE)}
          options={itemOptions}
          searchPlaceholder="Tìm dòng hàng…"
          emptyMessage="Không có dòng hàng nào"
          className="min-h-7 w-full text-xs"
        />
      </TableCell>
      <TableCell colSpan={restColSpan} className="px-2 py-1.5">
        <Button
          type="button"
          size="sm"
          className="h-7"
          disabled={!trimmed || pending || busy}
          onClick={() => void submit()}
        >
          {pending ? <Loader2 className="animate-spin" /> : <Plus />}
          Thêm hồ sơ
        </Button>
      </TableCell>
    </TableRow>
  )
}
