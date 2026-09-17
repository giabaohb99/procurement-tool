"""Tra danh mục ba nấc: khóa app cũ -> id ERP (§9.6 bản thiết kế).

BA NẤC, GOM MỘT CHỖ:

1. Dấu `legacy_id` dưới DB. Nấc này ăn 100% ca hiện có — 1313 phiếu nạp ngày
   16/09/2026 không trượt lần nào.
2. Không ra thì tra theo ĐẶC ĐIỂM TỰ NHIÊN: xe theo biển số, tài xế theo số
   điện thoại rồi tới tên, phòng ban và công ty theo tên đã chuẩn hóa. Khớp thì
   **đóng dấu `legacy_id` vào hàng có sẵn** rồi trả về — lần sau nấc 1 ăn luôn,
   và cái đợt nạp tay chốt được bao nhiêu cặp thì bộ này tự chốt tiếp bấy nhiêu.
3. Vẫn không ra mới tính tạo, và **KHÔNG tạo đồng đều mọi loại**: chỉ xe và tài
   xế, chỉ khi `SYNC_DATXE_AUTO_CREATE` bật. Phòng ban dính phân quyền theo
   phạm vi, công ty dính hợp đồng và công nợ, còn nhân sự / tài khoản / phân
   quyền thì tuyệt đối không — đây là cửa máy-gọi-máy từ ngoài vào, cho app cũ
   tự đẻ tài khoản ERP là mở đường leo thang quyền.

VÌ SAO KHÔNG CHO TỰ TẠO TẤT: bảng khai tay ở `mapping.py` tồn tại chính vì mấy
cặp ghép cần NGƯỜI quyết — `"Tự lái"` bên app cũ là một hồ sơ tài xế còn bên ERP
là cờ `is_self_drive`, bốn phòng ban được gộp tay, ba UID Firebase cùng một con
người. Bộ tự tạo không sai về kỹ thuật, nó chỉ không biết **cái gì đã tồn tại
dưới một cái tên khác**.

HÀNG TỰ TẠO ĐI ĐÂU ĐỂ NGƯỜI SOÁT? `tab_vehicle` và `tab_driver` không có cột
"chờ soát" nào (bản thiết kế §9.6 viết `is_active = False` là viết theo trí
nhớ, model không có cột đó). Nên hàng mới đi ra bằng **cờ cảnh báo
`auto_created` trên dòng sổ đồng bộ** — màn sổ đã có sẵn ô lọc "chỉ dòng có
cảnh báo", đó chính là hàng đợi soát. Đừng mượn cột `status` để đánh dấu: nó là
trạng thái vận hành (`available` / `on_trip` / `maintenance`), ghi đè vào đó là
nói dối đội điều phối.

CÁCH DÙNG. Bộ tra bày ra bốn "khung nhìn" cư xử y hệt `dict` —
`catalog.companies`, `.departments`, `.vehicles`, `.drivers` — nên
`build_seal` / `build_booking` ở `builder.py` KHÔNG phải sửa một dòng nào:
chúng vẫn gọi `.get(khóa, 0)` như với dict chỉ mục phẳng của đợt nạp, chỉ khác
là bây giờ phía sau `.get` có đủ ba nấc.
"""
import collections
import logging
import re

from sqlalchemy import select

from app.core.config import settings
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.vehicle_booking.model import Driver, Vehicle

from .firebase import read_node

LOGGER = logging.getLogger(__name__)

#: Cờ gắn lên dòng sổ đồng bộ. Nhãn khai ở `sync_log/registry.py`.
WARN_AUTO_CREATED = "auto_created"
WARN_STAMPED_BY_NAME = "stamped_by_name"
WARN_UNRESOLVED = "unresolved_catalog"

#: Nhánh Firebase của từng loại danh mục.
BRANCH_BRAND = "brands"
BRANCH_DEPARTMENT = "departments"
BRANCH_VEHICLE = "vehicles"
BRANCH_DRIVER = "drivers"


def normalize_name(value: str) -> str:
    """Tên để đem so: bỏ khoảng trắng thừa, bỏ phân biệt hoa thường.

    CỐ Ý KHÔNG bỏ dấu tiếng Việt. "Phòng Kế toán" và "Phong Ke toan" là hai
    chuỗi khác nhau, và ghép nhầm hai phòng ban là ghép nhầm cả một vùng dữ
    liệu — thà tra không ra rồi để người chốt tay.
    """
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()


def normalize_plate(value: str) -> str:
    """Biển số để đem so: chỉ giữ chữ và số.

    Cùng một chiếc xe được gõ "51D-465.49", "51D46549", "51d 465 49" ở ba chỗ
    khác nhau; dấu chấm và gạch ngang không mang thông tin nào cả.
    """
    return re.sub(r"[^0-9a-z]", "", (value or "").lower())


def normalize_phone(value: str) -> str:
    """Số điện thoại để đem so: chỉ giữ chữ số, lấy CHÍN SỐ CUỐI.

    Chín số cuối là phần bất biến của một thuê bao Việt Nam — nó bỏ qua mọi
    kiểu viết đầu số (`0901234567`, `+84901234567`, `84901234567`).
    """
    digits = re.sub(r"\D", "", value or "")
    return digits[-9:] if len(digits) >= 9 else ""


class _CatalogView:
    """Khung nhìn kiểu `dict` của một loại danh mục, phía sau là ba nấc tra.

    Có `get` / `in` / `[]` đúng như dict để `builder.py` dùng lại nguyên si.
    Kết quả đã tra (kể cả tra trượt) được nhớ lại trong lượt chạy, nên một phiếu
    hỏi cùng một khóa ba lần chỉ tốn một lần đi hỏi Firebase.
    """

    def __init__(self, catalog: "LegacyCatalog", branch: str):
        self._catalog = catalog
        self._branch = branch

    def get(self, key, default=None):
        found = self._catalog.resolve(self._branch, key or "")
        return found if found else default

    def __contains__(self, key) -> bool:
        return bool(self._catalog.resolve(self._branch, key or ""))

    def __getitem__(self, key):
        found = self._catalog.resolve(self._branch, key or "")
        if not found:
            raise KeyError(key)
        return found


class LegacyCatalog:
    """Bộ tra danh mục dùng chung cho cả cái móc lẫn vòng quét.

    Dựng MỘT lần cho cả một lượt chạy rồi truyền đi: hàm dựng nạp sẵn mọi dấu
    `legacy_id` đang có (bốn truy vấn), nên dựng lại cho từng phiếu là bốn truy
    vấn nhân số phiếu.

    `fetch_node` tách ra được để bài kiểm chạy không cần mạng; mặc định là đọc
    thẳng Firebase của app cũ.
    """

    def __init__(self, db, *, allow_create: bool | None = None, fetch_node=None,
                 actor_id: int = 0):
        self.db = db
        #  Nấc 3 mặc định TẮT. Bật bằng `.env`, và bật rồi thì mỗi hàng đẻ ra
        #  đều mang cờ `auto_created` trên sổ để còn soát lại.
        self.allow_create = (settings.SYNC_DATXE_AUTO_CREATE
                             if allow_create is None else allow_create)
        self.fetch_node = fetch_node if fetch_node is not None else read_node
        self.actor_id = actor_id
        self.warnings: list[str] = []
        self.stats: collections.Counter = collections.Counter()

        self._models = {
            BRANCH_BRAND: Company,
            BRANCH_DEPARTMENT: Department,
            BRANCH_VEHICLE: Vehicle,
            BRANCH_DRIVER: Driver,
        }
        self._index: dict[str, dict[str, int]] = {
            branch: {row.legacy_id: row.id for row in db.execute(
                select(model).where(model.legacy_id != "")).scalars()}
            for branch, model in self._models.items()
        }
        #  Khóa đã tra trượt trong lượt này — đừng đi hỏi Firebase lại.
        self._missed: set[tuple[str, str]] = set()

        self.companies = _CatalogView(self, BRANCH_BRAND)
        self.departments = _CatalogView(self, BRANCH_DEPARTMENT)
        self.vehicles = _CatalogView(self, BRANCH_VEHICLE)
        self.drivers = _CatalogView(self, BRANCH_DRIVER)

    # --- nấc 1 -------------------------------------------------------------

    def resolve(self, branch: str, key: str) -> int:
        """Ba nấc, theo đúng thứ tự. Trả `0` khi không ra."""
        if not key:
            return 0
        found = self._index[branch].get(key)
        if found:
            return found
        if (branch, key) in self._missed:
            return 0
        found = self._match_by_nature(branch, key) or self._create(branch, key)
        if found:
            self._index[branch][key] = found
        else:
            self._missed.add((branch, key))
            self.stats[f"tra khong ra: {branch} {key}"] += 1
            self._warn(WARN_UNRESOLVED)
        return found

    # --- nấc 2 -------------------------------------------------------------

    def _match_by_nature(self, branch: str, key: str) -> int:
        """Tra theo đặc điểm tự nhiên rồi ĐÓNG DẤU vào hàng có sẵn."""
        node = self.fetch_node(f"{branch}/{key}")
        if not node:
            return 0
        row = self._find_row(branch, node)
        if row is None:
            return 0
        if row.legacy_id and row.legacy_id != key:
            #  Hàng này đã đeo dấu của một khóa KHÁC. Không đè: hai khóa app cũ
            #  cùng trỏ một hàng ERP là chuyện có thật (ba UID cùng một người),
            #  và đè lên là cắt đứt dây nối của khóa kia trong im lặng.
            self.stats[f"hang ERP da deo dau khac: {branch} {key}"] += 1
            return row.id
        row.legacy_id = key
        row.updated_by = self.actor_id
        self.db.flush()
        self.stats[f"dong dau theo dac diem tu nhien: {branch}"] += 1
        self._warn(WARN_STAMPED_BY_NAME)
        LOGGER.info("Đóng dấu legacy_id %r lên %s id %s", key, branch, row.id)
        return row.id

    def _find_row(self, branch: str, node: dict):
        if branch == BRANCH_VEHICLE:
            return self._first(Vehicle, Vehicle.license_plate,
                               normalize_plate(node.get("licensePlate")),
                               normalize_plate)
        if branch == BRANCH_DRIVER:
            phone = normalize_phone(node.get("phone"))
            row = self._first(Driver, Driver.phone, phone, normalize_phone) if phone else None
            #  Tên chỉ là đường lùi, và chỉ khi tên ĐÚNG MỘT hàng khớp: hai tài
            #  xế trùng tên thì ghép bừa một trong hai là phiếu gán sai người.
            return row or self._only(Driver, Driver.name, node.get("name"))
        if branch == BRANCH_DEPARTMENT:
            return self._only(Department, Department.name, node.get("name"))
        if branch == BRANCH_BRAND:
            return self._only(Company, Company.name, node.get("name"))
        return None

    def _first(self, model, column, needle: str, normalizer):
        """Quét hàng có `legacy_id` rỗng trước, so bằng giá trị đã chuẩn hóa.

        So trong Python chứ không so dưới SQL vì phép chuẩn hóa (bỏ dấu chấm
        của biển số, lấy chín số cuối của điện thoại) không viết được thành
        điều kiện SQL chạy trên cả MySQL lẫn SQLite.
        """
        if not needle:
            return None
        for row in self.db.execute(select(model)).scalars():
            if normalizer(getattr(row, column.key, "") or "") == needle:
                return row
        return None

    def _only(self, model, column, raw_name):
        """Khớp tên, và CHỈ khi đúng một hàng khớp."""
        needle = normalize_name(raw_name)
        if not needle:
            return None
        rows = [row for row in self.db.execute(select(model)).scalars()
                if normalize_name(getattr(row, column.key, "") or "") == needle]
        if len(rows) != 1:
            if rows:
                self.stats[f"ten trung {len(rows)} hang, khong dam ghep: {model.__name__}"] += 1
            return None
        return rows[0]

    # --- nấc 3 -------------------------------------------------------------

    def _create(self, branch: str, key: str) -> int:
        """Chỉ xe và tài xế, chỉ khi được bật. Xem bảng ở §9.6."""
        if not self.allow_create or branch not in (BRANCH_VEHICLE, BRANCH_DRIVER):
            return 0
        node = self.fetch_node(f"{branch}/{key}")
        if not node:
            return 0
        if branch == BRANCH_VEHICLE:
            plate = (node.get("licensePlate") or "").strip()
            if not plate:
                #  `license_plate` là cột UNIQUE: hai xe không biển số thì hàng
                #  thứ hai đâm vào ràng buộc. Đặt biển tạm từ chính khóa app cũ
                #  — vừa duy nhất, vừa lần ngược được về bản ghi bên kia.
                plate = f"[app cũ] {key}"[:50]
                self._warn("no_plate")
            row = Vehicle(
                license_plate=plate,
                model=(node.get("model") or "").strip()[:100],
                type=(node.get("type") or "").strip()[:50],
                capacity=float(node.get("capacity") or 4),
                is_external=bool(node.get("isExternal")),
                external_company=(node.get("externalCompany") or "").strip()[:255],
            )
        else:
            row = Driver(
                name=(node.get("name") or "").strip()[:255] or f"[app cũ] {key}"[:255],
                phone=(node.get("phone") or "").strip()[:20],
                license_number=(node.get("licenseNumber") or "").strip()[:50],
                is_external=bool(node.get("isExternal")),
                external_company=(node.get("externalCompany") or "").strip()[:255],
            )
        row.legacy_id = key
        row.created_by = self.actor_id
        row.updated_by = self.actor_id
        self.db.add(row)
        self.db.flush()
        self.stats[f"tu tao: {branch}"] += 1
        self._warn(WARN_AUTO_CREATED)
        LOGGER.info("Tự tạo %s id %s từ khóa app cũ %r — cần người soát lại",
                    branch, row.id, key)
        return row.id

    # --- cờ cảnh báo -------------------------------------------------------

    def _warn(self, flag: str) -> None:
        if flag not in self.warnings:
            self.warnings.append(flag)
