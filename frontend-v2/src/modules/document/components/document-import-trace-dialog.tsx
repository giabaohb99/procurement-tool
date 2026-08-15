import { AlertTriangle, CheckCircle2, FileSearch, Info, XCircle } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

export interface DocumentImportTraceIssue {
  code: string
  severity: 'info' | 'warning' | 'error'
  message: string
  pages: number[]
}

export interface DocumentImportTrace {
  source_type: 'pdf'
  import_id: string
  quality: 'editable_with_review' | 'mixed' | 'visual_only'
  page_count: number
  editable_page_count: number
  image_page_count: number
  issues: DocumentImportTraceIssue[]
}

interface DocumentImportTraceDialogProps {
  trace: DocumentImportTrace | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onNavigate?: (importId: string, page: number) => boolean
}

const qualityLabel = {
  editable_with_review: 'Có thể chỉnh sửa — cần rà soát',
  mixed: 'Nội dung hỗn hợp',
  visual_only: 'Chỉ giữ hình ảnh',
} satisfies Record<DocumentImportTrace['quality'], string>

const severityIcon = {
  info: Info,
  warning: AlertTriangle,
  error: XCircle,
} satisfies Record<DocumentImportTraceIssue['severity'], typeof Info>

/** Báo phần PDF chỉ khôi phục gần đúng và cho nhảy tới đúng trang nguồn. */
export function DocumentImportTraceDialog({
  trace,
  open,
  onOpenChange,
  onNavigate,
}: DocumentImportTraceDialogProps) {
  if (!trace) return null

  const navigate = (page: number) => {
    if (onNavigate?.(trace.import_id, page)) onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileSearch className="size-5" />
            Báo cáo đối chiếu PDF
          </DialogTitle>
          <DialogDescription>
            PDF lưu chữ theo tọa độ thay vì cấu trúc đoạn như Word. Báo cáo này đánh dấu các trang
            nên đối chiếu lại trước khi lưu mẫu.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 rounded-lg border bg-muted/30 p-4 sm:grid-cols-3">
          <div>
            <p className="text-xs text-muted-foreground">Kết quả</p>
            <Badge variant="secondary" className="mt-1">
              {qualityLabel[trace.quality]}
            </Badge>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Trang sửa được</p>
            <p className="mt-1 text-lg font-semibold">
              {trace.editable_page_count}/{trace.page_count}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Trang dạng ảnh</p>
            <p className="mt-1 text-lg font-semibold">{trace.image_page_count}</p>
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 rounded-lg border px-3 py-2">
          <span className="text-sm text-muted-foreground">Nhảy tới bất kỳ trang nguồn nào</span>
          <Select onValueChange={(value) => navigate(Number(value))}>
            <SelectTrigger size="sm" className="w-36">
              <SelectValue placeholder="Chọn trang" />
            </SelectTrigger>
            <SelectContent>
              {Array.from({ length: trace.page_count }, (_, index) => index + 1).map((page) => (
                <SelectItem key={page} value={String(page)}>
                  Trang {page}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          {trace.issues.map((issue) => {
            const Icon = severityIcon[issue.severity]
            return (
              <div key={issue.code} className="rounded-lg border p-3">
                <div className="flex items-start gap-3">
                  <Icon
                    className={
                      issue.severity === 'error'
                        ? 'mt-0.5 size-4 shrink-0 text-destructive'
                        : issue.severity === 'warning'
                          ? 'mt-0.5 size-4 shrink-0 text-amber-600'
                          : 'mt-0.5 size-4 shrink-0 text-blue-600'
                    }
                  />
                  <div className="min-w-0 flex-1 space-y-2">
                    <p className="text-sm leading-relaxed">{issue.message}</p>
                    {!!issue.pages.length && (
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="text-xs text-muted-foreground">Đi tới trang:</span>
                        {issue.pages.slice(0, 10).map((page) => (
                          <Button
                            key={page}
                            type="button"
                            variant="outline"
                            size="xs"
                            onClick={() => navigate(page)}
                          >
                            {page}
                          </Button>
                        ))}
                        {issue.pages.length > 10 && (
                          <span className="text-xs text-muted-foreground">
                            +{issue.pages.length - 10} trang
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        <DialogFooter>
          <Button type="button" onClick={() => onOpenChange(false)}>
            <CheckCircle2 className="size-4" />
            Đã hiểu, tiếp tục chỉnh sửa
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
