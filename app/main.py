from contextlib import asynccontextmanager
from datetime import datetime
import asyncio
import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.schemas import TransferBookingResponse, TransferQuoteRequest, TransferQuoteResponse
from app.core.config import settings
from app.db.models import Booking
from app.db.session import get_db
from app.messaging.kafka_worker import run_kafka_worker
from app.services.quotes import calculate_quote

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    worker = asyncio.create_task(run_kafka_worker()) if settings.kafka_enabled else None
    yield
    if worker:
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Transfer Service", version="2.0.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": exc.errors()})


@app.post("/transfers/quote", response_model=TransferQuoteResponse, tags=["Transfers"])
def get_transfer_quote(request: TransferQuoteRequest, db: Session = Depends(get_db)):
    request_timezone = request.start_datetime.tzinfo
    today = datetime.now(request_timezone).date() if request_timezone else datetime.now().date()
    if request.start_datetime.date() < today:
        raise HTTPException(status_code=400, detail="Дата поездки не может быть раньше текущей даты")
    return calculate_quote(db, request)


@app.get("/transfers/bookings/{booking_id}", response_model=TransferBookingResponse, tags=["Bookings"])
def get_transfer_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.scalar(select(Booking).options(joinedload(Booking.tariff)).where(Booking.id == booking_id))
    if booking is None:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    return TransferBookingResponse(booking_id=booking.id, tariff_id=booking.tariff_id,
        tariff_name=booking.tariff.name, start_datetime=booking.start_datetime,
        start_latitude=booking.start_latitude, start_longitude=booking.start_longitude,
        end_latitude=booking.end_latitude, end_longitude=booking.end_longitude,
        calculated_price=float(booking.calculated_price), currency=booking.currency,
        booking_status=booking.booking_status, created_at=booking.created_at)
