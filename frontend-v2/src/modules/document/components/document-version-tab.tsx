import { GitBranch, Plus } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/shared/ui/card'
import { HelpHint } from '@/shared/ui/help-hint'
import { useDocumentVersions } from '../hooks/use-document-versions'
import type { DocumentRecord, DocumentVersion } from '../types/document-record'
import { DocumentDraftHolderNotice } from './document-draft-holder-notice'
import { DocumentVersionDialog } from './document-version-dialog'
import { DocumentVersionRow } from './document-version-row'

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
  const openDraft = versions.find((version) => !version.is_locked)
  const canOpenNew = canWrite && !openDraft && versions.some((v) => v.is_current && v.is_locked)

  //  Nút bị ẩn thì phải nói VÌ SAO ẩn. Trước đây nó biến mất không lời nào, nên
  //  người có quyền sửa mở tab ra chỉ thấy một danh sách trơ và không đoán được
  //  mở bản mới ở đâu.
  const blockedReason = !canWrite
    ? null
    : openDraft
      ? 'Đang có bản nháp mở — chốt xong bản đó rồi mới mở tiếp được.'
      : !versions.some((v) => v.is_current && v.is_locked)
        ? 'Chỉ mở phiên bản mới từ một bản ĐÃ DUYỆT. Bản đang dùng chưa duyệt xong.'
        : null

  return (
    <Card>
      {/*  `flex` phải khai TƯỜNG MINH: `CardHeader` của shadcn mặc định là
           `grid`, mà `flex-row` một mình không đè được `display` — thiếu nó thì
           nút «Mở phiên bản mới» rơi xuống hàng dưới và kéo dài hết bề ngang. */}
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="min-w-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <GitBranch className="size-4 text-muted-foreground" />
            Phiên bản ({versions.length})
          </CardTitle>
          <CardDescription className="mt-0.5">
            Mới nhất ở trên. Bản cũ không xóa — người còn cầm giấy tờ theo bản cũ vẫn phải
            tra ra được.
          </CardDescription>
        </div>

        {canOpenNew ? (
          <Button type="button" variant="outline" size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="size-4" />
            Mở phiên bản mới
          </Button>
        ) : (
          blockedReason && (
            <span className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground">
              Chưa mở được phiên bản mới
              <HelpHint label="Vì sao chưa mở được phiên bản mới">{blockedReason}</HelpHint>
            </span>
          )
        )}
      </CardHeader>

      <CardContent>
        {openDraft && (
          <DocumentDraftHolderNotice
            draft={openDraft}
            onOpenDraft={() => onSelect(openDraft)}
            className="mb-3"
          />
        )}

        <ul>
          {versions.map((version, index) => (
            <DocumentVersionRow
              key={version.id}
              version={version}
              dangXem={activeVersionId === version.id}
              onSelect={() => onSelect(version)}
              cuoiDanhSach={index === versions.length - 1}
            />
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
