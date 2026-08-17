import { AlertTriangle, Target } from 'lucide-react'

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
 * Băng cảnh báo khi chưa khai dòng nào là phần **quan trọng nhất** của thẻ này.
 * Quy tắc của hệ là *không khai gì = không ai thuộc phạm vi*, ngược hẳn trực
 * giác — người dùng mặc định tưởng "chưa giới hạn nghĩa là mọi người". Không nói
 * ra thì họ ban hành một văn bản không tới ai và không hiểu vì sao im lặng.
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
        {data?.applies_to_nobody && (
          <div className="flex gap-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3">
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <div className="text-sm text-amber-900">
              <p className="font-medium">Chưa khai phạm vi — văn bản này không tới ai.</p>
              <p className="text-amber-800">
                Để trống KHÔNG có nghĩa là áp cho mọi người. Khai ít nhất một dòng
                bao gồm thì văn bản mới hiện trong mục «Văn bản áp dụng cho tôi»
                của người thuộc phạm vi.
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
