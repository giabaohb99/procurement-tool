import os
import csv
import json
from app.core.database import SessionLocal
# Import all models to compile SQLAlchemy mappers properly
from app.modules.attachment.model import FileLink, StoredFile  # noqa: F401
from app.modules.audit.model import AuditLog  # noqa: F401
from app.modules.catalog.model import (Brand, ItemGroup,  # noqa: F401
                                       Unit, Warehouse)
from app.modules.company.model import Company
from app.modules.department.model import Department  # noqa: F401
from app.modules.employee.model import Employee
from app.modules.product.model import Product
from app.modules.purchase_request.model import (PurchaseRequest,  # noqa: F401
                                                PurchaseRequestItem)
from app.modules.purchase_order.model import (PurchaseOrder,  # noqa: F401
                                              POItem, PODelivery)
from app.modules.goods_receipt.model import GoodsReceipt  # noqa: F401
from app.modules.inventory.model import Inventory, InventoryMove  # noqa: F401
from app.modules.payable.model import Payable  # noqa: F401
from app.modules.payment_request.model import (PaymentRequest,  # noqa: F401
                                               PaymentRequestLine)
from app.modules.role.model import Permission, Role
from app.modules.supplier.model import Supplier
from app.modules.survey.model import (Survey, SurveyProductLine,  # noqa: F401
                                      SurveySupplierLine)
from app.modules.user.model import User, UserRole
from app.modules.notification.model import Notification, EmailLog  # noqa: F401

def run():
    tsv_path = "/app/app/seed_data/phanloai.txt"
    json_path = "/app/app/seed_data/item_groups.json"
    
    if not os.path.exists(tsv_path):
        tsv_path = os.path.join(os.path.dirname(__file__), "seed_data/phanloai.txt")
        json_path = os.path.join(os.path.dirname(__file__), "seed_data/item_groups.json")
        
    print(f"Reading from TSV: {tsv_path}")
    
    item_groups_data = {}
    
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        print("Header:", header)
        
        for idx, row in enumerate(reader, start=2):
            if not row:
                continue
            while len(row) < 5:
                row.append("")
                
            name = row[0].strip()
            if not name:
                continue
                
            days = row[1].strip()
            note = row[2].strip()
            apply_date = row[3].strip()
            available = row[4].strip().upper() # TRUE or FALSE or empty
            
            if name not in item_groups_data:
                item_groups_data[name] = {
                    "name": name,
                    "std_days": "",
                    "std_days_unavail": "",
                    "note": "",
                    "apply_date": ""
                }
            
            entry = item_groups_data[name]
            
            if available == "TRUE":
                entry["std_days"] = days
            elif available == "FALSE":
                entry["std_days_unavail"] = days
            else:
                if not entry["std_days"]:
                    entry["std_days"] = days
                if not entry["std_days_unavail"]:
                    entry["std_days_unavail"] = days
                    
            if note:
                if entry["note"]:
                    if note not in entry["note"]:
                        entry["note"] += "\n" + note
                else:
                    entry["note"] = note
                    
            if apply_date:
                entry["apply_date"] = apply_date

    # Fallback missing std_days
    for name, entry in item_groups_data.items():
        if entry["std_days"] and not entry["std_days_unavail"]:
            entry["std_days_unavail"] = entry["std_days"]
        elif entry["std_days_unavail"] and not entry["std_days"]:
            entry["std_days"] = entry["std_days_unavail"]

    # Write to JSON
    list_data = list(item_groups_data.values())
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(list_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(list_data)} item groups to {json_path}")
    
    # Sync with Database
    db = SessionLocal()
    try:
        # Check existing item groups in DB by name
        existing_groups = {g.name: g for g in db.query(ItemGroup).all()}
        
        updated_count = 0
        inserted_count = 0
        
        for name, data in item_groups_data.items():
            if name in existing_groups:
                g = existing_groups[name]
                g.std_days = data["std_days"]
                g.std_days_unavail = data["std_days_unavail"]
                g.note = data["note"]
                g.apply_date = data["apply_date"]
                updated_count += 1
            else:
                cnt = db.query(ItemGroup).count() + 1
                code = f"PL{cnt:03d}"
                g = ItemGroup(
                    code=code,
                    name=name,
                    std_days=data["std_days"],
                    std_days_unavail=data["std_days_unavail"],
                    note=data["note"],
                    apply_date=data["apply_date"],
                    is_active=True
                )
                db.add(g)
                inserted_count += 1
                
        db.commit()
        print(f"Database sync completed: Updated {updated_count}, Inserted {inserted_count} item groups.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
