import { Building2, Target } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import {
  useAddDocumentScope,
  useDeleteDocumentScope,
  useDocumentScopes,
} from '../hooks/use-document-scopes'
import { DocumentScopeAddForm } from './document-scope-add-form'
import { DocumentScopeRow } from './document-scope-row'

interface DocumentScopeCardProps {
  documentId: number
  canWrite: boolean
}

/**
 * PHẠM VI ÁP DỤNG (F01–F04) — văn bản này áp cho ai.
 *
 * Chưa khai dòng nào là chuyện BÌNH THƯỜNG: văn bản áp cho toàn bộ pháp nhân ban
 * hành. Băng ở đầu thẻ nói ra điều đó kèm TÊN pháp nhân — không thì người dùng
 * lại đoán, mà hai hướng đoán ("không tới ai" / "cả tập đoàn") đều sai.
 */
export function DocumentScopeCard({ documentId, canWrite }: DocumentScopeCardProps) {
  const { data } = useDocumentScopes(documentId)
  const addScope = useAddDocumentScope(documentId)
  const deleteScope = useDeleteDocumentScope(documentId)

  const items = data?.items ?? []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Target className="size-4 text-muted-foreground" />
          Phạm vi áp dụng ({items.length})
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {data?.default_to_issuer && (
          <div className="flex gap-3 rounded-md border bg-muted/40 px-4 py-3">
            <Building2 className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
            <div className="text-sm">
              <p className="font-medium">
                Chưa khai dòng nào — mặc định áp cho toàn bộ{' '}
                {data.issuer_company_name || 'pháp nhân ban hành'}.
              </p>
              <p className="text-muted-foreground">
                Mọi phòng ban, mọi nhân sự của chính pháp nhân này đều thấy văn bản
                trong mục «Văn bản áp dụng cho tôi». Chỉ khai thêm dòng khi muốn đi
                XA HƠN (pháp nhân khác) hoặc HẸP LẠI (một phòng ban, một người).
              </p>
            </div>
          </div>
        )}

        {items.length > 0 && (
          <ul className="divide-y">
            {items.map((scope) => (
              <DocumentScopeRow
                key={scope.id}
                scope={scope}
                onDelete={canWrite ? (id) => deleteScope.mutate(id) : undefined}
              />
            ))}
          </ul>
        )}

        {canWrite && (
          <div className="border-t pt-4">
            <DocumentScopeAddForm
              disabled={addScope.isPending}
              onAdd={(values) => addScope.mutate(values)}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
