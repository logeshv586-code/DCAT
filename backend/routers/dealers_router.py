from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Account, Dealership
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["dealers"])


@router.get("/accounts/{account_id}/dealers")
def list_dealers(account_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    acct = db.query(Account).get(account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found")

    dealers = (
        db.query(Dealership)
        .filter(Dealership.account_id == account_id)
        .order_by(Dealership.name)
        .all()
    )

    return [
        {"id": d.id, "name": d.name, "folder_name": d.folder_name}
        for d in dealers
    ]
