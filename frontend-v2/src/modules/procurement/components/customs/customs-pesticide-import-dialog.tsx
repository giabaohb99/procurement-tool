// Nạp lại danh mục thuốc BVTV từ tệp của bản cào danhmuc.thuocbvtv.com (`thuoc-bvtv.json` hoặc
// `thuoc-bvtv.xlsx`). THAY TOÀN BỘ thuốc lấy từ nguồn, GIỮ thuốc tự thêm trên màn (duoc-CR-490) —
// nên hộp thoại nói rõ số thuốc sắp bị thay, số được giữ, và chỗ sửa tay trên thuốc nguồn sẽ mất.
// Backend đọc + kiểm hết tệp rồi mới xóa, tệp hỏng thì danh mục cũ còn nguyên.
//
// Nút Nạp chặn bấm đúp bằng `useRef` ngay trong lượt bấm — `disabled` chỉ đổi ở lượt vẽ sau.
// Đang nạp thì KHÔNG cho đóng hộp: đóng là mất `useRef`, mở lại bấm tiếp là hai lượt thay toàn bộ
// chạy song song (backend có khóa chặn trả 409, đây là để người dùng khỏi ăn lỗi đó).
import { FileJson, TriangleAlert, Upload } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

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
import { formatDateTime } from '@/shared/utils/format-date'
import { formatFileSize } from '@/shared/utils/format-file-size'

import { useImportCustomsPesticides } from '../../hooks/use-customs-pesticides'
import { CustomsNotice } from './customs-controls'

const ACCEPTED = '.json,.xlsx'

interface CustomsPesticideImportDialogProps {
  /** Số thuốc đang có (gồm cả thuốc tự thêm). */
  currentTotal: number
  /** Số thuốc tự thêm trên màn — nạp lại GIỮ chúng. */
  manualCount: number
  /** Lần nạp gần nhất — để người nạp biết danh mục đang có cũ tới đâu. */
  lastLoadedAt: string | null
  onClose: () => void
}

export function CustomsPesticideImportDialog({
  currentTotal,
  manualCount,
  lastLoadedAt,
  onClose,
}: CustomsPesticideImportDialogProps) {
  const sourcedTotal = Math.max(currentTotal - manualCount, 0)
  const [file, setFile] = useState<File | null>(null)
  const busy = useRef(false)
  const importMutation = useImportCustomsPesticides()
  const pending = importMutation.isPending

  function close() {
    if (!pending) onClose()
  }

  async function submit() {
    if (busy.current || !file) return
    busy.current = true
    try {
      const result = await importMutation.mutateAsync(file)
      toast.success(
        `Đã nạp ${result.pesticides.toLocaleString('vi-VN')} thuốc, ` +
            `${result.uses.toLocaleString('vi-VN')} dòng phạm vi sử dụng` +
          (result.kept_manual > 0
            ? `, giữ ${result.kept_manual.toLocaleString('vi-VN')} thuốc tự thêm`
            : '') +
          (result.dropped > 0
            ? `, bỏ ${result.dropped.toLocaleString('vi-VN')} thuốc không còn trong tệp`
            : ''),
      )
      onClose()
    } catch {
      //  `httpClient` đã báo lỗi (sai định dạng, thiếu sheet…) bằng toast.
    } finally {
      busy.current = false
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && close()}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Nạp danh mục thuốc BVTV</DialogTitle>
          <DialogDescription>
            Tệp <b>thuoc-bvtv.json</b> hoặc <b>thuoc-bvtv.xlsx</b> của bản cào danh mục thuốc BVTV
            (danhmuc.thuocbvtv.com — dữ liệu EcoFarm của Cục BVTV).
          </DialogDescription>
        </DialogHeader>

        <FileDropzone
          accept={ACCEPTED}
          busy={pending}
          hint="Kéo thả tệp vào đây hoặc bấm để chọn"
          //  Khớp `MAX_UPLOAD_BYTES` của `pesticide_controller.py` (30 MB) — bản cũ ghi 60 MB.
          description=".json hoặc .xlsx · tối đa 30 MB"
          onFiles={(picked) => setFile(picked[0] ?? null)}
        />
        {file && (
          <p className="flex items-center gap-2 text-sm">
            <FileJson className="size-4 shrink-0 text-muted-foreground" />
            <span className="min-w-0 flex-1 truncate">{file.name}</span>
            <span className="shrink-0 text-xs text-muted-foreground">{formatFileSize(file.size)}</span>
          </p>
        )}
        {currentTotal > 0 && (
          <CustomsNotice tone="warning" icon={<TriangleAlert className="size-4" />}>
            Nạp tệp sẽ <b>thay toàn bộ</b> {sourcedTotal.toLocaleString('vi-VN')} thuốc lấy từ nguồn
            {lastLoadedAt ? ` (nạp lần cuối ${formatDateTime(lastLoadedAt)})` : ''} — chỗ sửa tay
            trên các thuốc đó sẽ bị ghi đè theo tệp mới — rồi gắn lại hoạt chất cho mọi dòng hàng
            hải quan. Thuốc vẫn còn trong tệp mới giữ nguyên tệp đính kèm; thuốc{' '}
            <b>không còn</b> trong tệp mới bị xóa cùng tệp đính kèm của nó.
            {manualCount > 0 && (
              <>
                {' '}
                <b>{manualCount.toLocaleString('vi-VN')} thuốc tự thêm</b> trên màn được giữ nguyên.
              </>
            )}
          </CustomsNotice>
        )}

        <DialogFooter>
          <Button type="button" variant="outline" disabled={pending} onClick={close}>
            Hủy
          </Button>
          <Button type="button" disabled={!file || pending} onClick={() => void submit()}>
            <Upload className="size-4" />
            {pending ? 'Đang nạp…' : 'Nạp danh mục'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
