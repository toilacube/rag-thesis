

from fastapi import APIRouter, HTTPException


router = APIRouter()

@router.post("/login")
async def login():
    return {"message": "Login successful"}

@router.get("/logout")
async def logout():
    raise HTTPException(status_code = 401, detail = "Unauthorized")