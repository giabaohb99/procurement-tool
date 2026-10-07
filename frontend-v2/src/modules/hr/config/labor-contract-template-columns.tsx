import { Download, FilePenLine, Pencil, Power, Replace, Trash2 } from 'lucide-react'

import type { DataTableColumn } from '@/shared/data-table'
import { LABOR_CONTRACT_TYPE, labelOf } from '@/shared/constants/statuses'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { formatDateTime } from '@/shared/utils/format-date'
import { formatFileSize } from '@/shared/utils/format-file-size'
import type { LaborContractTemplate } from '../types/labor-contract'

export interface LaborContractTemplateColumnActions {
  canWrite: boolean
  canDelete: boolean
  onDownload: (template: LaborContractTemplate) => void
  /** duoc-CR-606 — mở trang soạn nội dung trên web (người chỉ có quyền đọc vẫn mở xem được). */
  onEditContent: (template: LaborContractTemplate) => void
  /** duoc-CR-606 — hộp sửa tên / loại HĐ / ghi chú. */
  onEditInfo: (template: LaborContractTemplate) => void
  onReplaceFile: (template: LaborContractTemplate) => void
  onToggleActive: (template: LaborContractTemplate) => void
  onDelete: (template: LaborContractTemplate) => void
}

/**
 * Cột bảng «Mẫu hợp đồng». Là hàm vì cột «Thao tác» cần các callback của trang;
 * trang phải bọc kết quả bằng `useMemo`. Nút bị ẨN theo quyền ở đây — quyền thật do BE.
 */
export function buildLaborContractTemplateColumns(
  actions: LaborContractTemplateColumnActions,
): DataTableColumn<LaborContractTemplate>[] {
  const columns: DataTableColumn<LaborContractTemplate>[] = [
    { key: 'id', header: 'ID', width: 80, hideable: false, cell: (t) => t.id },
    {
      key: 'name',
      header: 'Tên mẫu',
      width: 260,
      hideable: false,
      wrap: true,
      cell: (t) => t.name,
    },
    {
      key: 'company',
      header: 'Pháp nhân',
      width: 240,
      wrap: true,
      cell: (t) => (
        <span>
          {t.company_name}
          {t.company_code && <span className="block text-xs text-muted-foreground">{t.company_code}</span>}
        </span>
      ),
    },
    {
      key: 'contract_type',
      header: 'Loại HĐ',
      width: 190,
      cell: (t) => labelOf(LABOR_CONTRACT_TYPE, String(t.contract_type)) || '—',
    },
    {
      key: 'file',
      header: 'Tệp gốc',
      width: 240,
      cell: (t) => (
        <span className="truncate" title={t.original_filename}>
          {t.original_filename || '—'}
          {t.file_size > 0 && (
            <span className="ml-1 text-muted-foreground">({formatFileSize(t.file_size)})</span>
          )}
        </span>
      ),
    },
    {
      key: 'contract_count',
      header: 'Số HĐ đã dùng',
      width: 130,
      align: 'right',
      cell: (t) => t.contract_count,
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      cell: (t) =>
        t.is_active ? <Badge variant="secondary">Đang dùng</Badge> : <Badge variant="outline">Ngừng</Badge>,
    },
    {
      //  Backend chỉ trả ngày tạo + người tạo (không có `updated_at`).
      key: 'created_at',
      header: 'Ngày tạo',
      width: 200,
      cell: (t) => (
        <span className="truncate">
          {formatDateTime(t.created_at)}
          {t.created_by_name && <span className="ml-1 text-muted-foreground">· {t.created_by_name}</span>}
        </span>
      ),
    },
  ]

  //  «Tải tệp» luôn có vì cả trang đã đòi `read`, nên cột Thao tác luôn dựng.
  columns.push({
      key: 'actions',
      header: 'Thao tác',
      width: 240,
      hideable: false,
      cell: (t) => (
        //  Chặn nổi bọt: bấm nút không được kích `onRowClick` (nếu sau này gắn).
        <div className="flex items-center gap-0.5" onClick={(e) => e.stopPropagation()}>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-8"
            title="Tải tệp mẫu"
            aria-label={`Tải tệp mẫu ${t.name}`}
            onClick={() => actions.onDownload(t)}
          >
            <Download className="size-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-8"
            title={actions.canWrite ? 'Soạn nội dung' : 'Xem nội dung'}
            aria-label={`${actions.canWrite ? 'Soạn' : 'Xem'} nội dung mẫu ${t.name}`}
            onClick={() => actions.onEditContent(t)}
          >
            <FilePenLine className="size-4" />
          </Button>
          {actions.canWrite && (
            <>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-8"
                title="Sửa thông tin"
                aria-label={`Sửa thông tin mẫu ${t.name}`}
                onClick={() => actions.onEditInfo(t)}
              >
                <Pencil className="size-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-8"
                title="Thay tệp mẫu"
                aria-label={`Thay tệp mẫu ${t.name}`}
                onClick={() => actions.onReplaceFile(t)}
              >
                <Replace className="size-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-8"
                title={t.is_active ? 'Ngừng dùng' : 'Bật dùng'}
                aria-label={`${t.is_active ? 'Ngừng dùng' : 'Bật dùng'} mẫu ${t.name}`}
                onClick={() => actions.onToggleActive(t)}
              >
                <Power className="size-4" />
              </Button>
            </>
          )}
          {actions.canDelete && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-8 text-destructive hover:text-destructive"
              title="Xóa mẫu"
              aria-label={`Xóa mẫu ${t.name}`}
              onClick={() => actions.onDelete(t)}
            >
              <Trash2 className="size-4" />
            </Button>
          )}
        </div>
      ),
  })
  return columns
}
