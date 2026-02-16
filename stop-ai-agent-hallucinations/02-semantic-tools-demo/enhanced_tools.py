"""
Enhanced Travel Agent Tools
Combines mock tools with real hotel database access
"""
import os
import sys
sys.path.append('../01-hotel-rag-demo/tools')

from strands import tool
from graph_tool import search_hotels_by_country, get_top_rated_hotels

# Configure Neo4j
os.environ['NEO4J_URI'] = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
os.environ['NEO4J_USER'] = os.getenv('NEO4J_USER', 'neo4j')
os.environ['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD', 'Eli12345678')

# ============================================================================
# HOTEL TOOLS (Real Database + Mock)
# ============================================================================

@tool
def search_real_hotels(country: str, min_rating: float = 0.0) -> str:
    """Search real hotels in a specific country from our database."""
    try:
        results = search_hotels_by_country(country, min_rating)
        return results
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_top_hotels(limit: int = 5) -> str:
    """Get the top-rated hotels from our database."""
    try:
        results = get_top_rated_hotels(limit)
        return results
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def search_hotels(query: str) -> str:
    """Search hotels by location or name."""
    return f"Hotels found for: {query}"

@tool
def search_hotel_reviews(hotel: str) -> str:
    """Search reviews for a hotel."""
    return f"Reviews for {hotel}: 4.5 stars"

@tool
def get_hotel_details(hotel: str) -> str:
    """Get hotel details like amenities and price."""
    return f"{hotel}: Pool, Spa, $200/night"

@tool
def get_hotel_pricing(hotel: str) -> str:
    """Get room pricing for a hotel."""
    return f"{hotel}: $200-400/night"

@tool
def check_hotel_availability(hotel: str, date: str) -> str:
    """Check if hotel has rooms on a date."""
    return f"{hotel} available on {date}"

@tool
def book_hotel(hotel: str, guest: str) -> str:
    """Book a hotel room."""
    return f"BOOKED {hotel} for {guest}"

@tool
def check_hotel_availability_dates(hotel_name: str, check_in: str, check_out: str) -> str:
    """Check real-time hotel room availability for specific dates."""
    import secrets
    from datetime import datetime
    
    try:
        checkin_date = datetime.strptime(check_in, '%Y-%m-%d')
        checkout_date = datetime.strptime(check_out, '%Y-%m-%d')
        nights = (checkout_date - checkin_date).days
        
        if nights <= 0:
            return f"Error: Check-out must be after check-in"
        
        available = secrets.randbelow(10) > 3
        rooms_left = secrets.randbelow(8) + 1 if available else 0
        
        if available:
            price_per_night = secrets.randbelow(251) + 150
            total = price_per_night * nights
            return f"{hotel_name}: AVAILABLE - {rooms_left} rooms left, ${price_per_night}/night, Total: ${total} for {nights} nights"
        else:
            return f"{hotel_name}: SOLD OUT for {check_in} to {check_out}"
    except ValueError:
        return "Error: Use date format YYYY-MM-DD"

@tool
def compare_hotel_prices(city: str, check_in: str, check_out: str) -> str:
    """Compare prices across multiple hotels in a city for specific dates."""
    import secrets
    
    hotels = ["Hotel Marriott", "Hilton Downtown", "Radisson Blu"]
    results = []
    for hotel in hotels:
        price = secrets.randbelow(231) + 120
        rating = round((secrets.randbelow(16) + 80) / 10, 1)
        results.append(f"{hotel}: ${price}/night (Rating: {rating}/10)")
    
    return f"Price comparison for {city} ({check_in} to {check_out}):\n" + "\n".join(results)

# ============================================================================
# FLIGHT TOOLS (Mock)
# ============================================================================

@tool
def search_flights(origin: str, dest: str) -> str:
    """Search flights between cities."""
    return f"Flights {origin}-{dest}: $300-500"

@tool
def search_flight_prices(origin: str, dest: str) -> str:
    """Get flight prices between cities."""
    return f"Prices {origin}-{dest}: $300-500"

@tool
def get_flight_details(flight: str) -> str:
    """Get details of a specific flight."""
    return f"Flight {flight}: Boeing 737, 3h"

@tool
def get_flight_status(flight: str) -> str:
    """Get real-time flight status."""
    return f"Flight {flight}: On time, Gate B4"

@tool
def check_flight_availability(flight: str) -> str:
    """Check seats available on a flight."""
    return f"Flight {flight}: 23 seats left"

@tool
def book_flight(flight: str, passenger: str) -> str:
    """Book a flight."""
    return f"BOOKED {flight} for {passenger}"

# ============================================================================
# WEATHER TOOLS (Mock)
# ============================================================================

@tool
def get_weather(city: str) -> str:
    """Get current weather."""
    return f"{city}: 22°C, Sunny"

@tool
def get_weather_forecast(city: str) -> str:
    """Get weather forecast."""
    return f"{city} forecast: 22°C today, 20°C tomorrow"

@tool
def get_weather_alerts(city: str) -> str:
    """Get weather alerts."""
    return f"{city}: No alerts"

# ============================================================================
# PAYMENT TOOLS (Mock)
# ============================================================================

@tool
def process_payment(amount: float) -> str:
    """Process a payment."""
    return f"PAID ${amount}"

@tool
def check_payment(transaction_id: str) -> str:
    """Check payment status."""
    return f"Transaction {transaction_id}: Complete"

@tool
def refund_payment(transaction_id: str) -> str:
    """Refund a payment."""
    return f"REFUNDED {transaction_id}"

# ============================================================================
# TRAVEL UTILITY TOOLS
# ============================================================================

@tool
def get_currency_exchange(from_currency: str, to_currency: str, amount: float) -> str:
    """Convert currency for international travel."""
    rates = {
        ('USD', 'EUR'): 0.92,
        ('EUR', 'USD'): 1.09,
        ('USD', 'GBP'): 0.79,
        ('GBP', 'USD'): 1.27,
        ('EUR', 'GBP'): 0.86,
        ('GBP', 'EUR'): 1.16,
    }
    rate = rates.get((from_currency, to_currency), 1.0)
    converted = amount * rate
    return f"{amount} {from_currency} = {converted:.2f} {to_currency} (rate: {rate})"

@tool
def get_travel_documents(destination_country: str, origin_country: str) -> str:
    """Get visa and travel document requirements."""
    if destination_country in ['France', 'Spain', 'Italy', 'Netherlands']:
        if origin_country == 'USA':
            return f"US citizens can visit {destination_country} visa-free for up to 90 days (Schengen). Valid passport required."
    return f"Check embassy website for {destination_country} visa requirements from {origin_country}."

# ============================================================================
# GENERIC/AMBIGUOUS TOOLS (High confusion risk)
# ============================================================================

@tool
def search(query: str) -> str:
    """Generic search."""
    return f"Results for: {query}"

@tool
def check(item: str) -> str:
    """Generic check."""
    return f"Checked: {item}"

@tool
def get_details(item: str) -> str:
    """Get details of anything."""
    return f"Details: {item}"

@tool
def get_status(item: str) -> str:
    """Get status of anything."""
    return f"Status: {item} OK"

@tool
def get_info(item: str) -> str:
    """Get info about anything."""
    return f"Info: {item}"

@tool
def book(item: str, name: str) -> str:
    """Book anything."""
    return f"BOOKED {item} for {name}"

@tool
def cancel(item: str) -> str:
    """Cancel anything."""
    return f"CANCELLED {item}"

# ============================================================================
# ALL TOOLS COLLECTION
# ============================================================================

ALL_TOOLS = [
    # Real database tools
    search_real_hotels, get_top_hotels,
    
    # Hotel tools (mock)
    search_hotels, search_hotel_reviews, get_hotel_details, get_hotel_pricing, 
    check_hotel_availability, book_hotel, check_hotel_availability_dates, compare_hotel_prices,
    
    # Flight tools
    search_flights, search_flight_prices, get_flight_details, get_flight_status, 
    check_flight_availability, book_flight,
    
    # Weather tools
    get_weather, get_weather_forecast, get_weather_alerts,
    
    # Payment tools
    process_payment, check_payment, refund_payment,
    
    # Travel utilities
    get_currency_exchange, get_travel_documents,
    
    # Generic/ambiguous tools
    search, check, get_details, get_status, get_info, book, cancel
]
