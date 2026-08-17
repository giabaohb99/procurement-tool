import { AlertTriangle, Link2, Lock, X } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import type { DocumentLink } from '../types/document-link'

interface DocumentLinkRowProps {
  link: DocumentLink
  onDelete?: (linkId: number) => void
}

/**
 * Một dòng quan hệ.
 *
 * Nút gỡ chỉ hiện với quan hệ **đi ra** và **không phải hệ thống tạo**:
 *  - chiều đi vào là dữ liệu của văn bản bên kia, gỡ từ đây là sửa hồ sơ người khác;
 *  - dòng `is_system` (trích từ, clone) mà gỡ được thì văn bản con thành mồ côi.
 */
export function DocumentLinkRow({ link, onDelete }: DocumentLinkRowProps) {
  const other = link.document
  const goDuoc = onDelete && link.direction === 'outgoing' && !link.is_system

  return (
    <li className="flex items-start gap-3 py-3 first:pt-0">
      <Link2 className="mt-0.5 size-4 shrink-0 text-muted-foreground" />

      <div className="min-w-0 flex-1">
        <p className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-muted-foreground">{link.relation_label}</span>
          {other ? (
            <Link
              to={appRoutes.document.documentDetail(other.id)}
              className="font-medium hover:underline"
            >
              {other.display_code ? `${other.display_code} · ` : ''}
              {other.title}
            </Link>
          ) : (
            <span className="italic text-muted-foreground">văn bản đã bị xóa</span>
          )}
          {link.is_system && (
            <Lock className="size-3.5 text-muted-foreground" aria-label="Hệ thống tạo" />
          )}
        </p>

        <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          {other && (
            <>
              <Badge variant="outline">{other.status_label}</Badge>
              {other.version_no && <span>Bản {other.version_no}</span>}
            </>
          )}
          {link.note && <span>· {link.note}</span>}
        </p>

        {/*  Bản trích đang bám theo một phiên bản CŨ của gốc — nó có thể đang
             nói sai. Đây là hệ quả nhìn thấy được của E11 (a). */}
        {link.is_outdated && (
          <p className="mt-1 flex items-center gap-1.5 text-xs text-amber-800">
            <AlertTriangle className="size-3.5 text-amber-700" />
            Bản gốc đã lên phiên bản mới sau lần trích này — cần rà lại.
          </p>
        )}
      </div>

      {goDuoc && (
        <ConfirmIconButton
          icon={X}
          title="Gỡ quan hệ"
          destructive
          confirmTitle="Gỡ quan hệ này?"
          confirmDescription="Chỉ gỡ liên kết, hai văn bản vẫn còn nguyên."
          confirmLabel="Gỡ"
          onConfirm={() => onDelete(link.id)}
        />
      )}
    </li>
  )
}
