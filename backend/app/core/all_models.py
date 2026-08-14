"""Import mọi model để Base.metadata đầy đủ (dùng cho Alembic autogenerate)."""
from app.core.base_model import Base  # noqa: F401

from app.modules.attachment import model as _attachment  # noqa: F401
from app.modules.audit import model as _audit  # noqa: F401
from app.modules.catalog import model as _catalog  # noqa: F401
from app.modules.company import model as _company  # noqa: F401
from app.modules.department import model as _department  # noqa: F401
from app.modules.employee import model as _employee  # noqa: F401
from app.modules.supplier import model as _supplier  # noqa: F401
from app.modules.product import model as _product  # noqa: F401
from app.modules.survey import model as _survey  # noqa: F401
from app.modules.purchase_request import model as _pr  # noqa: F401
from app.modules.purchase_order import model as _po  # noqa: F401
from app.modules.purchase_history import model as _purchase_history  # noqa: F401
from app.modules.goods_receipt import model as _gr  # noqa: F401
from app.modules.inventory import model as _inventory  # noqa: F401
from app.modules.payable import model as _payable  # noqa: F401
from app.modules.payment_request import model as _payment_request  # noqa: F401
from app.modules.role import model as _role  # noqa: F401
from app.modules.user import model as _user  # noqa: F401
from app.modules.notification import model as _notification  # noqa: F401
from app.modules.push import model as _push  # noqa: F401
from app.modules.report import model as _report  # noqa: F401
from app.modules.contract import model as _contract  # noqa: F401
from app.modules.setting import model as _setting  # noqa: F401
from app.modules.category_assignee import model as _category_assignee  # noqa: F401
from app.modules.survey_request import model as _survey_request  # noqa: F401
from app.modules.import_tool import model as _import_tool  # noqa: F401
from app.modules.backup import model as _backup  # noqa: F401
from app.modules.help_center import model as _help_center  # noqa: F401
from app.modules.faq import model as _faq  # noqa: F401
from app.modules.ticket import model as _ticket  # noqa: F401
from app.modules.comment import model as _comment  # noqa: F401
from app.modules.doc_catalog import model as _doc_catalog  # noqa: F401
from app.modules.doc_catalog import book_model as _doc_book  # noqa: F401
