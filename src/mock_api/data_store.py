import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

REGIONS = ["North", "South", "East", "West"]
VEHICLE_TYPES = ["van", "truck", "bike", "car"]
ZONES = ["Zone-A", "Zone-B", "Zone-C", "Zone-D", "Zone-E"]

NUM_DRIVERS = 20
NUM_VEHICLES = 15
NUM_LOCATIONS = 12


def _generate_drivers():
    return [
        {
            "driver_id": f"DRV{1000 + i}",
            "name": fake.name(),
            "hire_date": fake.date_between(start_date="-3y", end_date="-30d").isoformat(),
            "region": random.choice(REGIONS),
        }
        for i in range(1, NUM_DRIVERS + 1)
    ]


def _generate_vehicles():
    return [
        {
            "vehicle_id": f"VEH{2000 + i}",
            "type": random.choice(VEHICLE_TYPES),
            "capacity_kg": random.choice([50, 100, 250, 500, 1000]),
        }
        for i in range(1, NUM_VEHICLES + 1)
    ]


def _generate_locations():
    return [
        {
            "location_id": f"LOC{3000 + i}",
            "city": fake.city(),
            "zone": random.choice(ZONES),
            "latitude": float(fake.latitude()),
            "longitude": float(fake.longitude()),
        }
        for i in range(1, NUM_LOCATIONS + 1)
    ]


DRIVERS = _generate_drivers()
VEHICLES = _generate_vehicles()
LOCATIONS = _generate_locations()


def _seeded_random_for_date(seed_str: str) -> random.Random:
    seed = int.from_bytes(seed_str.encode(), "little") % (2**32)
    return random.Random(seed)


def generate_deliveries_for_date(date_str: str, count: int = 200) -> list:
    rnd = _seeded_random_for_date(date_str)
    base_date = datetime.fromisoformat(date_str)
    deliveries = []

    for i in range(1, count + 1):
        driver = rnd.choice(DRIVERS)
        vehicle = rnd.choice(VEHICLES)
        pickup_loc, delivery_loc = rnd.sample(LOCATIONS, 2)

        scheduled_pickup = base_date + timedelta(hours=rnd.randint(6, 10), minutes=rnd.randint(0, 59))
        pickup_delay = rnd.randint(-5, 45)
        actual_pickup = scheduled_pickup + timedelta(minutes=pickup_delay)

        transit_minutes = rnd.randint(30, 240)
        scheduled_delivery = scheduled_pickup + timedelta(minutes=transit_minutes)
        delivery_delay = rnd.choice([0, 0, 0, 5, 10, 15, 30, 45, 60, 90])
        actual_delivery = scheduled_delivery + timedelta(minutes=delivery_delay + pickup_delay)

        status_roll = rnd.random()
        if status_roll < 0.88:
            status = "DELIVERED"
        elif status_roll < 0.94:
            status = "FAILED"
        elif status_roll < 0.98:
            status = "RETURNED"
        else:
            status = "CANCELLED"

        attempts = 1 if (status == "DELIVERED" and delivery_delay < 30) else rnd.randint(1, 3)

        deliveries.append({
            "delivery_id": f"DEL-{date_str}-{i:04d}",
            "driver_id": driver["driver_id"],
            "vehicle_id": vehicle["vehicle_id"],
            "pickup_location_id": pickup_loc["location_id"],
            "delivery_location_id": delivery_loc["location_id"],
            "scheduled_pickup_time": scheduled_pickup.isoformat(),
            "actual_pickup_time": None if status == "CANCELLED" else actual_pickup.isoformat(),
            "scheduled_delivery_time": scheduled_delivery.isoformat(),
            "actual_delivery_time": actual_delivery.isoformat() if status == "DELIVERED" else None,
            "delivery_status": status,
            "delivery_attempts": attempts,
            "distance_km": round(rnd.uniform(2, 60), 1),
        })

    return deliveries


def generate_events_for_deliveries(deliveries: list, date_str: str) -> list:
    rnd = _seeded_random_for_date(date_str + "-events")
    events = []
    counter = 1

    for d in deliveries:
        status = d["delivery_status"]
        timeline = ["ASSIGNED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY"]
        timeline.append(status if status != "DELIVERED" else "DELIVERED")

        base_time = datetime.fromisoformat(d["scheduled_pickup_time"])
        for idx, ev_status in enumerate(timeline):
            events.append({
                "event_id": f"EVT-{date_str}-{counter:05d}",
                "delivery_id": d["delivery_id"],
                "event_timestamp": (base_time + timedelta(minutes=idx * rnd.randint(20, 60))).isoformat(),
                "event_type": "STATUS_CHANGE",
                "location_id": d["pickup_location_id"] if idx < 2 else d["delivery_location_id"],
                "status": ev_status,
            })
            counter += 1

    return events
