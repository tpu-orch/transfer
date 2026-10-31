from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Booking
from app.schemas import TransferBookingResponse, TransferQuoteRequest, TransferQuoteResponse
from app.services.quotes import calculate_quote


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema is managed by db/init SQL scripts for the local Docker PostgreSQL.
    yield


app = FastAPI(title="Transfer Service", version="1.0.0", lifespan=lifespan)


@app.post("/transfers/quote", response_model=TransferQuoteResponse, tags=["Transfers"])
def get_transfer_quote(request: TransferQuoteRequest, db: Session = Depends(get_db)):
    request_timezone = request.start_datetime.tzinfo
    today = datetime.now(request_timezone).date() if request_timezone else datetime.now().date()
    if request.start_datetime.date() < today:
        raise HTTPException(status_code=400, detail="Дата поездки не может быть раньше текущей даты")
    return calculate_quote(db, request)


@app.get("/transfers/bookings/{booking_id}", response_model=TransferBookingResponse, tags=["Bookings"])
def get_transfer_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.scalar(
        select(Booking)
        .options(joinedload(Booking.tariff))
        .where(Booking.id == booking_id)
    )
    if booking is None:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    return TransferBookingResponse(
        booking_id=booking.id,
        tariff_id=booking.tariff_id,
        tariff_name=booking.tariff.name,
        start_datetime=booking.start_datetime,
        start_latitude=booking.start_latitude,
        start_longitude=booking.start_longitude,
        end_latitude=booking.end_latitude,
        end_longitude=booking.end_longitude,
        calculated_price=float(booking.calculated_price),
        currency=booking.currency,
        booking_status=booking.booking_status,
        created_at=booking.created_at,
    )
