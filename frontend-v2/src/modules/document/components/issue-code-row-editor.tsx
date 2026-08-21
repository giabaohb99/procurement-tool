import { AlertTriangle, Check, Loader2 } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'
import type { IssueCodeRow } from '../types/issue-code'

interface IssueCodeRowEditorProps {
  row: IssueCodeRow
  pending: boolean
  onSave: (issueCode: string, force: boolean) => void
}

/**
 * MỘT dòng mã: tên đơn vị · ô nhập mã · nút lưu.
 *
 * Nút lưu chỉ hiện khi giá trị đã đổi — bày sẵn một hàng nút cho 60 dòng thì
 * mắt không nhặt ra nổi dòng nào mình vừa sửa.
 *
 * Đơn vị **đã cấp số** thì phải bấm HAI lần: lần đầu đổi nút thành «Vẫn đổi» và
 * hiện câu hậu quả. Chốt D07 ở backend vẫn chặn lần bấm thứ nhất; lần thứ hai
 * gửi kèm `force` và đi vào nhật ký thao tác. Người dùng chốt như vậy
 * (21/08/2026) thay cho khóa cứng — nhưng khóa cứng chỉ được nới TẠI ĐÂY, các
 * màn khác giữ nguyên.
 */
export function IssueCodeRowEditor({ row, pending, onSave }: IssueCodeRowEditorProps) {
  const [value, setValue] = useState(row.issue_code)
  const [xacNhan, setXacNhan] = useState(false)

  const daDoi = value.trim() !== row.issue_code
  const canXacNhan = row.da_cap_so && daDoi

  function luu() {
    if (canXacNhan && !xacNhan) {
      setXacNhan(true)
      return
    }
    onSave(value.trim(), xacNhan)
    setXacNhan(false)
  }

  return (
    <div className="grid grid-cols-[1fr_170px_auto] items-start gap-3 border-b py-2 last:border-b-0">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{row.name}</p>
        <p className="truncate text-xs text-muted-foreground">{row.code}</p>
      </div>

      <div className="space-y-1">
        <Input
          className={cn('h-8 font-mono', canXacNhan && xacNhan && 'border-amber-400')}
          value={value}
          placeholder="(chưa có mã)"
          onChange={(event) => {
            setValue(event.target.value)
            //  Sửa tiếp sau khi đã bấm «Vẫn đổi» thì phải hỏi lại từ đầu — câu
            //  cảnh báo vừa đọc nói về một giá trị khác.
            setXacNhan(false)
          }}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && daDoi) {
              event.preventDefault()
              luu()
            }
          }}
        />
        {/* Mã của đơn vị kinh doanh / ban dự án không đi vào số hiệu (A05) —
            nói ra để người dùng khỏi ngồi sửa một ô vô tác dụng. */}
        {row.trong_so_hieu === false && (
          <p className="text-xs text-muted-foreground">Không vào số hiệu</p>
        )}
      </div>

      <div className="flex min-h-8 items-center">
        {daDoi ? (
          <Button
            type="button"
            size="sm"
            variant={xacNhan ? 'destructive' : 'default'}
            disabled={pending}
            onClick={luu}
          >
            {pending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : xacNhan ? (
              <AlertTriangle className="size-4" />
            ) : (
              <Check className="size-4" />
            )}
            {xacNhan ? 'Vẫn đổi' : 'Lưu'}
          </Button>
        ) : (
          row.da_cap_so && (
            <span className="text-xs text-muted-foreground">Đã cấp số</span>
          )
        )}
      </div>

      {xacNhan && (
        <p className="col-span-3 flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          <AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-amber-700" />
          <span>
            <b>{row.name}</b> đã có văn bản mang số với mã «{row.issue_code || '(trống)'}».
            Số đã cấp giữ nguyên chuỗi cũ, số mới dùng mã mới — sổ sẽ có hai kiểu mã cạnh
            nhau. Lần đổi này đi vào nhật ký thao tác.
          </span>
        </p>
      )}
    </div>
  )
}
