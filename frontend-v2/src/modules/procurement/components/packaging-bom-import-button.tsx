/**
 * duoc-CR-784 — nút "Nhập từ Excel" của màn Định mức bao bì: tải `DATA_CHAI.xlsx` lên Quản lý Import
 * (`ImportModule.PACKAGING_BOM = 4`), LUÔN chạy thử trước, rồi sang trang chi tiết lô để xem nhật ký
 * từng dòng và bấm "Ghi thật". Lô này chưa hỗ trợ hoàn tác (phase 03).
 *
 * Không dùng `ImportUploadDialog` của Quản lý Import: ô chọn bảng ở đó chỉ biết các đối tượng khai trong
 * `system/config/import-meta.ts`, module 4 chưa có nên ô hiện trống. Hiện khi có ĐỦ `import.create` +
 * `import.read` (trang lô gác `import.read`) + `packaging_cost.create` — backend gác lại y hệt.
 */
import { FileUp, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { useUploadImport } from '@/modules/system/hooks/use-imports'
import { IMPORT_MODE_DRY_RUN } from '@/modules/system/config/import-meta'
import { appRoutes } from '@/shared/constants/app-routes'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
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

/** `ImportModule.PACKAGING_BOM` ở `backend/app/modules/import_tool/model.py`. */
const IMPORT_MODULE_PACKAGING_BOM = 4

export function PackagingBomImportButton() {
  const { can } = usePermission()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const upload = useUploadImport()
  const once = useSingleFlight()

  if (!(can('import', 'create') && can('import', 'read') && can('packaging_cost', 'create')))
    return null

  const submit = () =>
    once(async () => {
      if (!file) return
      try {
        const batch = await upload.mutateAsync({
          module: IMPORT_MODULE_PACKAGING_BOM,
          mode: IMPORT_MODE_DRY_RUN,
          file,
        })
        setOpen(false)
        navigate(appRoutes.system.importDetail(batch.id))
      } catch (error) {
        toast.error(extractErrorMessage(error))
      }
    })

  return (
    <>
      <Button
        type="button"
        variant="outline"
        className="max-md:w-full"
        onClick={() => setOpen(true)}
      >
        <FileUp />
        Nhập từ Excel
      </Button>
      {open && (
        <Dialog open onOpenChange={(next) => !next && !upload.isPending && setOpen(false)}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Nhập định mức bao bì</DialogTitle>
              <DialogDescription>
                Tệp DATA_CHAI.xlsx (sheet MAP_SP, hoặc data + DATA CHUNG). Hệ thống chạy thử trước —
                xem nhật ký từng dòng ở trang lô rồi mới bấm Ghi thật. Mã HH đã có thì cập nhật,
                chưa có thì tạo; dòng không có trong tệp giữ nguyên.
              </DialogDescription>
            </DialogHeader>
            <FileDropzone
              accept=".xlsx"
              busy={upload.isPending}
              description={file ? `Đã chọn: ${file.name}` : 'Chỉ nhận tệp .xlsx'}
              onFiles={(files) => {
                const picked = files[0]
                if (picked && !picked.name.toLowerCase().endsWith('.xlsx')) {
                  toast.error('Chỉ nhận tệp .xlsx')
                  return
                }
                setFile(picked ?? null)
              }}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                disabled={upload.isPending}
                onClick={() => setOpen(false)}
              >
                Hủy
              </Button>
              <Button
                type="button"
                disabled={!file || upload.isPending}
                onClick={() => void submit()}
              >
                {upload.isPending && <Loader2 className="size-4 animate-spin" />}
                Chạy thử
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </>
  )
}
