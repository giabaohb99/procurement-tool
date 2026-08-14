import { GitBranch, Lock, Plus } from 'lucide-react'
import { useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { useDocumentVersions } from '../hooks/use-document-versions'
import {
  CHANGE_KIND_LABELS,
  type DocumentRecord,
  type DocumentVersion,
} from '../types/document-record'
import { DocumentVersionDialog } from './document-version-dialog'

interface DocumentVersionTabProps {
  document: DocumentRecord
  /** Đang xem bản nào — bấm một dòng thì trang soạn thảo mở đúng bản đó. */
  activeVersionId: number | null
  onSelect: (version: DocumentVersion) => void
  /** Không có quyền sửa thì không mở được phiên bản mới. */
  canWrite: boolean
}

/**
 * TAB PHIÊN BẢN.
 *
 * Bản mới nhất lên đầu. Bản đã duyệt mang khóa và **mở ra là chỉ đọc** — sửa
 * một bản đã duyệt không phải là sửa dòng đó mà là mở một dòng mới (C04, C07).
 *
 * Bản cũ **không xóa, không ẩn**: người đang cầm giấy tờ theo bản 1.0 vẫn phải
 * tra ra nó (C18).
 */
export function DocumentVersionTab({
  document,
  activeVersionId,
  onSelect,
  canWrite,
}: DocumentVersionTabProps) {
  const { data: versions = [] } = useDocumentVersions(document.id)
  const [dialogOpen, setDialogOpen] = useState(false)

  //  Chỉ mở được bản mới khi bản đang dùng đã được duyệt và không còn bản nháp
  //  nào đang mở — cùng điều kiện backend kiểm, nói trước cho đỡ bấm vào rồi
  //  nhận lỗi.
  const hasOpenDraft = versions.some((version) => !version.is_locked)
  const canOpenNew = canWrite && !hasOpenDraft && versions.some((v) => v.is_current && v.is_locked)

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <GitBranch className="size-4 text-muted-foreground" />
          Phiên bản ({versions.length})
        </CardTitle>
        {canOpenNew && (
          <Button type="button" variant="outline" size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="size-4" />
            Mở phiên bản mới
          </Button>
        )}
      </CardHeader>

      <CardContent>
        {hasOpenDraft && (
          <p className="mb-3 rounded-md bg-muted px-3 py-2 text-sm text-muted-foreground">
            Đang có bản nháp mở — chốt xong bản đó rồi mới mở được phiên bản tiếp theo.
          </p>
        )}

        <ul className="divide-y">
          {versions.map((version) => (
            <li key={version.id}>
              <button
                type="button"
                onClick={() => onSelect(version)}
                className={cn(
                  'flex w-full items-start gap-3 py-3 text-left transition-colors hover:bg-muted/50',
                  activeVersionId === version.id && 'bg-muted/60',
                )}
              >
                <span className="w-14 shrink-0 font-medium tabular-nums">
                  {version.version_no}
                </span>

                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <Badge variant={version.is_current ? 'default' : 'outline'}>
                      {version.status_label}
                    </Badge>
                    {version.is_current && (
                      <Badge variant="secondary">Bản đang dùng</Badge>
                    )}
                    {version.is_locked && (
                      <Lock className="size-3.5 text-muted-foreground" />
                    )}
                    {version.change_kind > 0 && (
                      <span className="text-xs text-muted-foreground">
                        {CHANGE_KIND_LABELS[version.change_kind]}
                      </span>
                    )}
                  </span>

                  {version.change_summary && (
                    <span className="mt-1 block truncate text-sm">
                      {version.change_summary}
                    </span>
                  )}

                  <span className="mt-1 block text-xs text-muted-foreground">
                    {version.effective_from && `Hiệu lực từ ${formatDate(version.effective_from)} · `}
                    {version.approved_at
                      ? `Duyệt ${formatDateTime(version.approved_at)}${
                          version.approved_by_name ? ` bởi ${version.approved_by_name}` : ''
                        }`
                      : `Nháp của ${version.created_by_name || 'không rõ'}`}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </CardContent>

      <DocumentVersionDialog
        documentId={document.id}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
      />
    </Card>
  )
}
