import json
import logging
from datetime import datetime

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.schemas import TransferQuoteRequest
from app.core.config import settings
from app.db.models import Booking, Tariff
from app.db.session import SessionLocal
from app.services.quotes import calculate_quote

logger = logging.getLogger(__name__)


class BookCommand(BaseModel):
    compositeBookingId: int
    tariff_id: int
    start_datetime: datetime
    start_latitude: float = Field(ge=-90, le=90)
    start_longitude: float = Field(ge=-180, le=180)
    end_latitude: float = Field(ge=-90, le=90)
    end_longitude: float = Field(ge=-180, le=180)


class CancelCommand(BaseModel):
    compositeBookingId: int
    bookingId: int


def _booking_result(command: BookCommand) -> dict:
    with SessionLocal() as db:
        prior = db.scalar(select(Booking).options(joinedload(Booking.tariff)).where(
            Booking.composite_booking_id == command.compositeBookingId))
        if prior:
            return {"compositeBookingId": command.compositeBookingId, "bookingId": prior.id,
                    "tariff_id": prior.tariff_id, "start_datetime": prior.start_datetime.isoformat(),
                    "calculated_price": float(prior.calculated_price), "bookingStatus": prior.booking_status,
                    "created_at": prior.created_at.isoformat() if prior.created_at else None}

        result = {"compositeBookingId": command.compositeBookingId, "bookingId": 0,
                  "tariff_id": command.tariff_id, "start_datetime": command.start_datetime.isoformat(),
                  "calculated_price": 0.0, "bookingStatus": "REJECTED"}
        tariff = db.get(Tariff, command.tariff_id)
        if tariff is None:
            result["rejectionReason"] = "Тариф не найден"
            return result
        request = TransferQuoteRequest(**command.model_dump(exclude={"compositeBookingId", "tariff_id"}))
        quote = calculate_quote(db, request)
        selected = next((item for item in quote.tariffs if item.tariff_id == command.tariff_id), None)
        if selected is None:
            result["rejectionReason"] = "Тариф недоступен для всего маршрута"
            return result
        booking = Booking(tariff_id=command.tariff_id, composite_booking_id=command.compositeBookingId,
                          start_datetime=command.start_datetime, start_latitude=command.start_latitude,
                          start_longitude=command.start_longitude, end_latitude=command.end_latitude,
                          end_longitude=command.end_longitude, calculated_price=selected.calculated_price,
                          currency=selected.currency, booking_status="CONFIRMED")
        db.add(booking)
        db.commit()
        db.refresh(booking)
        result.update(bookingId=booking.id, calculated_price=float(booking.calculated_price),
                      bookingStatus="CONFIRMED", created_at=booking.created_at.isoformat())
        return result


def _cancellation_result(command: CancelCommand) -> dict:
    result = {"compositeBookingId": command.compositeBookingId, "bookingId": command.bookingId,
              "cancellationStatus": "REJECTED"}
    with SessionLocal() as db:
        booking = db.get(Booking, command.bookingId)
        if booking is None:
            result["rejectionReason"] = "Бронирование не найдено"
        elif booking.composite_booking_id != command.compositeBookingId:
            result["rejectionReason"] = "Идентификатор общей операции не совпадает"
        elif booking.booking_status != "CONFIRMED":
            result["rejectionReason"] = "Отменить можно только подтвержденное бронирование"
        else:
            booking.booking_status = "CANCELLED"
            db.commit()
            result["cancellationStatus"] = "CANCELLED"
    return result


async def run_kafka_worker() -> None:
    security = {"security_protocol": settings.kafka_security_protocol}
    if settings.kafka_sasl_mechanism:
        security.update(sasl_mechanism=settings.kafka_sasl_mechanism,
                        sasl_plain_username=settings.kafka_sasl_username,
                        sasl_plain_password=settings.kafka_sasl_password)
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        request_timeout_ms=15000,
        max_request_size=1048576,
        **security
    )
    consumer = AIOKafkaConsumer(settings.kafka_booking_topic, settings.kafka_cancel_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers, group_id=settings.kafka_group_id,
        enable_auto_commit=False, **security)
    await producer.start()
    await consumer.start()
    try:
        async for message in consumer:
            try:
                payload = json.loads(message.value)
                if message.topic == settings.kafka_booking_topic:
                    result = _booking_result(BookCommand.model_validate(payload))
                    topic = settings.kafka_status_topic
                else:
                    result = _cancellation_result(CancelCommand.model_validate(payload))
                    topic = settings.kafka_cancellation_result_topic
                await producer.send_and_wait(topic, json.dumps(result).encode())
                await consumer.commit()
            except (ValidationError, ValueError, TypeError) as exc:
                logger.error("Dropping invalid Kafka message from %s: %s", message.topic, exc)
                await consumer.commit()
            except Exception:
                logger.exception("Kafka message processing failed; it will be retried")
    finally:
        await consumer.stop()
        await producer.stop()
