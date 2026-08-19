/**
 * Đường dẫn tập trung — sửa URL một chỗ, không phải grep chuỗi khắp nơi.
 * Mỗi module đóng góp một nhánh; `routes.tsx` của module dùng chính hằng số này.
 */
export const appRoutes = {
  login: '/login',
  forgotPassword: '/forgot-password',
  /** Màn chọn phân hệ — trang chủ sau khi đăng nhập. */
  launcher: '/',

  sales: {
    root: '/sales',
  },
  inventory: {
    root: '/inventory',
    /** Tồn hiện tại theo kho — số dư do hệ thống tính, chỉ sửa qua điều chỉnh tay. */
    stock: '/inventory/stock',
  },
  procurement: {
    root: '/procurement',
    /** Yêu cầu báo giá (YCBG) — bước đầu của luồng mua hàng. */
    surveyRequests: '/procurement/survey-requests',
    surveyRequestNew: '/procurement/survey-requests/new',
    surveyRequestDetail: (id: number | string) => `/procurement/survey-requests/${id}`,
    /** Yêu cầu mua hàng (PYC). */
    purchaseRequests: '/procurement/purchase-requests',
    purchaseRequestNew: '/procurement/purchase-requests/new',
    purchaseRequestDetail: (id: number | string) => `/procurement/purchase-requests/${id}`,
    purchaseRequestPrint: (id: number | string) => `/print/purchase-request/${id}`,
    /** Đơn mua hàng (ĐMH). */
    purchaseOrders: '/procurement/purchase-orders',
    purchaseOrderNew: '/procurement/purchase-orders/new',
    purchaseOrderDetail: (id: number | string) => `/procurement/purchase-orders/${id}`,
    purchaseOrderPrint: (id: number | string) => `/print/purchase-order/${id}`,
    /** Báo cáo tiến độ theo từng lần giao hàng. */
    purchaseProgress: '/procurement/purchase-progress',
    /** Phiếu khảo sát NCC / sản phẩm. */
    surveys: '/procurement/surveys',
    /** Báo cáo khảo sát, cắt theo dòng khảo sát. */
    surveyReport: '/procurement/survey-report',
    /** Báo cáo mua hàng — tám tab trên cùng một bộ lọc công ty / năm. */
    purchaseReport: '/procurement/purchase-report',
  },
  /**
   * Bộ máy phê duyệt dùng chung — không nằm trong phân hệ nào vì «Việc của tôi»
   * gom việc của CẢ văn thư lẫn thu mua.
   */
  approval: {
    root: '/approval',
    /** I17 — màn được mở nhiều nhất của cả hệ. */
    myTasks: '/approval/my-tasks',
    flows: '/approval/flows',
    flowNew: '/approval/flows/new',
    flowDetail: (id: number | string) => `/approval/flows/${id}`,
    /** I26 — công tắc bật bộ máy duyệt mới theo từng loại chứng từ. */
    engine: '/approval/engine',
    delegations: '/approval/delegations',
  },
  finance: {
    root: '/finance',
    /** Công nợ phải trả — bảng chỉ đọc, sinh tự động khi nhận hàng. */
    payables: '/finance/payables',
  },
  customer: {
    root: '/customer',
  },
  project: {
    root: '/project',
  },
  document: {
    root: '/document',
    /** Văn bản đến / đi / nội bộ. */
    documents: '/document/documents',
    documentNew: '/document/documents/new',
    documentDetail: (id: number | string) => `/document/documents/${id}`,
    /** F05 — văn bản mà chính tôi nằm trong phạm vi áp dụng. */
    appliedToMe: '/document/applied-to-me',
    /** Danh sách SỔ (mỗi sổ một bộ đếm riêng), không phải danh sách văn bản. */
    books: '/document/books',
    bookNew: '/document/books/new',
    bookDetail: (id: number | string) => `/document/books/${id}`,
    /**
     * Thiết lập văn bản - các danh mục nền và thư viện mẫu nằm chung một trang,
     * phân biệt bằng `?tab=`.
     */
    settings: '/document/settings',
    /** Quy tắc đánh số — danh sách và trang khai báo, KHÔNG dùng hộp thoại. */
    numberingRules: '/document/numbering-rules',
    numberingRuleNew: '/document/numbering-rules/new',
    numberingRuleDetail: (id: number | string) => `/document/numbering-rules/${id}`,
    /** Quy tắc quan hệ cha–con giữa các LOẠI văn bản (E01). */
    linkRules: '/document/link-rules',
    linkRuleNew: '/document/link-rules/new',
    linkRuleDetail: (id: number | string) => `/document/link-rules/${id}`,
    settingsTab: (tab: 'types' | 'templates' | 'security-levels' | 'partners') =>
      `/document/settings?tab=${tab}`,
    /** Loại văn bản (công văn, quyết định…). */
    typeNew: '/document/types/new',
    typeDetail: (id: number | string) => `/document/types/${id}`,
    /** Thư viện nội dung mẫu dùng khi tạo văn bản. */
    templateNew: '/document/templates/new',
    templateDetail: (id: number | string) => `/document/templates/${id}`,
    /** Đơn vị gửi nhận bên ngoài. */
    partnerNew: '/document/partners/new',
    partnerDetail: (id: number | string) => `/document/partners/${id}`,
  },
  report: {
    root: '/report',
  },
  system: {
    root: '/system',
  },
  production: {
    root: '/production',
    /** Danh mục nhà cung cấp / đơn vị vận chuyển — thuộc phân hệ Sản xuất. */
    suppliers: '/production/suppliers',
    supplierDetail: (id: number | string) => `/production/suppliers/${id}`,
  },
  hr: {
    root: '/hr',
    employees: '/hr/employees',
    employeeDetail: (id: number | string) => `/hr/employees/${id}`,
    departments: '/hr/departments',
    departmentDetail: (id: number | string) => `/hr/departments/${id}`,
    companies: '/hr/companies',
    companyDetail: (id: number | string) => `/hr/companies/${id}`,
    /** Ma trận vai trò × quyền + danh sách tài khoản. */
    permissions: '/hr/permissions',
    /** Gán vai trò và phạm vi dữ liệu cho MỘT tài khoản. */
    userPermissionDetail: (userId: number | string) => `/hr/permissions/users/${userId}`,
  },
  approvalSeal: {
    root: '/approval-seal',
  },
  vehicleBooking: {
    root: '/vehicle-booking',
  },
  degoCoffee: {
    root: '/dego-coffee',
  },
} as const
