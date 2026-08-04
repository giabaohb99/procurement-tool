import { Link, useOutletContext } from 'react-router-dom'
import { Eye, FilePlus2, FolderPlus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import type { AdminOutletContext } from '@/layouts/admin-layout'
import { countDescendants } from '@/lib/help-tree'

// Trang chủ khu quản trị — tổng quan số liệu + hướng dẫn thao tác.

export default function AdminHome() {
  const { tree } = useOutletContext<AdminOutletContext>()
  const total = tree.reduce((sum, n) => sum + 1 + countDescendants(n), 0)

  return (
    <div className="mx-auto max-w-4xl px-8 py-8 pb-16">
      <h1 className="mb-2 text-2xl font-bold text-navy">Quản trị tài liệu hướng dẫn</h1>
      <p className="mb-7 text-muted-foreground">
        Thêm, sửa, xóa bài viết và ảnh hướng dẫn từng bước. Thay đổi hiển thị ngay ở trang người dùng.
      </p>

      <div className="grid grid-cols-2 gap-4">
        <Stat value={tree.length} label="Mục gốc" />
        <Stat value={total} label="Tổng bài viết" />
      </div>

      <h3 className="mb-3 mt-9 text-lg font-semibold text-navy">Thao tác cơ bản</h3>
      <ul className="mb-7 list-disc space-y-2 pl-6 leading-relaxed">
        <li>
          <strong>Thêm mục gốc:</strong> bấm <FolderPlus className="inline size-4 align-text-bottom" />{' '}
          ở góc trên bên trái — mục gốc sẽ thành 1 thẻ danh mục ở trang chủ người dùng.
        </li>
        <li>
          <strong>Thêm bài viết con:</strong> mở 1 bài rồi bấm{' '}
          <FilePlus2 className="inline size-4 align-text-bottom" /> để tạo bài nằm bên trong bài đang mở.
        </li>
        <li>
          <strong>Soạn nội dung:</strong> mở bài viết → <em>Sửa bài viết</em>. Ảnh chèn trong trình soạn
          thảo được tải lên storage (không nhúng base64).
        </li>
        <li>
          <strong>Ảnh từng bước:</strong> ở chế độ sửa, cuộn xuống mục <em>Quản lý slide hướng dẫn</em>.
        </li>
        <li><strong>Xóa:</strong> phải xóa hết bài con trước khi xóa thư mục cha.</li>
      </ul>

      {tree.length === 0 ? (
        <Card className="items-center gap-1.5 border-dashed py-12 text-center">
          <FolderPlus className="mb-1.5 size-9 text-muted-foreground" />
          <strong className="text-navy">Chưa có tài liệu nào</strong>
          <span className="text-sm text-muted-foreground">
            Bấm "Thêm mục gốc" ở góc trên bên trái để tạo bài viết đầu tiên.
          </span>
        </Card>
      ) : (
        <Button variant="outline" asChild>
          <Link to="/"><Eye /> Xem trang người dùng</Link>
        </Button>
      )}
    </div>
  )
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <Card className="bg-muted/50 py-5">
      <CardContent className="px-5">
        <div className="text-3xl font-bold leading-tight text-primary">{value}</div>
        <div className="text-sm text-muted-foreground">{label}</div>
      </CardContent>
    </Card>
  )
}
