"""Tools that demonstrate reasoning loops — some cause loops, some prevent them.

The key difference: tools WITHOUT clear terminal states cause agents to retry
endlessly. Tools WITH SUCCESS/FAILED states let agents know when to stop.
"""

from strands import tool
import secrets

# ── Tools that CAUSE loops (ambiguous feedback) ─────────────────────

@tool
def search_flights(origin: str, destination: str, max_price: float = 500.0) -> str:
    """Search for flights between cities under a max price.

    Args:
        origin: Departure city
        destination: Arrival city
        max_price: Maximum price in USD
    """
    # Always returns partial results — agent never knows if it found the best deal
    prices = [secrets.randbelow(601) + 200 for _ in range(3)]  # 200-800
    airlines = ["AirLine A", "AirLine B", "AirLine C"]
    results = [f"  {a}: ${p}" for a, p in zip(airlines, prices)]
    matching = [p for p in prices if p <= max_price]

    return (
        f"Found {len(matching)} flights under ${max_price:.0f} "
        f"(out of {len(prices)} checked):\n" + "\n".join(results) +
        "\nNote: More results may be available. Prices change frequently."
    )


@tool
def check_hotel_price(hotel: str, check_in: str) -> str:
    """Check current price for a hotel. Prices fluctuate.

    Args:
        hotel: Hotel name
        check_in: Check-in date
    """
    price = secrets.randbelow(301) + 150  # 150-450
    statuses = ["limited availability", "selling fast", "few rooms left"]
    status = statuses[secrets.randbelow(len(statuses))]
    return f"{hotel}: ${price}/night ({status}) for {check_in}. Prices may change — check again for latest."


# ── Tools that PREVENT loops (clear terminal states) ────────────────

@tool
def book_flight(flight: str, passenger: str) -> str:
    """Book a flight for a passenger. Returns clear SUCCESS or FAILED.

    Args:
        flight: Flight description
        passenger: Passenger name
    """
    if secrets.randbelow(100) >= 20:  # 80% success rate
        conf = f"FL{secrets.randbelow(90000) + 10000}"  # 10000-99999
        return f"SUCCESS: Flight booked. Confirmation {conf} for {passenger} on {flight}"
    return f"FAILED: No seats available on {flight}"


@tool
def book_hotel(hotel: str, guest: str, nights: int = 1) -> str:
    """Book a hotel room. Returns clear SUCCESS or FAILED.

    Args:
        hotel: Hotel name
        guest: Guest name
        nights: Number of nights
    """
    if secrets.randbelow(100) >= 15:  # 85% success rate
        conf = f"HT{secrets.randbelow(90000) + 10000}"  # 10000-99999
        price = secrets.randbelow(201) + 150  # 150-350
        return f"SUCCESS: Booking {conf} confirmed — {guest} at {hotel}, {nights} nights, ${price * nights} total"
    return f"FAILED: {hotel} fully booked"
