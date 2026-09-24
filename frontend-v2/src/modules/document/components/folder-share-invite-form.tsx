import { ChevronDown } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/shared/ui/collapsible'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { useGrantFolderAccessBulk } from '../hooks/use-document-folder-access'
import { EFFECT } from '../types/document-access'
import { FOLDER_ACCESS_LEVEL_LABELS } from '../types/document-folder'
import { FolderShareSubjectPicker, type MixedSubject } from './folder-share-subject-picker'

interface FolderShareInviteFormProps {
  folderId: number
}

/**
 * Khối MỜI trên cùng của hộp «Chia sẻ» kiểu Drive (đặc tả §C/§P7, làm lại UI
 * 23/09/2026) — ô chọn nhiều đứng RIÊNG, không còn bọc trong khung viền to
 * (bug lead bắt: "remove the big bordered box"). Ô mức quyền + nút «Cấp
 * quyền» CHỈ HIỆN khi đã chọn ≥1 đối tượng — trước đó form chỉ có mỗi ô chọn,
 * đúng luồng "chọn người rồi mới quyết định cấp gì" của Drive thay vì bày sẵn
 * hết mọi ô. «Cấm» + hiệu lực từ–đến + lý do gấp trong «Tùy chọn nâng cao» —
 * Cho là mặc định, không còn cặp radio Cho/Cấm nổi bật ngay ngoài.
 *
 * Chỉ hiện khi `folder-share-dialog.tsx` đã xác nhận người xem đủ mức Quản
 * lý — tệp này không tự kiểm quyền lần hai.
 */
export function FolderShareInviteForm({ folderId }: FolderShareInviteFormProps) {
  const grantBulk = useGrantFolderAccessBulk(folderId)
  const [subjects, setSubjects] = useState<MixedSubject[]>([])
  const [effect, setEffect] = useState(String(EFFECT.allow))
  const [level, setLevel] = useState('1')
  const [validFrom, setValidFrom] = useState('')
  const [validTo, setValidTo] = useState('')
  const [reason, setReason] = useState('')
  const [advancedOpen, setAdvancedOpen] = useState(false)

  const isDeny = Number(effect) === EFFECT.deny

  function reset() {
    setSubjects([])
    setEffect(String(EFFECT.allow))
    setLevel('1')
    setValidFrom('')
    setValidTo('')
    setReason('')
  }

  function handleGrant() {
    if (subjects.length === 0) return
    grantBulk.mutate(
      {
        subjects,
        effect: Number(effect),
        level: isDeny ? undefined : Number(level),
        valid_from: validFrom || null,
        valid_to: validTo || null,
        reason: reason.trim(),
      },
      { onSuccess: reset },
    )
  }

  return (
    <div className="space-y-3">
      <div className="space-y-1.5">
        <Label>Chọn đối tượng</Label>
        <FolderShareSubjectPicker value={subjects} onChange={setSubjects} />
      </div>

      {subjects.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          {!isDeny && (
            <Select value={level} onValueChange={setLevel}>
              <SelectTrigger className="w-40" aria-label="Mức quyền">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[1, 2, 3].map((value) => (
                  <SelectItem key={value} value={String(value)}>
                    {FOLDER_ACCESS_LEVEL_LABELS[value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Button type="button" onClick={handleGrant} disabled={grantBulk.isPending}>
            Cấp quyền ({subjects.length})
          </Button>
        </div>
      )}

      <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
        <CollapsibleTrigger asChild>
          <button type="button" className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
            <ChevronDown className={cn('size-3.5 transition-transform', advancedOpen && 'rotate-180')} />
            Tùy chọn nâng cao — cấm, hiệu lực từ–đến, lý do
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-3 pt-3">
          <div className="space-y-1.5">
            <Label>Chiều tác động</Label>
            <RadioGroup value={effect} onValueChange={setEffect} className="flex gap-4">
              <label className="flex items-center gap-2 text-sm">
                <RadioGroupItem value={String(EFFECT.allow)} />
                Cho
              </label>
              <label className="flex items-center gap-2 text-sm">
                <RadioGroupItem value={String(EFFECT.deny)} />
                Cấm
              </label>
            </RadioGroup>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="space-y-1.5">
              <Label>Hiệu lực từ</Label>
              <DatePicker value={validFrom} onChange={setValidFrom} />
            </div>
            <div className="space-y-1.5">
              <Label>Đến</Label>
              <DatePicker value={validTo} onChange={setValidTo} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="folder-share-reason">Lý do</Label>
              <Input id="folder-share-reason" value={reason} onChange={(e) => setReason(e.target.value)} />
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}
