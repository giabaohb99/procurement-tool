import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DocumentCard } from './document-card'
import { DOCUMENT_STATUS, type DocumentRecord } from '../types/document-record'

function doc(overrides: Partial<DocumentRecord> = {}): DocumentRecord {
  return {
    id: 1,
    origin: 1,
    doc_code: null,
    issue_number: '',
    display_code: 'DEGO-QC-001',
    seq_no: 1,
    issue_year: 2026,
    allow_manual_number: false,
    legacy_code: '',
    storage_location: '',
    metadata: null,
    doc_type_id: 3,
    doc_type_name: 'Quy chế / Quy trình',
    doc_type_code: 'QC',
    company_id: 1,
    company_name: 'CÔNG TY TNHH DEGO HOLDING',
    department_id: 2,
    department_name: 'Phòng Kế toán',
    owner_employee_id: 1,
    owner_name: 'Dego Admin',
    drafter_employee_id: 1,
    drafter_name: 'Dego Admin',
    signer_employee_id: 0,
    signer_name: '',
    title: 'Quy chế công tác văn thư, lưu trữ',
    summary: '',
    keywords: '',
    secrecy_level: 2,
    urgency: 1,
    //  Mặc định là NHÁP: `effectiveLabel` chỉ tính lại nhãn theo ngày khi văn
    //  bản «Có hiệu lực», nên trạng thái này giữ bài kiểm khỏi phụ thuộc hôm nay.
    status: DOCUMENT_STATUS.draft,
    status_label: 'Nháp',
    effective_date: null,
    expire_date: null,
    attachment_view_until: null,
    book_id: null,
    book_name: '',
    book_seq_no: null,
    book_year: null,
    book_number_display: '',
    current_version_id: null,
    version_no: '1.0',
    version_count: 1,
    attachment_count: 0,
    needs_review: false,
    needs_review_note: '',
    apply_mode: 1,
    created_at: '2026-09-01T08:00:00',
    ...overrides,
  }
}

describe('DocumentCard', () => {
  /**
   * ⚠️ Bài kiểm quan trọng nhất của tệp này.
   *
   * `DataTableMobileCards` bọc kết quả của `renderCard` trong MỘT `<button>` để
   * cả thẻ bấm được bằng bàn phím lẫn trình đọc màn hình. Nút lồng trong nút là
   * HTML sai — trình duyệt tự gỡ cây DOM ra và trên máy cảm ứng thì hai vùng
   * chạm đè nhau, bấm vào "xem bản riêng" lại mở trang chi tiết.
   *
   * Nên bảng có mũi tên bung và nút sao chép, còn thẻ thì KHÔNG được có nút nào.
   */
  it('dựng không nút nào bên trong — thẻ nằm trong một <button> của khung thẻ', () => {
    const { container } = render(
      <DocumentCard doc={doc({ clone_count: 3 })} awaitingMyApproval showOrigin showReviewFlag />,
    )

    expect(container.querySelectorAll('button')).toHaveLength(0)
  })

  /**
   * Bài học duoc-CR-364: số hiệu đứng đầu thì cả một danh sách nháp in ra mười
   * dòng «Chưa cấp số» giống hệt nhau, còn TÊN — thứ duy nhất nói đây là văn bản
   * gì — bị đẩy xuống. Trên thẻ, tên phải ra trước số hiệu.
   */
  it('đặt tên văn bản TRƯỚC số hiệu, ngược thứ tự cột của bảng', () => {
    render(<DocumentCard doc={doc()} />)

    const text = screen.getByText('Quy chế công tác văn thư, lưu trữ')
    const code = screen.getByText('DEGO-QC-001')

    //  `compareDocumentPosition` đọc thứ tự THẬT trong cây DOM — đó cũng là thứ
    //  tự trình đọc màn hình đọc ra và thứ tự mắt lướt qua.
    expect(text.compareDocumentPosition(code) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('nói rõ «Chưa cấp số» thay vì để trống khi văn bản chưa duyệt', () => {
    render(<DocumentCard doc={doc({ display_code: '' })} />)

    expect(screen.getByText('Chưa cấp số')).toBeInTheDocument()
  })

  describe('«Cần rà lại»', () => {
    it('hiện ở tab Văn bản đến khi văn bản cha đã đổi', () => {
      render(<DocumentCard doc={doc({ needs_review: true })} showReviewFlag />)

      expect(screen.getByText('Cần rà lại')).toBeInTheDocument()
    })

    it('im khi văn bản không cần rà lại', () => {
      render(<DocumentCard doc={doc({ needs_review: false })} showReviewFlag />)

      expect(screen.queryByText('Cần rà lại')).not.toBeInTheDocument()
    })

    /**
     * Tab «Văn bản đi» không có cột này trên bảng, nên thẻ cũng không được có —
     * hai khổ màn nói khác nhau về cùng một văn bản là chuyện không giải thích
     * được với người dùng.
     */
    it('im ở tab Văn bản đi dù cờ đang bật', () => {
      render(<DocumentCard doc={doc({ needs_review: true })} showOrigin />)

      expect(screen.queryByText('Cần rà lại')).not.toBeInTheDocument()
    })
  })

  describe('huy hiệu bản riêng', () => {
    it('đếm số bản riêng đã tách cho pháp nhân con', () => {
      render(<DocumentCard doc={doc({ clone_count: 3 })} showOrigin />)

      expect(screen.getByText('3 bản riêng')).toBeInTheDocument()
    })

    /**
     * `clone_count` chỉ có ở endpoint DANH SÁCH của tab đi; `0` và `undefined`
     * đều nghĩa là "không tách bản nào" — in ra «0 bản riêng» là bịa thêm một
     * khái niệm cho mọi dòng bình thường.
     */
    it.each([
      ['bằng 0', 0],
      ['thiếu hẳn', undefined],
    ])('im khi số bản riêng %s', (_name, cloneCount) => {
      render(<DocumentCard doc={doc({ clone_count: cloneCount })} showOrigin />)

      expect(screen.queryByText(/bản riêng/)).not.toBeInTheDocument()
    })
  })

  describe('pháp nhân · phòng chủ trì', () => {
    it('ghép hai ô thành một dòng ở tab Văn bản đi', () => {
      render(<DocumentCard doc={doc()} showOrigin />)

      expect(
        screen.getByText('CÔNG TY TNHH DEGO HOLDING · Phòng Kế toán'),
      ).toBeInTheDocument()
    })

    /**
     * Phòng chủ trì để trống là chuyện thường (văn bản cấp tập đoàn). Nối chuỗi
     * mà không lọc thì ra «CÔNG TY TNHH DEGO HOLDING · » — một dấu chấm giữa mồ
     * côi treo ở cuối dòng.
     */
    it('không để lại dấu · mồ côi khi thiếu phòng chủ trì', () => {
      render(<DocumentCard doc={doc({ department_name: '' })} showOrigin />)

      expect(screen.getByText('CÔNG TY TNHH DEGO HOLDING')).toBeInTheDocument()
    })

    it('im ở tab Văn bản đến — bảng bên đó cũng ẩn hai cột này', () => {
      render(<DocumentCard doc={doc()} showReviewFlag />)

      expect(screen.queryByText(/CÔNG TY TNHH DEGO HOLDING/)).not.toBeInTheDocument()
    })
  })

  /**
   * «Chờ bạn duyệt» đứng CẠNH trạng thái chứ không thay thế nó: văn bản vẫn đang
   * ở «Đang duyệt», thứ thêm vào là *lượt của ai*.
   */
  it('bày cả trạng thái lẫn «Chờ bạn duyệt» khi tới lượt người đang xem', () => {
    render(
      <DocumentCard
        doc={doc({ status: DOCUMENT_STATUS.submitted, status_label: 'Đang duyệt' })}
        awaitingMyApproval
      />,
    )

    expect(screen.getByText('Đang duyệt')).toBeInTheDocument()
    expect(screen.getByText('Chờ bạn duyệt')).toBeInTheDocument()
  })

  it('im «Chờ bạn duyệt» khi không phải lượt của người đang xem', () => {
    render(<DocumentCard doc={doc({ status: DOCUMENT_STATUS.submitted })} />)

    expect(screen.queryByText('Chờ bạn duyệt')).not.toBeInTheDocument()
  })

  /** Dòng chân chỉ dựng khi có gì để nói — thẻ rỗng thì đừng chừa một hàng trống. */
  it('bỏ hẳn dòng chân khi chưa có ngày hiệu lực và chưa có tệp', () => {
    render(<DocumentCard doc={doc({ effective_date: null, attachment_count: 0 })} />)

    expect(screen.queryByText(/Hiệu lực/)).not.toBeInTheDocument()
  })

  it('bày ngày hiệu lực và số tệp đính kèm khi có', () => {
    render(<DocumentCard doc={doc({ effective_date: '2026-01-30', attachment_count: 2 })} />)

    expect(screen.getByText('Hiệu lực 30/01/2026')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })
})
