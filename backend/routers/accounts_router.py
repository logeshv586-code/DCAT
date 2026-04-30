from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Account
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["accounts"])


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(Account).order_by(Account.name).all()
    return [
        {"id": a.id, "name": a.name, "slug": a.slug}
        for a in rows
    ]
