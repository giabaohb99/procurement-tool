import { AlertTriangle, Building2, Copy } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { formatDate } from '@/shared/utils/format-date'
import { useDocumentClones } from '../hooks/use-document-clones'
import { CLONE_STATUS, type DocumentCloneRow } from '../types/document-clone'
import { DocumentCloneDialog } from './document-clone-dialog'

interface DocumentCloneCardProps {
  documentId: number
  /** Chỉ clone được văn bản đã ban hành. */
  isIssued: boolean
  canCreate: boolean
}

/**
 * BẢNG THEO DÕI CÁC BẢN CLONE (F10) — điều kiện thứ tư trong bốn điều kiện bắt
 * buộc để clone không thành thảm họa.
 *
 * Màn hình này phải trả lời được đúng bốn câu: **ai đã ban hành · ai còn nháp ·
 * ai chưa đụng tới · ai đang lệch bản**. Thiếu nó thì đúng như cảnh báo trong
 * quyết định cũ — sau hai năm có 12 bản khác nhau và không ai biết bản nào đúng.
 */
export function DocumentCloneCard({
  documentId,
  isIssued,
  canCreate,
}: DocumentCloneCardProps) {
  const { data } = useDocumentClones(documentId)
  const [cloneOpen, setCloneOpen] = useState(false)

  const items = data?.items ?? []
  const pending = data?.pending_companies ?? []
  const lechBan = items.filter((row) => row.is_outdated).length

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Copy className="size-4 text-muted-foreground" />
          Bản clone ở pháp nhân con ({items.length})
        </CardTitle>
        {canCreate && isIssued && pending.length > 0 && (
          <Button type="button" variant="outline" size="sm" onClick={() => setCloneOpen(true)}>
            <Copy className="size-4" />
            Clone xuống pháp nhân
          </Button>
        )}
      </CardHeader>

      <CardContent className="space-y-3">
        {/*  Câu "ai đang lệch bản" là câu khó nhất và nguy hiểm nhất — đưa lên
             đầu thay vì để người dùng tự đếm trong bảng. */}
        {lechBan > 0 && (
          <p className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <span>
              <b>{lechBan}</b> bản clone đang bám phiên bản cũ của văn bản này. Người
              phụ trách đã được báo, nhưng bản của họ vẫn đang nói theo nội dung cũ.
            </span>
          </p>
        )}

        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {isIssued
              ? 'Chưa clone xuống pháp nhân nào.'
              : 'Clone được sau khi văn bản đã ban hành.'}
          </p>
        ) : (
          <ul className="divide-y">
            {items.map((row) => (
              <CloneRow key={row.document_id} row={row} />
            ))}
          </ul>
        )}

        {items.length > 0 && pending.length > 0 && (
          <p className="text-sm text-muted-foreground">
            <Building2 className="mr-1 inline size-3.5" />
            Chưa đụng tới: {pending.map((item) => item.company_name).join(', ')}
          </p>
        )}
      </CardContent>

      <DocumentCloneDialog
        documentId={documentId}
        open={cloneOpen}
        onOpenChange={setCloneOpen}
        companies={pending}
      />
    </Card>
  )
}

function CloneRow({ row }: { row: DocumentCloneRow }) {
  return (
    <li className="flex flex-wrap items-center gap-2 py-2 text-sm first:pt-0">
      <span className="min-w-40 font-medium">{row.company_name}</span>

      <Link
        to={appRoutes.document.documentDetail(row.document_id)}
        className="text-muted-foreground hover:underline"
      >
        {row.display_code || 'chưa cấp số'}
      </Link>

      <Badge variant={row.clone_status === CLONE_STATUS.issued ? 'default' : 'outline'}>
        {row.clone_status_label}
      </Badge>

      {row.version_no && (
        <span className="text-xs text-muted-foreground">bản {row.version_no}</span>
      )}

      {row.is_outdated && (
        <span className="flex items-center gap-1 text-xs text-amber-800">
          <AlertTriangle className="size-3.5 text-amber-700" />
          lệch bản
        </span>
      )}

      {row.assignee_name && (
        <span className="text-xs text-muted-foreground">· {row.assignee_name}</span>
      )}

      {row.due_date && (
        <span className="text-xs text-muted-foreground">
          · hạn {formatDate(row.due_date)}
        </span>
      )}
    </li>
  )
}
