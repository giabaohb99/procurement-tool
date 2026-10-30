import { FileText, Plus, Trash2 } from 'lucide-react'
import { useRef, useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Textarea } from '@/shared/ui/textarea'
import { formatDateTime } from '@/shared/utils/format-date'
import { FILE_MAX_BYTES, TEXT_FILE_EXTS, formatBytes, validateFilePath } from '../config/ai-skill-constants'
import { useDeleteSkillFile, usePutSkillFile } from '../hooks/use-ai-skill'
import type { SkillFile } from '../types/ai-skill'

interface SkillFilesCardProps {
  skillId: number
  files: SkillFile[]
  canWrite: boolean
}

/**
 * Khối "Tệp đi kèm" của trang soạn skill (G4): biểu mẫu, bảng tra, ví dụ mà SKILL.md nhắc tới. Chỉ nhận tệp CHỮ
 * (≤ 2 MB mỗi tệp) vì AI đọc chúng dạng chữ qua cổng kết nối. Kéo thả tệp có sẵn hoặc gõ tay một tệp mới. Ghi đè:
 * lưu lại đúng tên cũ là thay nội dung.
 */
export function SkillFilesCard({ skillId, files, canWrite }: SkillFilesCardProps) {
  const put = usePutSkillFile(skillId)
  const remove = useDeleteSkillFile(skillId)
  const [composing, setComposing] = useState(false)
  const [path, setPath] = useState('')
  const [content, setContent] = useState('')
  const [error, setError] = useState('')
  const busy = useRef(false)

  async function save(filePath: string, text: string) {
    const problem = validateFilePath(filePath)
    if (problem) {
      setError(problem)
      return false
    }
    if (new Blob([text]).size > FILE_MAX_BYTES) {
      setError(`Tệp quá ${formatBytes(FILE_MAX_BYTES)}.`)
      return false
    }
    if (busy.current) return false
    busy.current = true
    setError('')
    try {
      await put.mutateAsync({ path: filePath.trim(), content: text })
      return true
    } catch {
      return false
    } finally {
      busy.current = false
    }
  }

  async function handleDrop(dropped: File[]) {
    for (const file of dropped) {
      if (file.size > FILE_MAX_BYTES) {
        setError(`${file.name}: quá ${formatBytes(FILE_MAX_BYTES)}.`)
        continue
      }
      const ok = await save(file.name, await file.text())
      if (!ok) break
    }
  }

  async function handleCompose() {
    if (await save(path, content)) {
      setPath('')
      setContent('')
      setComposing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <SectionHeading>Tệp đi kèm ({files.length})</SectionHeading>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {files.length === 0 ? (
          <p className="text-muted-foreground">Chưa có tệp nào. Skill ngắn thì không cần tệp đi kèm.</p>
        ) : (
          <ul className="divide-y rounded-md border">
            {files.map((file) => (
              <li key={file.id} className="flex items-center gap-3 px-3 py-2">
                <FileText className="size-4 shrink-0 text-muted-foreground" />
                <span className="min-w-0 flex-1 truncate font-mono text-xs" title={file.path}>
                  {file.path}
                </span>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {formatBytes(file.size)}
                  {file.updated_at && ` · ${formatDateTime(file.updated_at)}`}
                </span>
                {canWrite && (
                  <ConfirmIconButton
                    icon={Trash2}
                    title={`Xóa tệp ${file.path}`}
                    confirmTitle={`Xóa tệp ${file.path}?`}
                    confirmLabel="Xóa"
                    destructive
                    disabled={remove.isPending}
                    onConfirm={() => remove.mutate(file.id)}
                  />
                )}
              </li>
            ))}
          </ul>
        )}

        {canWrite && (
          <>
            <FileDropzone
              onFiles={(dropped) => void handleDrop(dropped)}
              accept={TEXT_FILE_EXTS.join(',')}
              busy={put.isPending}
              hint="Kéo thả tệp chữ vào đây hoặc bấm để chọn"
              description={`${TEXT_FILE_EXTS.join(' ')} · tối đa ${formatBytes(FILE_MAX_BYTES)} mỗi tệp · trùng tên là ghi đè`}
            />
            {composing ? (
              <div className="space-y-2 rounded-md border p-3">
                <div className="space-y-1">
                  <Label htmlFor="skill-file-path">Tên tệp</Label>
                  <Input
                    id="skill-file-path"
                    value={path}
                    onChange={(e) => setPath(e.target.value)}
                    placeholder="mau/bang-gia.csv"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="skill-file-content">Nội dung</Label>
                  <Textarea
                    id="skill-file-content"
                    rows={6}
                    className="font-mono text-xs"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" size="sm" onClick={() => setComposing(false)}>
                    Hủy
                  </Button>
                  <Button type="button" size="sm" onClick={() => void handleCompose()} disabled={put.isPending}>
                    Lưu tệp
                  </Button>
                </div>
              </div>
            ) : (
              <Button type="button" variant="outline" size="sm" onClick={() => setComposing(true)}>
                <Plus className="size-4" />
                Gõ tệp mới
              </Button>
            )}
          </>
        )}
        {error && <p className="text-xs text-destructive">{error}</p>}
      </CardContent>
    </Card>
  )
}
