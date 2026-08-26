import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { useIssueCodes, useSaveIssueCode } from '../hooks/use-issue-codes'
import type { IssueCodeGroups, IssueCodeRow } from '../types/issue-code'
import { IssueCodeRowEditor } from './issue-code-row-editor'

interface IssueCodeDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

/** Bốn thẻ của mẫu số hiệu, cộng mã riêng theo pháp nhân. Nhãn nói thẳng thẻ nào. */
const NHOM: { key: keyof IssueCodeGroups; tab: string; title: string; mo_ta: string }[] = [
  {
    key: 'companies',
    tab: '{PhapNhan}',
    title: 'Mã pháp nhân',
    mo_ta: 'Đoạn cuối của số hiệu — «…-DEGO». Chỉ chữ không dấu và số.',
  },
  {
    key: 'departments',
    tab: '{PhongBan}',
    title: 'Mã phòng ban',
    mo_ta:
      'Đoạn giữa — «…-NSHC-…». Bỏ trống thì số hiệu không có đoạn này. Đơn vị kinh doanh và ban dự án không vào số hiệu (A05).',
  },
  {
    key: 'department_companies',
    tab: 'Mã riêng',
    title: 'Mã riêng của phòng tại từng pháp nhân',
    mo_ta:
      'Ghi đè mã phòng khi phòng đó dùng chung ở nhiều nơi — phòng Kế toán ở DEGO là KT, ở SAM là KTSAM. Bỏ trống = dùng mã phòng chung.',
  },
  {
    key: 'doc_types',
    tab: '{LoaiVB}',
    title: 'Mã loại văn bản',
    mo_ta:
      'Đoạn đầu của phần đuôi — «…/TB-…». Bắt buộc và không trùng nhau: mã này nằm trong khóa bộ đếm.',
  },
  {
    key: 'books',
    tab: '{SoVB}',
    title: 'Mã sổ văn bản',
    mo_ta: 'Chỉ dùng khi mẫu có thẻ {SoVB}. Bỏ trống thì lấy mã sổ.',
  },
]

/**
 * SỬA MÃ ĐƯA VÀO SỐ HIỆU ngay tại trang Quy tắc đánh số (CR-118).
 *
 * Người khai quy tắc đứng đúng chỗ nhìn ra "số hiệu ra hình thù gì", nhưng mã
 * của từng phần lại nằm ở bốn màn thuộc ba phân hệ — và ba trong bốn màn đó họ
 * có thể không có quyền vào. Hộp thoại này gom lại, gác bằng chính quyền đang
 * mở trang này.
 *
 * Chia tab theo **thẻ trong mẫu** chứ không theo tên bảng: người dùng vừa gõ
 * `{PhongBan}` vào mẫu xong, thứ họ đi tìm là "cái {PhongBan} đó lấy mã ở đâu".
 */
export function IssueCodeDialog({ open, onOpenChange }: IssueCodeDialogProps) {
  const [tab, setTab] = useState<keyof IssueCodeGroups>('companies')
  const [keyword, setKeyword] = useState('')
  //  Chỉ nạp khi hộp thoại mở — 60+ dòng gom từ năm bảng.
  const { data, isLoading } = useIssueCodes(open)
  const save = useSaveIssueCode()

  const rows = useMemo(() => {
    const all: IssueCodeRow[] = data?.[tab] ?? []
    const can = keyword.trim().toLowerCase()
    if (!can) return all
    return all.filter((row) =>
      [row.name, row.code, row.issue_code].some((o) => (o ?? '').toLowerCase().includes(can)),
    )
  }, [data, tab, keyword])

  const nhom = NHOM.find((item) => item.key === tab)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[85vh] flex-col sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Mã đưa vào số hiệu</DialogTitle>
          <DialogDescription>
            Sửa ngay tại đây, khỏi đi sang Nhân sự hay Thiết lập văn bản. Mã mới áp cho
            số cấp từ nay về sau; số đã cấp giữ nguyên chuỗi cũ.
          </DialogDescription>
        </DialogHeader>

        <Tabs
          value={tab}
          onValueChange={(next) => {
            setTab(next as keyof IssueCodeGroups)
            //  Từ khóa của tab cũ gần như không bao giờ khớp tab mới — giữ lại
            //  là người dùng đổi tab xong thấy bảng rỗng và tưởng chưa có gì.
            setKeyword('')
          }}
          className="flex min-h-0 flex-1 flex-col"
        >
          <TabsList className="self-start">
            {NHOM.map((item) => (
              <TabsTrigger key={item.key} value={item.key} className="font-mono text-xs">
                {item.tab}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value={tab} className="mt-3 flex min-h-0 flex-1 flex-col gap-3">
            <div>
              <p className="text-sm font-medium">{nhom?.title}</p>
              <p className="text-xs text-muted-foreground">{nhom?.mo_ta}</p>
            </div>

            <div className="relative w-full max-w-xs">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Tìm theo tên hoặc mã…"
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
              />
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto pr-1">
              {isLoading ? (
                <p className="py-8 text-center text-sm text-muted-foreground">Đang tải…</p>
              ) : rows.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  Không có dòng nào khớp.
                </p>
              ) : (
                rows.map((row) => (
                  <IssueCodeRowEditor
                    //  Khóa gồm cả pháp nhân: mã riêng có nhiều dòng cùng
                    //  `department_id`, khác nhau ở pháp nhân.
                    key={`${row.kind}:${row.id}:${row.company_id ?? 0}`}
                    row={row}
                    pending={save.isPending}
                    onSave={(issueCode, force) =>
                      save.mutate({
                        kind: row.kind,
                        id: row.id,
                        company_id: row.company_id,
                        issue_code: issueCode,
                        force,
                      })
                    }
                  />
                ))
              )}
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
