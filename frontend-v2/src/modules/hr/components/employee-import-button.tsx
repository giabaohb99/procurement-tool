import { FileUp } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
//  Import chéo phân hệ: hộp thoại tải tệp là của «Quản lý Import»; màn Nhân sự chỉ khóa đối tượng lại.
import { ImportUploadDialog } from '@/modules/system/components/import-upload-dialog'
import { IMPORT_MODULE_EMPLOYEE } from '@/modules/system/config/import-meta'

/**
 * Nút «Nhập Excel» của màn Nhân sự (duoc-CR-628). Bấm → hộp thoại tải tệp (khóa đối tượng «Nhân sự»,
 * mặc định «Chạy thử») → sang trang chi tiết lô để xem log, «Ghi thật» hoặc «Hoàn tác».
 *
 * Hiện khi có ĐỦ: `import.create` + `import.read` (trang chi tiết lô gác `import.read` — thiếu thì tạo
 * xong bị đá 403) + (`employee.create` hoặc `employee.write`). Backend gác lại y hệt ở `/api/imports`.
 */
export function EmployeeImportButton() {
  const { can } = usePermission()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const allowed =
    can('import', 'create') &&
    can('import', 'read') &&
    (can('employee', 'create') || can('employee', 'write'))
  if (!allowed) return null

  return (
    <>
      <Button variant="outline" className="max-md:w-full" onClick={() => setOpen(true)}>
        <FileUp />
        Nhập Excel
      </Button>
      <ImportUploadDialog
        open={open}
        onOpenChange={setOpen}
        lockedModule={IMPORT_MODULE_EMPLOYEE}
        onCreated={(id) => navigate(appRoutes.system.importDetail(id))}
      />
    </>
  )
}
