from dataclasses import dataclass
from math import cos, hypot, radians, sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models import Area, Tariff
from app.schemas import TariffQuote, TransferQuoteRequest, TransferQuoteResponse

EARTH_RADIUS_M = 6_371_000.0


@dataclass(frozen=True)
class _AreaPrice:
    area: Area
    price: float


def _route_projection(request: TransferQuoteRequest) -> tuple[float, float, float, float, float]:
    """Project route coordinates locally to meters for circle/segment intersections."""
    lat0 = radians((request.start_latitude + request.end_latitude) / 2)
    sx, sy = 0.0, 0.0
    ex = radians(request.end_longitude - request.start_longitude) * EARTH_RADIUS_M * cos(lat0)
    ey = radians(request.end_latitude - request.start_latitude) * EARTH_RADIUS_M
    return sx, sy, ex, ey, lat0


def _area_interval(area: Area, request: TransferQuoteRequest, route: tuple[float, float, float, float, float]) -> tuple[float, float] | None:
    sx, sy, ex, ey, lat0 = route
    cx = radians(area.longitude - request.start_longitude) * EARTH_RADIUS_M * cos(lat0)
    cy = radians(area.latitude - request.start_latitude) * EARTH_RADIUS_M
    dx, dy = ex - sx, ey - sy
    a = dx * dx + dy * dy
    if a < 1e-12:
        return (0.0, 1.0) if hypot(cx, cy) <= area.radius else None
    b = -2 * (cx * dx + cy * dy)
    c = cx * cx + cy * cy - area.radius * area.radius
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return None
    root = sqrt(max(0.0, discriminant))
    low, high = (-b - root) / (2 * a), (-b + root) / (2 * a)
    low, high = max(0.0, low), min(1.0, high)
    return (low, high) if high > low else None


def calculate_quote(db: Session, request: TransferQuoteRequest) -> TransferQuoteResponse:
    route = _route_projection(request)
    sx, sy, ex, ey, _ = route
    distance_m = hypot(ex - sx, ey - sy)
    areas = db.scalars(select(Area).options(joinedload(Area.area_tariffs))).unique().all()

    area_prices: dict[int, list[_AreaPrice]] = {}
    for area in areas:
        for price in area.area_tariffs:
            area_prices.setdefault(price.tariff_id, []).append(_AreaPrice(area, float(price.price_per_km)))

    options: dict[int, list[tuple[float, float]]] = {}
    for tariff_id, prices in area_prices.items():
        boundaries = {0.0, 1.0}
        intervals: list[tuple[float, float, float]] = []
        for area_price in prices:
            interval = _area_interval(area_price.area, request, route)
            if interval:
                low, high = interval
                boundaries.update((low, high))
                intervals.append((low, high, area_price.price))
        ordered = sorted(boundaries)
        segments: list[tuple[float, float]] = []
        available = True
        for low, high in zip(ordered, ordered[1:]):
            if high - low < 1e-12:
                continue
            midpoint = (low + high) / 2
            covering = [price for start, end, price in intervals if start <= midpoint <= end]
            if not covering:
                available = False
                break
            segments.append(((high - low) * distance_m / 1000, max(covering)))
        if available and segments:
            options[tariff_id] = segments

    tariff_ids = list(options)
    tariffs = db.scalars(select(Tariff).where(Tariff.id.in_(tariff_ids))).all() if tariff_ids else []
    tariff_by_id = {tariff.id: tariff for tariff in tariffs}
    quotes = [
        TariffQuote(
            tariff_id=tariff_id,
            tariff_name=tariff_by_id[tariff_id].name,
            calculated_price=round(sum(km * price for km, price in segments), 2),
            currency=settings.currency,
        )
        for tariff_id, segments in options.items()
        if tariff_id in tariff_by_id
    ]
    quotes.sort(key=lambda item: item.tariff_id)
    return TransferQuoteResponse(
        start_datetime=request.start_datetime,
        distance_km=round(distance_m / 1000, 2),
        tariffs=quotes,
    )
