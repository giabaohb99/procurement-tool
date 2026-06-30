import csv
import sys
import os
from sqlalchemy.orm import Session

# Add the backend dir to path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.modules.catalog.model import Brand
from app.modules.employee.model import Employee
from app.core.utils import generate_code

def main():
    dept_file = r"/app/scripts/departments.csv"
    user_file = r"/app/scripts/users.csv"
    
    db = SessionLocal()
    
    try:
        # 1. Parse and Upsert Employees (to ensure they exist before linking to departments)
        print("Importing Employees...")
        with open(user_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get('id', '').strip()
                name = row.get('name', '').strip()
                email = row.get('email', '').strip()
                disabled = row.get('disabled', '').strip().lower() == 'true'
                
                if not code or not name:
                    continue
                    
                emp = db.query(Employee).filter(Employee.code == code).first()
                if not emp:
                    emp = Employee(
                        code=code,
                        full_name=name,
                        email=email,
                        is_active=not disabled,
                        created_by=1,
                        updated_by=1
                    )
                    db.add(emp)
                else:
                    emp.full_name = name
                    emp.email = email
                    emp.is_active = not disabled
            
            db.commit()
            print("Employees imported/updated successfully.")
            
        # 2. Parse and Upsert Brands (Departments)
        print("Importing Brands (Departments)...")
        brand_map = {}
        with open(dept_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dept_name = row.get('dept', '').strip()
                manager_name = row.get('manager', '').strip()
                
                if not dept_name:
                    continue
                    
                brand = db.query(Brand).filter(Brand.department == dept_name).first()
                if not brand:
                    brand = Brand(
                        code=generate_code(db, Brand, "PBA"),
                        department=dept_name,
                        is_active=True,
                        created_by=1,
                        updated_by=1
                    )
                    db.add(brand)
                    db.flush()
                
                brand_map[dept_name] = brand
                
                # Find the manager by name
                if manager_name:
                    manager = db.query(Employee).filter(Employee.full_name == manager_name).first()
                    if manager:
                        brand.manager_id = manager.id
                        
            db.commit()
            print("Brands imported/updated successfully.")
            
        # 3. Link Employees to their Departments
        print("Linking Employees to Departments...")
        with open(user_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get('id', '').strip()
                dept_name = row.get('dept', '').strip()
                
                if not code or not dept_name:
                    continue
                    
                emp = db.query(Employee).filter(Employee.code == code).first()
                brand = brand_map.get(dept_name)
                if not brand:
                    brand = db.query(Brand).filter(Brand.department == dept_name).first()
                
                if emp and brand:
                    emp.department_id = brand.id
                    
            db.commit()
            print("Employee to Department linking completed.")
            
        print("All legacy data imported successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during import: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
