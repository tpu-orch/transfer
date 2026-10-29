from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TransferQuoteRequest(BaseModel):
    start_datetime: datetime
    start_latitude: float = Field(ge=-90, le=90)
    start_longitude: float = Field(ge=-180, le=180)
    end_latitude: float = Field(ge=-90, le=90)
    end_longitude: float = Field(ge=-180, le=180)


class TariffQuote(BaseModel):
    tariff_id: int
    tariff_name: str
    calculated_price: float
    currency: str


class TransferQuoteResponse(BaseModel):
    start_datetime: datetime
    distance_km: float
    tariffs: list[TariffQuote]


class TransferBookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking_id: int = Field(validation_alias="id")
    tariff_id: int
    tariff_name: str
    start_datetime: datetime
    start_latitude: float
    start_longitude: float
    end_latitude: float
    end_longitude: float
    calculated_price: float
    currency: str
    booking_status: str
    created_at: datetime
