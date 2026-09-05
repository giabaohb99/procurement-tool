/**
 * Query key tập trung một chỗ. Trải rác chuỗi thô trong component là nguyên nhân
 * số 1 của lỗi "sửa xong mà danh sách không tự nạp lại" — invalidate trượt key.
 *
 * Quy ước: `[<module>, <entity>, <tham số>]` để invalidate được theo tầng
 * (`queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })`).
 */
export const queryKeys = {
  /** Hồ sơ của chính người đang đăng nhập — Trang cá nhân đọc bằng khóa này. */
  auth: {
    all: ['auth'] as const,
    me: () => ['auth', 'me'] as const,
    /** Tuỳ chọn hiển thị cá nhân (bảng màu giao diện). */
    preferences: () => ['auth', 'preferences'] as const,
  },
  procurement: {
    all: ['procurement'] as const,
    purchaseRequests: (params?: Record<string, unknown>) =>
      ['procurement', 'purchase-requests', params ?? {}] as const,
    purchaseRequest: (id: number) => ['procurement', 'purchase-requests', id] as const,
    /** Số đã đặt theo mã hàng của một phiếu YCMH. */
    purchaseRequestProgress: (id: number) =>
      ['procurement', 'purchase-requests', id, 'order-progress'] as const,
    /** Những người được phép duyệt bước 1 của một phiếu YCMH (CR-071). */
    purchaseRequestDeptHeads: (id: number) =>
      ['procurement', 'purchase-requests', id, 'dept-head-candidates'] as const,
    surveyRequests: (params?: Record<string, unknown>) =>
      ['procurement', 'survey-requests', params ?? {}] as const,
    surveyRequest: (id: number) => ['procurement', 'survey-requests', id] as const,
    /**
     * Khung KẾT QUẢ của YCBG (`/{id}/result`) — phải tách khóa khỏi khung đầu phiếu
     * ở trên, vì backend trả hai hình dạng khác nhau cho cùng một phiếu.
     */
    surveyRequestResult: (id: number) =>
      ['procurement', 'survey-requests', id, 'result'] as const,
    /**
     * Khung XỬ LÝ của YCBG (`/{id}/process`) — bản nội bộ cho NSTM, kèm đủ danh
     * tính NCC. Cũng phải tách khóa riêng như `result` ở trên.
     */
    surveyRequestProcess: (id: number) =>
      ['procurement', 'survey-requests', id, 'process'] as const,
    /** Bảng "Kết quả khảo sát đã duyệt" chọn được cho MỘT dòng của khung xử lý. */
    surveyRequestAvailableLines: (id: number, lineId: number, params?: Record<string, unknown>) =>
      ['procurement', 'survey-requests', id, 'process', 'available', lineId, params ?? {}] as const,
    purchaseOrders: (params?: Record<string, unknown>) =>
      ['procurement', 'purchase-orders', params ?? {}] as const,
    purchaseOrder: (id: number) => ['procurement', 'purchase-orders', id] as const,
    surveys: (params?: Record<string, unknown>) =>
      ['procurement', 'surveys', params ?? {}] as const,
    survey: (id: number) => ['procurement', 'surveys', id] as const,
    purchaseProgress: (params?: Record<string, unknown>) =>
      ['procurement', 'purchase-progress', params ?? {}] as const,
    surveyReport: (params?: Record<string, unknown>) =>
      ['procurement', 'survey-report', params ?? {}] as const,

    /**
     * Báo cáo mua hàng. Sáu đường API khác nhau nên sáu khóa riêng — chung một
     * khóa thì đổi tab là ghi đè cache của tab trước, quay lại phải tải lại.
     */
    reportProcurement: (params?: Record<string, unknown>) =>
      ['procurement', 'purchase-report', 'procurement', params ?? {}] as const,
    reportMatrix: (params?: Record<string, unknown>) =>
      ['procurement', 'purchase-report', 'matrix', params ?? {}] as const,
    reportRequestMatrix: (params?: Record<string, unknown>) =>
      ['procurement', 'purchase-report', 'request-matrix', params ?? {}] as const,
    /** Bảng phẳng theo khoảng ngày — khóa mang cả đường API vì mỗi tab một đường. */
    reportRange: (endpoint: string, params?: Record<string, unknown>) =>
      ['procurement', 'purchase-report', 'range', endpoint, params ?? {}] as const,
    reportShippingDetail: (params?: Record<string, unknown>) =>
      ['procurement', 'purchase-report', 'shipping-detail', params ?? {}] as const,
    reportDaily: (params?: Record<string, unknown>) =>
      ['procurement', 'purchase-report', 'daily', params ?? {}] as const,

    /** Số liệu trang Tổng quan Thu mua (`/api/dashboard/overview`). */
    dashboard: () => ['procurement', 'dashboard'] as const,
  },
  production: {
    all: ['production'] as const,
    // Danh mục NCC nằm ở phân hệ Sản xuất (không phải Thu mua).
    suppliers: (params?: Record<string, unknown>) =>
      ['production', 'suppliers', params ?? {}] as const,
    supplier: (id: number) => ['production', 'suppliers', id] as const,
    /** Hợp đồng — danh mục dùng chung, đặt ở Sản xuất cùng chỗ với NCC. */
    allContracts: ['production', 'contracts'] as const,
    contracts: (params?: Record<string, unknown>) =>
      ['production', 'contracts', params ?? {}] as const,
    contract: (id: number) => ['production', 'contracts', id] as const,
    /** Dòng khảo sát của một NCC (`/api/survey-report/by-supplier`). */
    supplierSurveys: (params?: Record<string, unknown>) =>
      ['production', 'suppliers', 'surveys', params ?? {}] as const,
    /**
     * KPI giao hàng của NCC, lấy từ báo cáo ma trận. Khóa mang cả năm vì backend
     * mặc định NĂM HIỆN TẠI khi không gửi tham số.
     */
    supplierKpi: (year: string) => ['production', 'suppliers', 'kpi', year] as const,
  },
  hr: {
    all: ['hr'] as const,
    employees: (params?: Record<string, unknown>) => ['hr', 'employees', params ?? {}] as const,
    employee: (id: number) => ['hr', 'employees', id] as const,
    employeeDepartments: (id: number) => ['hr', 'employees', id, 'departments'] as const,
    departments: (params?: Record<string, unknown>) => ['hr', 'departments', params ?? {}] as const,
    department: (id: number) => ['hr', 'departments', id] as const,
    departmentCompanies: (id: number) => ['hr', 'departments', id, 'companies'] as const,
    /** Cặp (phòng ban × pháp nhân) của một nhóm pháp nhân — khóa theo danh sách id. */
    departmentsByCompanies: (companyIds: number[]) =>
      ['hr', 'departments', 'by-companies', [...companyIds].sort((a, b) => a - b)] as const,
    companies: (params?: Record<string, unknown>) => ['hr', 'companies', params ?? {}] as const,
    company: (id: number) => ['hr', 'companies', id] as const,
    roles: (params?: Record<string, unknown>) => ['hr', 'roles', params ?? {}] as const,
    /** Danh sách entity/action/scope để dựng ma trận — gần như bất biến. */
    permissionMeta: () => ['hr', 'permission-meta'] as const,
    rolePermissions: (roleId: number) => ['hr', 'roles', roleId, 'permissions'] as const,
    userAccounts: (params?: Record<string, unknown>) => ['hr', 'users', params ?? {}] as const,
    userAccount: (id: number) => ['hr', 'users', id] as const,
    userScope: (userId: number, roleId: number) =>
      ['hr', 'users', userId, 'scope', roleId] as const,
  },
  /** Phân hệ Văn thư. Danh mục nền nạp cả danh sách nên key không mang tham số lọc. */
  document: {
    all: ['document'] as const,
    numberingRuleAll: ['document', 'numbering-rules'] as const,
    numberPreviewAll: ['document', 'number-preview'] as const,
    numberingRules: (direction: number) => ['document', 'numbering-rules', direction] as const,
    /**
     * Một quy tắc theo id. Chèn `'detail'` vào giữa là BẮT BUỘC: không có nó thì
     * key trùng hệt `numberingRules(direction)` — quy tắc id 1 và chiều "văn bản
     * đến" (direction 1) dùng chung một ô nhớ, đọc chi tiết xong là danh sách
     * hiện một bản ghi lẻ.
     */
    numberingRule: (id: number) => ['document', 'numbering-rules', 'detail', id] as const,
    /** Mã đưa vào số hiệu, gom từ năm bảng — chỉ nạp khi mở hộp thoại sửa mã. */
    issueCodes: () => ['document', 'issue-codes'] as const,
    docTypes: () => ['document', 'doc-types'] as const,
    docType: (id: number) => ['document', 'doc-types', id] as const,
    securityLevels: () => ['document', 'security-levels'] as const,
    securityLevel: (id: number) => ['document', 'security-levels', id] as const,
    templates: (params?: Record<string, unknown>) =>
      ['document', 'templates', params ?? {}] as const,
    template: (id: number) => ['document', 'templates', id] as const,
    externalParties: () => ['document', 'external-parties'] as const,
    externalParty: (id: number) => ['document', 'external-parties', id] as const,
    books: (year?: number) => ['document', 'books', year ?? 0] as const,
    book: (id: number) => ['document', 'books', id] as const,
    /** Bộ đếm tách riêng theo năm: đổi năm là đọc lại, không đụng bản ghi sổ. */
    bookCounter: (id: number, year: number) => ['document', 'books', id, 'counter', year] as const,

    /** Số liệu trang tổng quan Văn thư, theo bộ lọc của thanh trên cùng trang. */
    dashboard: (params?: Record<string, unknown>) =>
      ['document', 'dashboard', params ?? {}] as const,
    /** Gợi ý cho ô «Nơi lưu trữ cứng» — các giá trị đã từng nhập. */
    storageLocations: () => ['document', 'storage-locations'] as const,
    records: (params?: Record<string, unknown>) => ['document', 'records', params ?? {}] as const,
    record: (id: number) => ['document', 'records', id] as const,
    /** Danh sách phiên bản — KHÔNG kèm nội dung, nhẹ. */
    versions: (documentId: number) => ['document', 'records', documentId, 'versions'] as const,
    /** Một phiên bản KÈM nội dung — tách key để mở bản khác không nạp lại cả danh sách. */
    version: (documentId: number, versionId: number) =>
      ['document', 'records', documentId, 'versions', versionId] as const,
    access: (documentId: number) => ['document', 'records', documentId, 'access'] as const,
    /** Quan hệ cha–con hai chiều + phần khai còn thiếu để gửi duyệt (nhóm E). */
    links: (documentId: number) => ['document', 'records', documentId, 'links'] as const,
    /** Các ô quan hệ form phải tự hiện theo loại, kèm danh sách chọn được (E03). */
    linkSlots: (documentId: number) => ['document', 'records', documentId, 'link-slots'] as const,
    tree: (documentId: number) => ['document', 'records', documentId, 'tree'] as const,
    /** F10 — bảng theo dõi các bản clone của một văn bản gốc. */
    clones: (documentId: number) => ['document', 'records', documentId, 'clones'] as const,
    /** J04 — bản xem trước lúc ban hành. */
    issuePreview: (documentId: number) =>
      ['document', 'records', documentId, 'issue-preview'] as const,
    /** Hộp thư TÔI được gửi danh nghĩa khi ban hành văn bản này (26/08/2026). */
    issueMailboxes: (documentId: number) =>
      ['document', 'records', documentId, 'mailboxes'] as const,
    /** J10 — văn bản này bị văn bản nào sửa đổi / thay thế / bãi bỏ. */
    amendedBy: (documentId: number) =>
      ['document', 'records', documentId, 'amended-by'] as const,
    /** Phạm vi áp dụng của một văn bản (F01–F04). */
    scopes: (documentId: number) => ['document', 'records', documentId, 'scopes'] as const,
    scopeOptions: () => ['document', 'scope-options'] as const,
    /** Chữ ký của một văn bản (J02, J03). */
    signatures: (documentId: number) =>
      ['document', 'records', documentId, 'signatures'] as const,
    signKinds: () => ['document', 'sign-kinds'] as const,
    /** F05 — văn bản đang áp dụng cho chính tôi. Không theo văn bản nào. */
    appliesToMe: () => ['document', 'applies-to-me'] as const,
    /** Quy tắc quan hệ theo LOẠI văn bản — danh mục nền, không theo văn bản nào. */
    linkRulesAll: ['document', 'link-rules'] as const,
    /**
     * Bảng quy tắc, lọc theo loại nguồn. `0` = cả bảng (trang danh mục), id =
     * chỉ quy tắc của một loại (thẻ quan hệ trên trang loại văn bản). Hai chỗ
     * đọc hai danh sách khác nhau nên khóa phải khác nhau; muốn dọn cả hai thì
     * vô hiệu theo `linkRulesAll`.
     */
    linkRules: (sourceTypeId = 0) => ['document', 'link-rules', sourceTypeId] as const,
    linkRule: (id: number) => ['document', 'link-rules', 'detail', id] as const,
    linkRuleOptions: () => ['document', 'link-rules', 'options'] as const,
    permissions: (documentId: number) =>
      ['document', 'records', documentId, 'permissions'] as const,
    suggestions: (params: Record<string, unknown>) => ['document', 'suggestions', params] as const,
    /** Quan hệ tiên quyết còn thiếu của một loại — hỏi trước khi tạo văn bản (E04b). */
    prerequisites: (docTypeId: number) => ['document', 'prerequisites', docTypeId] as const,
    numberPreview: (params: Record<string, unknown>) =>
      ['document', 'number-preview', params] as const,
  },
  /**
   * Bộ máy phê duyệt dùng chung — KHÔNG thuộc phân hệ nào. Cùng bộ khóa này
   * phục vụ văn bản, YCMH, ĐMH, khảo sát, YCBG, YCTT.
   */
  approval: {
    all: ['approval'] as const,
    myTasks: (entity: string) => ['approval', 'my-tasks', entity] as const,
    /** «Đã duyệt gần đây» — phiếu chính tôi vừa quyết định, theo số ngày nhìn lại. */
    myHistory: (entity: string, days: number) =>
      ['approval', 'my-history', entity, days] as const,
    options: () => ['approval', 'options'] as const,
    flows: (entity: string) => ['approval', 'flows', entity] as const,
    flow: (id: number) => ['approval', 'flows', 'detail', id] as const,
    trail: (instanceId: number) => ['approval', 'trail', instanceId] as const,
    /** Phiên duyệt của MỘT chứng từ — trang chi tiết chứng từ hỏi bằng key này. */
    ofEntity: (entity: string, entityId: number) =>
      ['approval', 'of-entity', entity, entityId] as const,
    switches: () => ['approval', 'switches'] as const,
    delegations: (employeeId: number) => ['approval', 'delegations', employeeId] as const,
  },
  /** Chuông thông báo trên thanh trên — dùng chung cho mọi phân hệ. */
  notification: {
    all: ['notification'] as const,
    list: (params?: Record<string, unknown>) => ['notification', 'list', params ?? {}] as const,
    alerts: () => ['notification', 'alerts'] as const,
    /**
     * Việc cần làm (`/api/dashboard/tasks`) — nằm chung nhóm `notification` là
     * CỐ Ý (CR-215): "đánh dấu làm xong" phải ẩn cả ở chuông cảnh báo, nên một
     * lần vô hiệu nhóm này là tab việc lẫn chuông cùng nạp lại.
     */
    tasks: (params?: Record<string, unknown>) => ['notification', 'tasks', params ?? {}] as const,
  },
  // Phân hệ đang tắt — giữ chỗ để bật lại không phải nghĩ lại quy ước key.
  sales: {
    all: ['sales'] as const,
  },
  inventory: {
    all: ['inventory'] as const,
    /** Tồn hiện tại theo bộ ba công ty · kho · mã SP. */
    stock: (params?: Record<string, unknown>) => ['inventory', 'stock', params ?? {}] as const,
    /** Sổ phát sinh nhập/xuất — tách khóa khỏi `stock` vì là API khác. */
    moves: (params?: Record<string, unknown>) => ['inventory', 'moves', params ?? {}] as const,
    // Ba danh mục nền dưới đây không mang tham số lọc: nạp trọn danh sách một
    // lần rồi lọc tại chỗ, trừ ô tìm sản phẩm (danh mục hàng nghìn mã).
    warehouses: () => ['inventory', 'warehouses'] as const,
    itemGroups: () => ['inventory', 'item-groups'] as const,
    products: (search: string) => ['inventory', 'products', search] as const,
  },
  finance: {
    all: ['finance'] as const,
    payables: (params?: Record<string, unknown>) => ['finance', 'payables', params ?? {}] as const,
    /**
     * Bốn số tổng của màn Công nợ. Tách khóa khỏi danh sách ở trên vì hai lời
     * gọi ăn chung bộ lọc nhưng KHÁC tham số phân trang — dùng chung khóa thì
     * đổi trang cũng nạp lại tổng, mà tổng thì không đổi theo trang.
     */
    payableSummary: (params?: Record<string, unknown>) =>
      ['finance', 'payables', 'summary', params ?? {}] as const,
    /** Danh sách Yêu cầu thanh toán (YCTT), lọc theo tham số truyền vào. */
    paymentRequests: (params?: Record<string, unknown>) =>
      ['finance', 'payment-requests', params ?? {}] as const,
    /** Một phiếu YCTT theo id — hành động (duyệt/chi…) làm mất hiệu lực khóa này. */
    paymentRequest: (id: number) => ['finance', 'payment-requests', id] as const,
  },
  system: {
    all: ['system'] as const,
    /** Cấu hình chạy nóng (email, lưu trữ, công tắc quy trình) — một khóa duy nhất. */
    settings: () => ['system', 'settings'] as const,
    backups: (params?: Record<string, unknown>) => ['system', 'backups', params ?? {}] as const,
    auditLogs: (params?: Record<string, unknown>) => ['system', 'audit-logs', params ?? {}] as const,
    /** Hộp thư gửi danh nghĩa địa chỉ khác (26/08/2026). */
    mailboxes: () => ['system', 'mailboxes'] as const,
    /** Mẫu email thông báo theo bước (Đặt xe) — sửa được trong Cấu hình. */
    emailTemplates: () => ['system', 'email-templates'] as const,
    /** Loại trừ email theo cá nhân / phòng ban / công ty. */
    emailExclusions: () => ['system', 'email-exclusions'] as const,
    imports: (params?: Record<string, unknown>) => ['system', 'imports', params ?? {}] as const,
    importDetail: (id: number | string) => ['system', 'imports', 'detail', id] as const,
    importLogs: (id: number | string, params?: Record<string, unknown>) =>
      ['system', 'imports', 'logs', id, params ?? {}] as const,
    exports: (params?: Record<string, unknown>) => ['system', 'exports', params ?? {}] as const,
    exportEntities: () => ['system', 'exports', 'entities'] as const,
    exportDetail: (id: number | string) => ['system', 'exports', 'detail', id] as const,
  },
  /** Phân hệ Hỗ trợ — phiếu hỗ trợ (ticket) và luồng trao đổi trong từng phiếu. */
  support: {
    all: ['support'] as const,
    tickets: (params?: Record<string, unknown>) => ['support', 'tickets', params ?? {}] as const,
    ticket: (id: number) => ['support', 'tickets', id] as const,
    /** Tệp gửi kèm lúc TẠO phiếu (entity `ticket`) — tách khỏi tệp trong tin nhắn. */
    ticketAttachments: (id: number) => ['support', 'tickets', id, 'attachments'] as const,
  },
  /** Diễn đàn nội bộ — bảng tin cuộn vô hạn + từng bài viết. */
  forum: {
    all: ['forum'] as const,
    /** Feed chung, phân trang con trỏ — khóa của `useInfiniteQuery`. */
    feed: () => ['forum', 'posts', 'feed'] as const,
    /**
     * Bài MỚI NHẤT trên máy chủ (limit=1) — nút "Có bài viết mới" thăm dò bằng
     * khóa này. Tách khỏi `feed` để lời thăm dò không đè cache của feed.
     */
    feedHead: () => ['forum', 'posts', 'head'] as const,
    /** Bài đang ghim (F9a) — dải đầu Bảng tin + tab «Thông báo», không phân trang. */
    pinned: () => ['forum', 'posts', 'pinned'] as const,
    post: (id: number) => ['forum', 'posts', id] as const,
    /** Mọi tủ bài viết cá nhân — dùng để reset cả cụm sau khi đăng/xóa bài. */
    userPostsAll: () => ['forum', 'posts', 'user'] as const,
    /** Tủ bài viết của một người (trang cá nhân) — cũng cuộn vô hạn như feed. */
    userPosts: (userId: number) => ['forum', 'posts', 'user', userId] as const,
    /** Danh sách người đã thích một bài — chỉ nạp khi mở hộp thoại. */
    postLikes: (postId: number) => ['forum', 'posts', postId, 'likes'] as const,
    /** Trang bình luận GỐC của một bài (F4) — phản hồi tải riêng khi bung, không có khóa. */
    comments: (postId: number) => ['forum', 'posts', postId, 'comments'] as const,
  },
  /** Trợ lý AI — nhà cung cấp, danh sách hội thoại và từng hội thoại kèm tin. */
  assistant: {
    all: ['assistant'] as const,
    /** Nhà cung cấp + model mặc định — gần như bất biến trong phiên. */
    providers: () => ['assistant', 'providers'] as const,
    conversations: () => ['assistant', 'conversations'] as const,
    conversation: (id: number) => ['assistant', 'conversations', id] as const,
  },
  /**
   * Phân hệ Công việc (CR-216). `board` là khóa nặng nhất — mọi thao tác trên
   * thẻ (kéo cột, tick xong, đổi PIC, gắn nhãn) đều phải làm nó mới lại, nên
   * mutation nào của task cũng invalidate `board(listId)`.
   */
  work: {
    all: ['work'] as const,
    /** Cây nhóm → list bên trái; đổi khi tạo/sửa/lưu trữ nhóm hoặc list. */
    sidebar: (includeArchived: boolean) => ['work', 'sidebar', includeArchived] as const,
    /** Số liệu màn Tổng quan phân hệ Dự án. */
    overview: () => ['work', 'overview'] as const,
    lists: (includeArchived: boolean) => ['work', 'lists', includeArchived] as const,
    /**
     * Bảng liệt kê dự án — cùng dữ liệu `lists` nhưng kèm chủ sở hữu + thành
     * viên. Cố ý nằm DƯỚI nhánh `lists` để mọi chỗ đang invalidate
     * `lists(false)` quét trúng luôn, không thì số việc trên bảng đứng im.
     */
    projects: (includeArchived: boolean) =>
      ['work', 'lists', includeArchived, 'people'] as const,
    list: (id: number) => ['work', 'lists', id] as const,
    board: (listId: number) => ['work', 'lists', listId, 'board'] as const,
    members: (listId: number) => ['work', 'lists', listId, 'members'] as const,
    sections: (listId: number) => ['work', 'lists', listId, 'sections'] as const,
    labelFields: (listId: number) => ['work', 'lists', listId, 'label-fields'] as const,
    task: (id: number) => ['work', 'tasks', id] as const,
  },
  vehicleBooking: {
    all: ['vehicle-booking'] as const,
    bookings: (params?: Record<string, unknown>) =>
      ['vehicle-booking', 'bookings', params ?? {}] as const,
    booking: (id: number) => ['vehicle-booking', 'bookings', id] as const,
  },
  /** Phân hệ Duyệt dấu — phiếu yêu cầu đóng dấu + danh mục Loại con dấu. */
  sealRequest: {
    all: ['seal-request'] as const,
    list: (params?: Record<string, unknown>) =>
      ['seal-request', 'list', params ?? {}] as const,
    detail: (id: number) => ['seal-request', 'list', id] as const,
  },
  sealType: {
    all: ['seal-type'] as const,
    list: (params?: Record<string, unknown>) => ['seal-type', 'list', params ?? {}] as const,
    detail: (id: number) => ['seal-type', 'list', id] as const,
  },
} as const
