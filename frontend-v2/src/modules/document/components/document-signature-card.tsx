import { AlertTriangle, PenLine, ShieldCheck } from 'lucide-react'
import { useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { formatDateTime } from '@/shared/utils/format-date'
import { useDocumentSignatures } from '../hooks/use-document-signatures'
import { SIGN_KIND, type DocumentSignature } from '../types/document-signature'
import { DocumentSignDialog } from './document-sign-dialog'

interface DocumentSignatureCardProps {
  documentId: number
  /** Phiên bản đang mở — ký vào đúng bản này. */
  versionId: number | null
  /** Chỉ ký được bản ĐÃ KHÓA; bản nháp còn sửa được. */
  isLocked: boolean
  canApprove: boolean
}

/**
 * CHỮ KÝ (J02, J03).
 *
 * Câu **giá trị pháp lý** hiện ngay cạnh từng chữ ký, không giấu trong tài liệu
 * hướng dẫn — đó là yêu cầu tường minh của J03. Ký điện tử nội bộ chỉ có giá trị
 * trong tập đoàn; nhầm nó với ký số là gửi ra ngoài một văn bản tưởng có giá trị
 * pháp lý mà thật ra không.
 */
export function DocumentSignatureCard({
  documentId,
  versionId,
  isLocked,
  canApprove,
}: DocumentSignatureCardProps) {
  const { data: signatures = [] } = useDocumentSignatures(documentId)
  const [signOpen, setSignOpen] = useState(false)

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <PenLine className="size-4 text-muted-foreground" />
          Chữ ký ({signatures.length})
        </CardTitle>
        {canApprove && isLocked && versionId && (
          <Button type="button" variant="outline" size="sm" onClick={() => setSignOpen(true)}>
            <PenLine className="size-4" />
            Ký văn bản
          </Button>
        )}
      </CardHeader>

      <CardContent>
        {signatures.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {isLocked
              ? 'Chưa có chữ ký nào.'
              : 'Ký được sau khi phiên bản được duyệt và khóa lại.'}
          </p>
        ) : (
          <ul className="divide-y">
            {signatures.map((signature) => (
              <SignatureRow key={signature.id} signature={signature} />
            ))}
          </ul>
        )}
      </CardContent>

      {versionId && (
        <DocumentSignDialog
          documentId={documentId}
          versionId={versionId}
          open={signOpen}
          onOpenChange={setSignOpen}
        />
      )}
    </Card>
  )
}

function SignatureRow({ signature }: { signature: DocumentSignature }) {
  const isCertified = signature.sign_kind === SIGN_KIND.certified

  return (
    <li className="py-3 first:pt-0">
      <div className="flex flex-wrap items-center gap-2">
        <ShieldCheck
          className={
            isCertified ? 'size-4 shrink-0 text-primary' : 'size-4 shrink-0 text-muted-foreground'
          }
        />
        <span className="font-medium">{signature.signer_name || 'Không rõ người ký'}</span>
        <Badge variant={isCertified ? 'default' : 'secondary'}>
          {signature.sign_kind_label}
        </Badge>
        <span className="text-xs text-muted-foreground">
          bản {signature.version_no} · {formatDateTime(signature.signed_at)}
        </span>
      </div>

      {/*  J03 — câu giá trị pháp lý đi kèm CHỮ KÝ, không nằm ở trang trợ giúp. */}
      <p className="mt-1 text-xs text-muted-foreground">{signature.legal_note}</p>

      {signature.cert_serial && (
        <p className="mt-1 text-xs text-muted-foreground">
          Chứng thư {signature.cert_serial}
          {signature.cert_issuer && ` · ${signature.cert_issuer}`}
        </p>
      )}

      <p className="mt-1 font-mono text-xs text-muted-foreground">
        <span title={`SHA-256 nội dung lúc ký: ${signature.content_sha256}`}>
          {signature.content_sha256.slice(0, 12)}
        </span>
        {signature.ip && <span className="font-sans"> · từ {signature.ip}</span>}
      </p>

      {/*  Nội dung đã đổi sau khi ký — đây là chuyện đáng báo động, không phải
           một chi tiết kỹ thuật nhỏ. */}
      {!signature.content_matches && (
        <p className="mt-1 flex items-center gap-1.5 text-xs text-amber-800">
          <AlertTriangle className="size-3.5 text-amber-700" />
          Nội dung phiên bản không còn khớp mã băm lúc ký — chữ ký này không còn
          bảo chứng cho nội dung đang hiển thị.
        </p>
      )}
    </li>
  )
}
