import { useRef, useState } from 'react'

import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import {
  DESC_MAX,
  NAME_MAX,
  SECURITY_LEVEL,
  SECURITY_LEVEL_OPTIONS,
  SKILL_SET_STATUS,
  SKILL_SET_STATUS_OPTIONS,
} from '../config/ai-skill-constants'
import { useCreateSkillSet, useUpdateSkillSet } from '../hooks/use-ai-skill'
import type { SkillSet } from '../types/ai-skill'

/** Bộ không gắn phòng chủ quản lưu `0` ở backend — đó là một lựa chọn thật, không phải «chưa chọn». */
const NO_DEPARTMENT = '0'

interface SkillSetFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Có = sửa bộ này; không = tạo bộ mới. */
  skillSet?: SkillSet
  onCreated?: (created: SkillSet) => void
}

/**
 * Hộp tạo / sửa BỘ skill (G2, doc 21 §6.2). Mã bộ chỉ nhập lúc tạo (backend không cho đổi). Mặc định tạo ở trạng thái
 * Nháp + mức Mở: bộ mới chưa lộ ra AI của ai cho tới khi chuyển Đang dùng và gán quyền đọc.
 */
export function SkillSetFormDialog({ open, onOpenChange, skillSet, onCreated }: SkillSetFormDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90dvh] flex-col overflow-hidden sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{skillSet ? 'Sửa bộ skill' : 'Tạo bộ skill'}</DialogTitle>
          <DialogDescription>
            Một bộ gom các skill cùng một mảng việc (ví dụ quy trình thu mua). Quyền đọc gán theo bộ.
          </DialogDescription>
        </DialogHeader>
        {/*  `key` dựng lại biểu mẫu mỗi lần mở / đổi bộ — không mang chữ gõ dở của lần trước sang. */}
        {open && <SkillSetForm key={skillSet?.id ?? 'new'} skillSet={skillSet} onDone={onOpenChange} onCreated={onCreated} />}
      </DialogContent>
    </Dialog>
  )
}

function SkillSetForm({
  skillSet,
  onDone,
  onCreated,
}: {
  skillSet?: SkillSet
  onDone: (open: boolean) => void
  onCreated?: (created: SkillSet) => void
}) {
  const create = useCreateSkillSet()
  const update = useUpdateSkillSet(skillSet?.id ?? 0)
  const { data: departments } = useDepartments({ page_size: 500 })
  const [name, setName] = useState(skillSet?.name ?? '')
  const [code, setCode] = useState(skillSet?.code ?? '')
  const [description, setDescription] = useState(skillSet?.description ?? '')
  const [departmentId, setDepartmentId] = useState(String(skillSet?.owner_department_id ?? 0))
  const [status, setStatus] = useState(String(skillSet?.status ?? SKILL_SET_STATUS.draft))
  const [security, setSecurity] = useState(String(skillSet?.security_level ?? SECURITY_LEVEL.open))
  const [error, setError] = useState('')
  //  Bấm đúp nút Lưu: `disabled={isPending}` chỉ có hiệu lực ở lượt render sau, nên chặn bằng ref đổi ngay trong tick
  //  (bẫy biểu mẫu thứ tư, duoc-CR-317).
  const busy = useRef(false)

  async function handleSubmit() {
    if (busy.current) return
    const trimmed = name.trim()
    if (!trimmed) {
      setError('Nhập tên bộ skill.')
      return
    }
    setError('')
    busy.current = true
    try {
      const common = {
        name: trimmed,
        description: description.trim(),
        owner_department_id: Number(departmentId),
        status: Number(status),
        security_level: Number(security),
      }
      if (skillSet) {
        await update.mutateAsync(common)
      } else {
        const created = await create.mutateAsync({ ...common, code: code.trim() })
        onCreated?.(created)
      }
      onDone(false)
    } catch {
      //  Lỗi đã có toast tự động (câu backend) — giữ hộp mở để sửa.
    } finally {
      busy.current = false
    }
  }

  const activeDepartments = (departments?.items ?? []).filter((d) => d.is_active || d.id === skillSet?.owner_department_id)
  const pending = create.isPending || update.isPending

  return (
    <>
      <div className="-mx-6 min-h-0 flex-1 space-y-4 overflow-y-auto px-6">
        <div className="space-y-1.5">
          <Label htmlFor="skill-set-name">
            Tên bộ <RequiredMark hint="Bắt buộc" />
          </Label>
          <Input
            id="skill-set-name"
            value={name}
            maxLength={NAME_MAX}
            onChange={(e) => setName(e.target.value)}
            placeholder="Quy trình thu mua"
            aria-invalid={Boolean(error)}
          />
          {error && <p className="text-xs text-destructive">{error}</p>}
        </div>

        {!skillSet && (
          <div className="space-y-1.5">
            <Label htmlFor="skill-set-code">Mã bộ</Label>
            <Input
              id="skill-set-code"
              value={code}
              maxLength={50}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Để trống thì hệ thống tự đặt"
            />
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="skill-set-description">Mô tả</Label>
          <Textarea
            id="skill-set-description"
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value.slice(0, DESC_MAX))}
            placeholder="Bộ này dùng cho ai, việc gì"
          />
        </div>

        <div className="space-y-1.5">
          <Label>Phòng chủ quản</Label>
          <Select value={departmentId} onValueChange={setDepartmentId}>
            <SelectTrigger className="w-full" aria-label="Phòng chủ quản">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={NO_DEPARTMENT}>Không gắn phòng</SelectItem>
              {activeDepartments.map((d) => (
                <SelectItem key={d.id} value={String(d.id)}>
                  {d.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>Trạng thái</Label>
          <RadioGroup value={status} onValueChange={setStatus} className="grid gap-2">
            {SKILL_SET_STATUS_OPTIONS.map((option) => (
              <label key={option.value} className="flex items-start gap-2 text-sm">
                <RadioGroupItem value={String(option.value)} className="mt-0.5" />
                <span>
                  {option.label}
                  <span className="block text-xs text-muted-foreground">{option.hint}</span>
                </span>
              </label>
            ))}
          </RadioGroup>
        </div>

        <div className="space-y-1.5">
          <Label>Mức bảo mật</Label>
          <RadioGroup value={security} onValueChange={setSecurity} className="grid gap-2">
            {SECURITY_LEVEL_OPTIONS.map((option) => (
              <label key={option.value} className="flex items-start gap-2 text-sm">
                <RadioGroupItem value={String(option.value)} className="mt-0.5" />
                <span>
                  {option.label}
                  <span className="block text-xs text-muted-foreground">{option.hint}</span>
                </span>
              </label>
            ))}
          </RadioGroup>
        </div>
      </div>

      <DialogFooter className="shrink-0 border-t pt-4">
        <Button type="button" variant="outline" onClick={() => onDone(false)}>
          Hủy
        </Button>
        <Button type="button" onClick={() => void handleSubmit()} disabled={pending}>
          {skillSet ? 'Lưu' : 'Tạo bộ'}
        </Button>
      </DialogFooter>
    </>
  )
}
