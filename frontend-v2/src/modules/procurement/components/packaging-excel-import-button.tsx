/**
 * duoc-CR-784 — nút nhập Excel dùng chung của cụm Giá NVL sản xuất (định mức bao bì, báo giá VTBB, Sổ Misa — khai ở
 * `config/packaging-excel-imports.ts`). Tải tệp lên Quản lý Import, LUÔN chạy thử trước, rồi sang trang chi tiết lô để xem
 * nhật ký từng dòng và bấm "Ghi thật". Hộp thoại có nút "Tải tệp mẫu" (`GET /api/imports/template?module=`).
 *
 * Không dùng `ImportUploadDialog` của Quản lý Import: ô chọn bảng ở đó chỉ biết các đối tượng khai trong
 * `system/config/import-meta.ts` có `moduleId`. Hiện khi có ĐỦ `import.create` + `import.read` (trang lô gác `import.read`)
 * + quyền `kind.action` trên `kind.entity` (bao-CR-792: khóa của màn chứa nút, không còn khóa chung `packaging_cost`) —
 * backend gác lại y hệt.
 */
import { FileDown, FileUp, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { downloadFile } from '@/core/api/download-file'
import { usePermission } from '@/core/authorization/use-permission'
import { IMPORT_MODE_DRY_RUN } from '@/modules/system/config/import-meta'
import { useUploadImport } from '@/modules/system/hooks/use-imports'
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

import type { PackagingExcelImportKind } from '../config/packaging-excel-imports'

interface PackagingExcelImportButtonProps {
  kind: PackagingExcelImportKind
}

export function PackagingExcelImportButton({ kind }: PackagingExcelImportButtonProps) {
  const { can } = usePermission()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [downloading, setDownloading] = useState(false)
  const upload = useUploadImport()
  const once = useSingleFlight()

  if (!(can('import', 'create') && can('import', 'read') && can(kind.entity, kind.action)))
    return null

  const submit = () =>
    once(async () => {
      if (!file) return
      try {
        const batch = await upload.mutateAsync({ module: kind.module, mode: IMPORT_MODE_DRY_RUN, file })
        setOpen(false)
        navigate(appRoutes.system.importDetail(batch.id))
      } catch (error) {
        toast.error(extractErrorMessage(error))
      }
    })

  const downloadTemplate = () =>
    once(async () => {
      setDownloading(true)
      try {
        await downloadFile('/api/imports/template', kind.templateName, { module: kind.module })
      } catch (error) {
        toast.error(extractErrorMessage(error))
      } finally {
        setDownloading(false)
      }
    })

  return (
    <>
      <Button
        type="button"
        variant="outline"
        //  `flex-1` chứ không `w-full`: ở màn CRUD nút nằm cạnh nút "Thêm" trong một hàng KHÔNG xuống dòng — `w-full` đẩy
        //  nút "Thêm" tràn ra ngoài mép phải ở khổ điện thoại; `flex-1` chia đều hàng với nó.
        className="max-md:flex-1"
        onClick={() => setOpen(true)}
      >
        <FileUp />
        {kind.label}
      </Button>
      {open && (
        <Dialog open onOpenChange={(next) => !next && !upload.isPending && setOpen(false)}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>{kind.title}</DialogTitle>
              <DialogDescription>{kind.description}</DialogDescription>
            </DialogHeader>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="w-fit"
              disabled={downloading}
              onClick={() => void downloadTemplate()}
            >
              {downloading ? <Loader2 className="size-4 animate-spin" /> : <FileDown />}
              Tải tệp mẫu
            </Button>
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
              <Button type="button" variant="outline" disabled={upload.isPending} onClick={() => setOpen(false)}>
                Hủy
              </Button>
              <Button type="button" disabled={!file || upload.isPending} onClick={() => void submit()}>
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
