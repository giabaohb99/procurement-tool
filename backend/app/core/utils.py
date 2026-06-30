from sqlalchemy.orm import Session

def generate_code(db: Session, model, prefix: str) -> str:
    """Generate a sequential code with a given prefix (e.g. CTY001)."""
    last_obj = db.query(model).filter(model.code.like(f"{prefix}%")).order_by(model.code.desc()).first()
    if not last_obj or not last_obj.code.startswith(prefix):
        return f"{prefix}001"
    
    try:
        num = int(last_obj.code[len(prefix):]) + 1
        return f"{prefix}{num:03d}"
    except ValueError:
        return f"{prefix}001"
