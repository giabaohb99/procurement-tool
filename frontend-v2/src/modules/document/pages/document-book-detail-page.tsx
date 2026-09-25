import { Save } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'
import { BookCounterCard } from '../components/book-counter-card'
import { BookDocumentsTab } from '../components/book-documents-tab'
import { DetailPageShell } from '../components/detail-page-shell'
import { DocumentBookForm } from '../components/document-book-form'
import {
  useDeleteDocumentBook,
  useDocumentBook,
  useSaveDocumentBook,
} from '../hooks/use-document-books'
import { BOOK_KIND_LABELS } from '../types/document-book'

const FORM_ID = 'document-book-form'

/**
 * Trang MỞ SỔ / SỬA SỔ.
 *
 * Sổ đã tồn tại thì có HAI tab: «Thông tin sổ» (form khai báo + bộ đếm đang
 * tới đâu) và «Văn bản trong sổ» (duoc-CR-474, 23/09/2026). Trang thêm mới chỉ có
 * form: sổ chưa tồn tại thì chưa có số nào để đếm và chưa có văn bản nào để
 * liệt kê, nên không có gì để tách tab.
 */
export function DocumentBookDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()

  const bookId = Number(id)
  const isCreating = !Number.isFinite(bookId)

  const { data: book, isLoading } = useDocumentBook(isCreating ? undefined : bookId)
  const save = useSaveDocumentBook()
  const remove = useDeleteDocumentBook()

  const [year, setYear] = useState(new Date().getFullYear())
  const [tab, setTab] = useUrlParamState('tab', 'info')

  const backTo = appRoutes.document.books

  return (
    <DetailPageShell
      title={isCreating ? 'Mở sổ văn bản' : (book?.name ?? '')}
      //  ⚠️ Dòng mô tả ẨN ở khổ hẹp, vì hai lẽ đi cùng nhau. Một: ở trang đã có
      //  sổ, nó chỉ nhắc lại *loại sổ · mã · pháp nhân* — đúng ba ô nằm ngay
      //  dưới trong biểu mẫu, tức đọc hai lần cùng một thứ. Hai: dải tiêu đề nay
      //  GHIM theo cuộn (xem `stickyHeader`), nên mỗi dòng ở đây là chỗ đứng yên
      //  vĩnh viễn — riêng câu này rớt **hai hàng ≈ 48px** trên màn 796px.
      //  Trang thêm mới thì giữ: ở đó chưa có ô nào điền nên câu dẫn còn việc.
      description={
        isCreating ? (
          'Mỗi sổ có bộ đếm số riêng — khai xong là dùng được ngay.'
        ) : (
          <span className="max-md:hidden">
            {`${book ? BOOK_KIND_LABELS[book.kind] : ''} · mã ${book?.code} · ${book?.company_name}`}
          </span>
        )
      }
      //  Form dài (đo ở 393px: **1812px**, gấp hơn hai màn hình) mà nút Lưu
      //  nằm trên đầu — không ghim thì sửa một ô ở giữa xong phải cuộn ngược lên
      //  tận đỉnh mới lưu được, rồi cuộn xuống lại để sửa ô tiếp theo. Cùng lý do
      //  với tab Thông tin của chi tiết Văn bản.
      stickyHeader
      formId={FORM_ID}
      isCreating={isCreating}
      backTo={backTo}
      isMissing={!isCreating && !isLoading && !book}
      missingTitle="Không tìm thấy sổ"
      audit={book ? { entity: 'document_book', id: book.id } : undefined}
      deleteConfirmDescription="Chỉ xóa được sổ chưa cấp số nào. Sổ đã dùng thì chuyển sang Ngừng dùng."
      onDelete={
        book ? () => remove.mutate(book.id, { onSuccess: () => navigate(backTo) }) : undefined
      }
      //  ⚠️ Trang thêm mới KHÔNG có tab (`actions` mặc định của `DetailPageShell`
      //  ăn khớp: một `<form>` duy nhất, luôn ở trong DOM). Trang đã có sổ thì
      //  tách hai tab bằng Radix `Tabs`, mà Radix HỦY MOUNT `TabsContent` đang
      //  ẩn — nút Lưu mặc định trỏ `form={FORM_ID}` vẫn đứng ở đầu trang bất kể
      //  tab nào đang mở, nên đứng ở tab «Văn bản trong sổ» thì `<form>` đã biến
      //  khỏi DOM và bấm Lưu không làm gì cả, không báo lỗi (cùng bẫy đã ghi ở
      //  `document-detail-page.tsx`). Tự dựng `actions`, chỉ bày nút Lưu khi
      //  đang đứng ở tab «info».
      actions={
        isCreating ? undefined : (
          <>
            <Button variant="outline" onClick={() => navigate(backTo)} className="max-md:hidden">
              Hủy
            </Button>
            {tab === 'info' && (
              <Button type="submit" form={FORM_ID} className="max-md:flex-1">
                <Save className="size-4" />
                Lưu
              </Button>
            )}
          </>
        )
      }
    >
      {isCreating ? (
        <DocumentBookForm
          formId={FORM_ID}
          book={book}
          onSubmit={(values) =>
            save.mutate(
              { id: book?.id, values },
              {
                onSuccess: (saved) => {
                  navigate(appRoutes.document.bookDetail(saved.id), { replace: true })
                },
              },
            )
          }
        />
      ) : (
        <Tabs value={tab} onValueChange={setTab}>
          <ScrollableTabsList value={tab}>
            <TabsTrigger value="info" className={TAB_TRIGGER_UNDERLINE}>
              Thông tin sổ
            </TabsTrigger>
            <TabsTrigger value="documents" className={TAB_TRIGGER_UNDERLINE}>
              Văn bản trong sổ
            </TabsTrigger>
          </ScrollableTabsList>

          <TabsContent value="info" className="mt-4 space-y-4">
            <DocumentBookForm
              formId={FORM_ID}
              book={book}
              onSubmit={(values) => save.mutate({ id: book?.id, values })}
            />

            {book && <BookCounterCard bookId={book.id} year={year} onYearChange={setYear} />}
          </TabsContent>

          <TabsContent value="documents" className="mt-4">
            {book && <BookDocumentsTab bookId={book.id} year={year} onYearChange={setYear} />}
          </TabsContent>
        </Tabs>
      )}
    </DetailPageShell>
  )
}
