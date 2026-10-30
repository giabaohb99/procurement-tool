import { FileArchive, TriangleAlert } from 'lucide-react'
import { useRef, useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { PACKAGE_EXTS, PACKAGE_MAX_BYTES, checkPackageFile, formatBytes, validateSlug } from '../config/ai-skill-constants'
import { useImportSkillPackage } from '../hooks/use-ai-skill'
import type { SkillImportResult, SkillSet } from '../types/ai-skill'

interface SkillImportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Bộ đích cố định (mở từ trang chi tiết bộ). Bỏ trống thì hộp cho chọn bộ trong `sets`. */
  setId?: number
  sets?: SkillSet[]
  onImported?: (result: SkillImportResult) => void
}

/**
 * Hộp "Tải gói lên" (G2 / G3): nhận gói skill `.zip` / `.skill` có SKILL.md. Trùng tên skill trong bộ là THAY GÓI —
 * ghi đè bản nháp và THAY TOÀN BỘ tệp đi kèm cũ (Agent 1 dặn phải báo rõ trên màn). Bản đang phát cho AI không đổi cho
 * tới khi bấm Xuất bản.
 */
export function SkillImportDialog({ open, onOpenChange, setId, sets, onImported }: SkillImportDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Tải gói skill lên</DialogTitle>
          <DialogDescription>
            Gói là tệp .zip hoặc .skill có SKILL.md (định dạng skill của Claude). Tên skill lấy từ trường name trong gói.
          </DialogDescription>
        </DialogHeader>
        {open && <ImportForm setId={setId} sets={sets} onDone={onOpenChange} onImported={onImported} />}
      </DialogContent>
    </Dialog>
  )
}

function ImportForm({
  setId,
  sets,
  onDone,
  onImported,
}: Omit<SkillImportDialogProps, 'open' | 'onOpenChange'> & { onDone: (open: boolean) => void }) {
  const importPackage = useImportSkillPackage()
  const [targetSet, setTargetSet] = useState(setId ? String(setId) : '')
  const [file, setFile] = useState<File | null>(null)
  const [slug, setSlug] = useState('')
  const [error, setError] = useState('')
  const busy = useRef(false)

  function pick(files: File[]) {
    const chosen = files[0]
    const problem = checkPackageFile(chosen)
    setError(problem)
    setFile(problem ? null : chosen)
  }

  async function handleSubmit() {
    if (busy.current) return
    const target = Number(targetSet)
    if (!target) return setError('Chọn bộ skill nhận gói.')
    if (!file) return setError('Chọn tệp gói.')
    if (slug.trim()) {
      const slugError = validateSlug(slug)
      if (slugError) return setError(slugError)
    }
    setError('')
    busy.current = true
    try {
      const result = await importPackage.mutateAsync({ setId: target, file, slug: slug.trim() })
      onImported?.(result)
      onDone(false)
    } catch {
      //  Toast lỗi tự động (vd "Gói phải có tệp SKILL.md") — giữ hộp mở.
    } finally {
      busy.current = false
    }
  }

  return (
    <>
      <div className="space-y-4">
        {!setId && (
          <div className="space-y-1.5">
            <Label>Bộ skill nhận gói</Label>
            <Select value={targetSet} onValueChange={setTargetSet}>
              <SelectTrigger className="w-full" aria-label="Bộ skill nhận gói">
                <SelectValue placeholder="Chọn bộ skill" />
              </SelectTrigger>
              <SelectContent>
                {(sets ?? []).map((s) => (
                  <SelectItem key={s.id} value={String(s.id)}>
                    {s.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <FileDropzone
          onFiles={pick}
          accept={PACKAGE_EXTS.join(',')}
          busy={importPackage.isPending}
          hint="Kéo thả gói skill vào đây hoặc bấm để chọn"
          description={`${PACKAGE_EXTS.join(' · ')} · tối đa ${formatBytes(PACKAGE_MAX_BYTES)}`}
        />
        {file && (
          <p className="flex items-center gap-2 text-sm">
            <FileArchive className="size-4 text-muted-foreground" />
            <span className="min-w-0 truncate font-medium">{file.name}</span>
            <span className="shrink-0 text-xs text-muted-foreground">{formatBytes(file.size)}</span>
          </p>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="skill-import-slug">Đặt tên skill khác (không bắt buộc)</Label>
          <Input
            id="skill-import-slug"
            value={slug}
            maxLength={100}
            onChange={(e) => setSlug(e.target.value)}
            placeholder="Để trống thì dùng tên trong gói"
          />
        </div>

        <p className="flex gap-2 rounded-md border border-warning/40 bg-warning/10 p-3 text-xs text-foreground">
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-warning" />
          <span>
            Nếu bộ đã có skill cùng tên, gói này sẽ <b>thay toàn bộ</b>: ghi đè bản nháp và xóa hết tệp đi kèm cũ của
            skill đó. Bản AI đang đọc chỉ đổi khi bạn bấm Xuất bản.
          </span>
        </p>

        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={() => onDone(false)}>
          Hủy
        </Button>
        <Button type="button" onClick={() => void handleSubmit()} disabled={importPackage.isPending || !file}>
          Tải lên
        </Button>
      </DialogFooter>
    </>
  )
}
