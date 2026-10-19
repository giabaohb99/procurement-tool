import { ArrowLeft } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import {
  DOCUMENT_TYPE_FLAGS,
  ID_SCHEME_LABELS,
  documentCodeSample,
  type DocumentType,
} from '../types/document-type'

interface DocumentSystemTypeViewProps {
  documentType: DocumentType
  onBack: () => void
}

/**
 * Loại văn bản do HỆ THỐNG giữ (bản lưu trữ hợp đồng lao động, mã HDLD — duoc-CR-629): chỉ XEM.
 *
 * Backend khóa mọi cờ của loại này (đổi cờ hay xóa đều 400) vì mở `is_personal`, bật duyệt / cấp số hoặc tắt
 * loại là mở đường rò dữ liệu lương hoặc làm cầu đồng bộ từ Nhân sự chết im lặng. Trang này không dựng form
 * để khỏi mời người dùng sửa một thứ chắc chắn bị từ chối.
 */
export function DocumentSystemTypeView({ documentType, onBack }: DocumentSystemTypeViewProps) {
  const flags = DOCUMENT_TYPE_FLAGS.filter((flag) => documentType[flag.key])
  return (
    <PageContainer className="space-y-4">
      <div className="flex items-center gap-3">
        <Button type="button" variant="outline" size="sm" onClick={onBack}>
          <ArrowLeft className="size-4" />
          Về danh sách
        </Button>
        <h1 className="text-lg font-semibold text-navy">{documentType.name}</h1>
        <Badge variant="secondary">Loại hệ thống</Badge>
      </div>
      <p className="text-sm text-muted-foreground">
        Loại này do phân hệ Nhân sự tự sinh làm bản lưu trữ hợp đồng lao động nên không sửa hay xóa được.
      </p>
      <dl className="grid max-w-xl grid-cols-[10rem_1fr] gap-x-4 gap-y-2 text-sm">
        <dt className="text-muted-foreground">Mã loại</dt>
        <dd className="font-medium">{documentType.code}</dd>
        <dt className="text-muted-foreground">Số hiệu</dt>
        <dd>
          {documentCodeSample(documentType.code, documentType.id_scheme)} ·{' '}
          {ID_SCHEME_LABELS[documentType.id_scheme]}
        </dd>
        <dt className="text-muted-foreground">Quy tắc đang bật</dt>
        <dd className="flex flex-wrap gap-1">
          {flags.length === 0
            ? '—'
            : flags.map((flag) => (
                <Badge key={flag.key} variant="outline" className="font-normal">
                  {flag.label}
                </Badge>
              ))}
        </dd>
        <dt className="text-muted-foreground">Trạng thái</dt>
        <dd>{documentType.is_active ? 'Đang dùng' : 'Ngừng'}</dd>
      </dl>
    </PageContainer>
  )
}
