from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Area(Base):
    __tablename__ = "areas"
    __table_args__ = (CheckConstraint("latitude BETWEEN -90 AND 90"), CheckConstraint("longitude BETWEEN -180 AND 180"), CheckConstraint("radius > 0"))

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius: Mapped[float] = mapped_column(Float, nullable=False)
    area_tariffs: Mapped[list["AreaTariff"]] = relationship(back_populates="area")


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    area_tariffs: Mapped[list["AreaTariff"]] = relationship(back_populates="tariff")


class AreaTariff(Base):
    __tablename__ = "area_tariffs"
    __table_args__ = (UniqueConstraint("area_id", "tariff_id", name="uq_area_tariff"), CheckConstraint("price_per_km >= 0"))

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id", ondelete="CASCADE"), nullable=False)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id", ondelete="CASCADE"), nullable=False)
    price_per_km: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    area: Mapped[Area] = relationship(back_populates="area_tariffs")
    tariff: Mapped[Tariff] = relationship(back_populates="area_tariffs")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (CheckConstraint("booking_status IN ('PENDING', 'CONFIRMED', 'REJECTED', 'CANCELLED')"), CheckConstraint("calculated_price >= 0"))

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id"), nullable=False)
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    start_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    end_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    end_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    calculated_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    booking_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    tariff: Mapped[Tariff] = relationship()
