// Nạp lại danh mục thuốc BVTV — chấp nhận CẢ BA loại tệp: bản cào gốc (`thuoc-bvtv.json` /
// `.xlsx` từ danhmuc.thuocbvtv.com), tệp xuất «Toàn bộ danh mục» hoặc tệp xuất «Trang hiện tại»
// (xem `customs-pesticide-export-menu.tsx`). Backend tự nhận ra loại tệp qua sheet ẩn và trả về
// `mode`: bản cào gốc/tệp toàn bộ → THAY cả danh mục (GIỮ thuốc tự thêm, duoc-CR-490); tệp theo
// trang → chỉ CẬP NHẬT đúng các thuốc có trong tệp, phần còn lại giữ nguyên. Hộp thoại không tự
// đoán trước loại tệp (chỉ biết sau khi nạp xong) nên câu cảnh báo số thuốc sắp bị thay ở dưới chỉ
// đúng cho trường hợp THAY — đã nói rõ bằng chữ. Backend đọc + kiểm hết tệp rồi mới xóa, tệp hỏng
// thì danh mục cũ còn nguyên.
//
// Nút Nạp chặn bấm đúp bằng `useRef` ngay trong lượt bấm — `disabled` chỉ đổi ở lượt vẽ sau.
// Đang nạp thì KHÔNG cho đóng hộp: đóng là mất `useRef`, mở lại bấm tiếp là hai lượt thay toàn bộ
// chạy song song (backend có khóa chặn trả 409, đây là để người dùng khỏi ăn lỗi đó).
import { FileJson, Info, TriangleAlert, Upload } from 'lucide-react'
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
      const { result, message } = await importMutation.mutateAsync(file)
      //  Có `mode` = backend đã biết phân biệt tệp toàn bộ / tệp theo trang, câu `message` của nó
      //  đã đúng theo từng chế độ — hiện NGUYÊN câu đó. Backend CŨ chưa trả `mode` thì tự ghép câu
      //  như trước (chỉ đúng cho chế độ THAY, vì bản cũ chỉ có một chế độ).
      toast.success(
        result.mode && message
          ? message
          : `Đã nạp ${result.pesticides.toLocaleString('vi-VN')} thuốc, ` +
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

        <CustomsNotice tone="info" icon={<Info className="size-4" />}>
          Tệp toàn bộ danh mục (bản cào gốc hoặc xuất «Toàn bộ danh mục») sẽ{' '}
          <b>thay cả danh mục</b>. Tệp xuất «Trang hiện tại» chỉ <b>cập nhật</b> đúng các thuốc có
          trong tệp (thêm thuốc mới nếu chưa có), phần còn lại giữ nguyên.
        </CustomsNotice>

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
