import { AlertTriangle } from 'lucide-react'
import { useMemo } from 'react'

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import {
  useAddDocumentLink,
  useDeleteDocumentLink,
  useDocumentLinkSlots,
  useDocumentLinks,
} from '../hooks/use-document-links'
import { DocumentLinkAddForm } from './document-link-add-form'
import { DocumentLinkRow } from './document-link-row'
import { DocumentTreeCard } from './document-tree-card'

interface DocumentLinkTabProps {
  documentId: number
  /** Không có quyền sửa thì chỉ xem, không khai và không gỡ. */
  canWrite: boolean
}

/**
 * TAB QUAN HỆ (E03–E06).
 *
 * Ba khối, theo đúng thứ tự người dùng cần:
 *  1. còn thiếu gì để gửi duyệt được (E04) — thứ đang CHẶN họ;
 *  2. khai thêm / gỡ quan hệ (E03);
 *  3. cây tài liệu (E06) — nhìn toàn cảnh.
 */
export function DocumentLinkTab({ documentId, canWrite }: DocumentLinkTabProps) {
  const { data } = useDocumentLinks(documentId)
  const { data: slots = [] } = useDocumentLinkSlots(documentId)
  const addLink = useAddDocumentLink(documentId)
  const deleteLink = useDeleteDocumentLink(documentId)

  const outgoing = useMemo(() => data?.outgoing ?? [], [data?.outgoing])
  const incoming = data?.incoming ?? []
  const missing = data?.missing_required ?? []

  //  Đếm theo TỪNG DÒNG QUY TẮC, không theo loại quan hệ: một loại văn bản có
  //  thể có hai dòng cùng quan hệ khác loại đích (Biểu mẫu *thuộc về* Quy trình
  //  và *thuộc về* Quy chế). Đếm gộp thì khai một cái là ô kia cũng tự khóa.
  const countByRule = useMemo(() => {
    const dem: Record<number, number> = {}
    for (const slot of slots) {
      dem[slot.rule_id] = outgoing.filter(
        (link) =>
          link.relation === slot.relation &&
          //  Quy tắc để trống loại đích thì mọi văn bản đều tính.
          (!slot.target_type_id || link.document?.doc_type_id === slot.target_type_id),
      ).length
    }
    return dem
  }, [outgoing, slots])

  return (
    <div className="space-y-4">
      {/*  E04 — nói TRƯỚC còn thiếu gì. Backend vẫn chặn lần nữa lúc gửi duyệt,
           băng này chỉ để người dùng khỏi bấm rồi mới biết. */}
      {missing.length > 0 && (
        <div className="flex gap-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
          <div className="text-sm text-amber-900">
            <p className="font-medium">Chưa gửi duyệt được — còn thiếu quan hệ bắt buộc:</p>
            <ul className="mt-1 list-inside list-disc text-amber-800">
              {missing.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {canWrite && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Khai quan hệ</CardTitle>
          </CardHeader>
          <CardContent>
            <DocumentLinkAddForm
              slots={slots}
              countByRule={countByRule}
              disabled={addLink.isPending}
              onAdd={(relation, targetDocumentId) =>
                addLink.mutate({ relation, target_document_id: targetDocumentId })
              }
            />
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Văn bản này trỏ tới ({outgoing.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {outgoing.length === 0 ? (
            <p className="text-sm text-muted-foreground">Chưa khai quan hệ nào.</p>
          ) : (
            <ul className="divide-y">
              {outgoing.map((link) => (
                <DocumentLinkRow
                  key={link.id}
                  link={link}
                  onDelete={canWrite ? (id) => deleteLink.mutate(id) : undefined}
                />
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {incoming.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Văn bản khác trỏ tới đây ({incoming.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="divide-y">
              {incoming.map((link) => (
                <DocumentLinkRow key={link.id} link={link} />
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <DocumentTreeCard documentId={documentId} />
    </div>
  )
}
