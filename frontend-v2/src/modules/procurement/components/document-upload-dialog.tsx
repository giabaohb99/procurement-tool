import { Loader2, Plus, Trash2, Upload, X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatFileSize } from '@/shared/utils/format-file-size'
import {
  useDocumentTypes,
  useUploadDocumentBatches,
} from '../hooks/use-purchase-request-support'
import { OTHER_DOC_TYPE, withOtherType } from '../utils/document-attachment-groups'

/** Một mục sắp tải lên: chọn loại chứng từ rồi thả tệp của đúng loại đó vào. */
interface UploadRow {
  docType: string
  files: File[]
}

interface DocumentUploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** `purchase_request` | `purchase_order` | `survey` | `contract` — quyết định chính sách tệp ở backend. */
  entity: string
  entityId: number
  /** Hạn mức MỘT tệp (MB) chỉ để hiện đúng câu nhắc; ngưỡng thật ở `FILE_POLICY` backend. */
  maxSizeMb?: number
  /**
   * Loại chứng từ điền sẵn cho mục đầu tiên.
   *
   * Mở từ nút "Upload thêm tệp cho mục này" thì phải đúng mục đang xem, không
   * thì người dùng bấm từ thư mục Hóa đơn GTGT mà tệp lại rơi vào Khác.
   */
  initialDocType?: string
}

/**
 * Tải chứng từ theo LOẠI, nhiều loại trong một lượt.
 *
 * Khác vùng kéo-thả nhanh ngoài thẻ (mọi tệp rơi vào một mục đang mở): ở đây một
 * bộ hồ sơ vừa nhận về — báo giá, PO ký, hóa đơn — được chia đúng ngăn ngay lúc
 * tải, thay vì tải hết vào "Khác" rồi ngồi phân loại lại từng tệp.
 */
export function DocumentUploadDialog({
  open,
  onOpenChange,
  entity,
  entityId,
  maxSizeMb = 50,
  initialDocType = OTHER_DOC_TYPE,
}: DocumentUploadDialogProps) {
  const [rows, setRows] = useState<UploadRow[]>([{ docType: initialDocType, files: [] }])
  const { data: documentTypes } = useDocumentTypes()
  const upload = useUploadDocumentBatches(entity, entityId)
  const options = withOtherType(documentTypes ?? [])

  // Mỗi lần mở là một lượt tải mới: còn giữ lựa chọn cũ thì bấm "Lưu chứng từ"
  // lần hai sẽ tải lại đúng xấp tệp vừa tải xong.
  const openChanged = useHasChanged(open)
  if (openChanged && open) setRows([{ docType: initialDocType, files: [] }])

  const totalFiles = rows.reduce((sum, row) => sum + row.files.length, 0)

  function patchRow(index: number, changes: Partial<UploadRow>) {
    setRows((current) =>
      current.map((row, position) => (position === index ? { ...row, ...changes } : row)),
    )
  }

  function addFiles(index: number, selected: File[]) {
    setRows((current) =>
      current.map((row, position) => {
        if (position !== index) return row
        // Thả hai lần cùng một tệp là chuyện thường khi kéo từ nhiều cửa sổ —
        // chống trùng theo tên + dung lượng để khỏi tải lên hai bản y hệt.
        const seen = new Set(row.files.map((file) => `${file.name}|${file.size}`))
        const added = selected.filter((file) => !seen.has(`${file.name}|${file.size}`))
        return { ...row, files: [...row.files, ...added] }
      }),
    )
  }

  function removeFile(index: number, fileIndex: number) {
    setRows((current) =>
      current.map((row, position) =>
        position === index
          ? { ...row, files: row.files.filter((_, order) => order !== fileIndex) }
          : row,
      ),
    )
  }

  async function submit() {
    const batches = rows
      .filter((row) => row.files.length > 0)
      .map((row) => ({ docType: row.docType || OTHER_DOC_TYPE, files: row.files }))

    if (!batches.length) {
      toast.error('Chưa chọn tệp nào để tải lên.')
      return
    }

    try {
      await upload.mutateAsync(batches)
      onOpenChange(false)
    } catch {
      // Lỗi của POST đã được `http-client` bật toast sẵn — giữ hộp thoại mở để
      // người dùng bỏ bớt tệp quá nặng rồi lưu lại, không bắt chọn lại từ đầu.
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[92dvh] flex-col gap-0 overflow-hidden p-0 sm:max-w-2xl">
        <DialogHeader className="border-b px-5 py-4 pr-12">
          <DialogTitle className="flex items-center gap-2">
            <Upload className="size-4 text-primary" />
            Upload chứng từ
          </DialogTitle>
          <DialogDescription>
            Mỗi mục là một loại chứng từ. Thêm mục để tải nhiều loại trong cùng một lượt.
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 space-y-4 overflow-auto px-5 py-4">
          {rows.map((row, index) => (
            <div
              key={index}
              className="flex items-start gap-2 border-b border-dashed pb-4 last:border-b-0 last:pb-0"
            >
              <div className="min-w-0 flex-1 space-y-2">
                <Select
                  value={row.docType}
                  onValueChange={(value) => patchRow(index, { docType: value })}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Chọn loại chứng từ" />
                  </SelectTrigger>
                  <SelectContent>
                    {options.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <FileDropzone
                  hint="Kéo thả hoặc bấm chọn tệp — PDF, ảnh, Word, Excel, XML (hóa đơn), TXT, CDR…"
                  disabled={upload.isPending}
                  onFiles={(selected) => addFiles(index, selected)}
                />

                {row.files.length > 0 && (
                  <ul className="space-y-1">
                    {row.files.map((file, fileIndex) => (
                      <li
                        key={`${file.name}|${file.size}`}
                        className="flex items-center gap-2 rounded-md bg-muted/60 px-2 py-1.5 text-xs"
                      >
                        <span className="min-w-0 flex-1 truncate" title={file.name}>
                          {file.name}
                        </span>
                        <span className="shrink-0 text-muted-foreground">
                          {formatFileSize(file.size)}
                        </span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-xs"
                          className="text-destructive hover:text-destructive"
                          title="Bỏ tệp này"
                          aria-label={`Bỏ tệp ${file.name}`}
                          disabled={upload.isPending}
                          onClick={() => removeFile(index, fileIndex)}
                        >
                          <X />
                        </Button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="text-destructive hover:text-destructive"
                title="Xóa mục này"
                aria-label="Xóa mục chứng từ"
                disabled={rows.length === 1 || upload.isPending}
                onClick={() => setRows((current) => current.filter((_, p) => p !== index))}
              >
                <Trash2 />
              </Button>
            </div>
          ))}

          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={upload.isPending}
            onClick={() => setRows((current) => [...current, { docType: OTHER_DOC_TYPE, files: [] }])}
          >
            <Plus />
            Thêm loại chứng từ
          </Button>
        </div>

        <DialogFooter className="items-center border-t px-5 py-3 sm:justify-between">
          <span className="text-xs text-muted-foreground">
            {totalFiles > 0 ? `Đã chọn ${totalFiles} tệp` : `Mỗi tệp tối đa ${maxSizeMb} MB`}
          </span>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={upload.isPending}
              onClick={() => onOpenChange(false)}
            >
              Hủy
            </Button>
            <Button type="button" disabled={upload.isPending} onClick={() => void submit()}>
              {upload.isPending && <Loader2 className="animate-spin" />}
              {upload.isPending ? 'Đang lưu…' : 'Lưu chứng từ'}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
