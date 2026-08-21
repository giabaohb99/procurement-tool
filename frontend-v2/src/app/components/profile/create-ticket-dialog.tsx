import { Loader2, Upload, X } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { ticketApi, type UploadedFile } from '@/modules/support/api/ticket-api'
import { TICKET_PRIORITY_OPTIONS } from '@/modules/support/config/ticket-constants'
import { useCreateTicket } from '@/modules/support/hooks/use-tickets'
import type { TicketDetail } from '@/modules/support/types/ticket'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'

const DEPARTMENTS = [
  'Hệ thống / CNTT',
  'Thu mua / Cung ứng',
  'Kế toán / Tài chính',
  'Nhân sự / Hành chính',
  'Sản xuất / Kho',
  'Khác',
]

interface CreateTicketDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function CreateTicketDialog({
  open,
  onOpenChange,
  onSuccess,
}: CreateTicketDialogProps) {
  const navigate = useNavigate()
  const createMutation = useCreateTicket()

  const [subject, setSubject] = useState('')
  const [department, setDepartment] = useState('Hệ thống / CNTT')
  const [priority, setPriority] = useState('normal')
  const [body, setBody] = useState('')
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [uploading, setUploading] = useState(false)

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(e.target.files || [])
    if (selectedFiles.length === 0) return

    setUploading(true)
    try {
      const uploaded = await ticketApi.uploadMessageFiles(selectedFiles)
      setFiles((prev) => [...prev, ...uploaded])
      toast.success(`Đã tải lên ${uploaded.length} tệp đính kèm`)
    } catch {
      toast.error('Không thể tải tệp đính kèm')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  function removeFile(fileId: number) {
    setFiles((prev) => prev.filter((f) => f.file_id !== fileId))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!subject.trim()) {
      toast.error('Vui lòng nhập chủ đề phiếu hỗ trợ')
      return
    }
    if (!body.trim()) {
      toast.error('Vui lòng nhập nội dung chi tiết')
      return
    }

    createMutation.mutate(
      {
        subject: subject.trim(),
        department,
        priority,
        body: body.trim(),
        origin_url: window.location.pathname,
        file_ids: files.map((f) => f.file_id),
      },
      {
        onSuccess: (newTicket: TicketDetail) => {
          onOpenChange(false)
          setSubject('')
          setBody('')
          setFiles([])
          onSuccess?.()
          navigate(`/support/tickets/${newTicket.id}`)
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>Gửi phiếu yêu cầu hỗ trợ mới</DialogTitle>
            <DialogDescription>
              Mô tả sự cố hoặc yêu cầu cần hỗ trợ. Bộ phận CNTT / Hỗ trợ sẽ tiếp nhận và xử lý.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            <div>
              <Label htmlFor="ticket-subject" className="text-xs font-semibold">
                Chủ đề yêu cầu <span className="text-destructive">*</span>
              </Label>
              <Input
                id="ticket-subject"
                value={subject}
                placeholder="VD: Không tải được báo cáo thu mua, lỗi cấp quyền..."
                className="mt-1"
                onChange={(e) => setSubject(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="ticket-dept" className="text-xs font-semibold">
                  Bộ phận liên quan
                </Label>
                <Select value={department} onValueChange={setDepartment}>
                  <SelectTrigger id="ticket-dept" className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DEPARTMENTS.map((dept) => (
                      <SelectItem key={dept} value={dept}>
                        {dept}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="ticket-priority" className="text-xs font-semibold">
                  Mức độ ưu tiên
                </Label>
                <Select value={priority} onValueChange={setPriority}>
                  <SelectTrigger id="ticket-priority" className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TICKET_PRIORITY_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="ticket-body" className="text-xs font-semibold">
                Nội dung chi tiết <span className="text-destructive">*</span>
              </Label>
              <Textarea
                id="ticket-body"
                value={body}
                rows={4}
                placeholder="Mô tả chi tiết các bước gặp lỗi, hình ảnh hoặc yêu cầu hỗ trợ..."
                className="mt-1 text-xs"
                onChange={(e) => setBody(e.target.value)}
              />
            </div>

            <div>
              <Label className="text-xs font-semibold">Tệp đính kèm / Ảnh minh họa</Label>
              <div className="mt-1.5 flex flex-wrap items-center gap-2">
                <label className="flex h-8 cursor-pointer items-center gap-1.5 rounded-md border border-input bg-background px-3 text-xs font-medium hover:bg-accent hover:text-accent-foreground">
                  {uploading ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <Upload className="size-3.5 text-muted-foreground" />
                  )}
                  <span>{uploading ? 'Đang tải lên...' : 'Chọn tệp đính kèm'}</span>
                  <input
                    type="file"
                    multiple
                    className="hidden"
                    disabled={uploading}
                    onChange={handleFileUpload}
                  />
                </label>
              </div>

              {files.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {files.map((file) => (
                    <span
                      key={file.file_id}
                      className="inline-flex items-center gap-1 rounded-md border bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                    >
                      <span className="max-w-[150px] truncate">{file.filename}</span>
                      <button
                        type="button"
                        onClick={() => removeFile(file.file_id)}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <X className="size-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Hủy
            </Button>
            <Button type="submit" disabled={createMutation.isPending || uploading}>
              {createMutation.isPending && <Loader2 className="size-4 animate-spin" />}
              Gửi phiếu hỗ trợ
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
