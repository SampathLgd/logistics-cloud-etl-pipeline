import os
import random
import logging

from fastapi import FastAPI, HTTPException, Query

from . import data_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_logistics_api")

app = FastAPI(title="Mock Logistics API")

FAILURE_RATE = float(os.getenv("MOCK_API_FAILURE_RATE", "0.05"))


def maybe_fail():
    if random.random() < FAILURE_RATE:
        logger.warning("Simulated API failure triggered")
        raise HTTPException(status_code=503, detail="Simulated upstream failure")


def paginate(items: list, page: int, page_size: int) -> dict:
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total_items": len(items),
        "total_pages": max(1, (len(items) + page_size - 1) // page_size),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/drivers")
def get_drivers(page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500)):
    maybe_fail()
    return paginate(data_store.DRIVERS, page, page_size)


@app.get("/vehicles")
def get_vehicles(page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500)):
    maybe_fail()
    return paginate(data_store.VEHICLES, page, page_size)


@app.get("/locations")
def get_locations(page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500)):
    maybe_fail()
    return paginate(data_store.LOCATIONS, page, page_size)


@app.get("/deliveries")
def get_deliveries(date: str = Query(...), page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500)):
    maybe_fail()
    deliveries = data_store.generate_deliveries_for_date(date)
    return paginate(deliveries, page, page_size)


@app.get("/delivery_events")
def get_delivery_events(date: str = Query(...), page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500)):
    maybe_fail()
    deliveries = data_store.generate_deliveries_for_date(date)
    events = data_store.generate_events_for_deliveries(deliveries, date)
    return paginate(events, page, page_size)
