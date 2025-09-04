from langchain_core.tools import tool
from typing import Dict, List, Any
import json
import random
from datetime import datetime, timedelta

# Mock travel data
MOCK_FLIGHTS = [
    {
        "flight_id": "AA123",
        "airline": "American Airlines",
        "departure": "2025-09-15 09:00",
        "arrival": "2025-09-15 12:30",
        "price": 299.99,
        "route": "NYC-LAX"
    },
    {
        "flight_id": "UA456", 
        "airline": "United Airlines",
        "departure": "2025-09-15 14:00",
        "arrival": "2025-09-15 17:45",
        "price": 325.50,
        "route": "NYC-LAX"
    }
]

MOCK_HOTELS = [
    {
        "hotel_id": "HTL001",
        "name": "Grand Plaza Hotel",
        "location": "Downtown NYC",
        "price_per_night": 250.00,
        "rating": 4.5,
        "amenities": ["wifi", "gym", "pool", "business_center"]
    },
    {
        "hotel_id": "HTL002",
        "name": "Budget Inn Express",
        "location": "Midtown NYC", 
        "price_per_night": 120.00,
        "rating": 3.8,
        "amenities": ["wifi", "continental_breakfast"]
    }
]

@tool
def search_flights(destination: str, departure_date: str, return_date: str = None) -> str:
    """
    Search for available flights to a destination.
    
    Args:
        destination: Destination city or airport code
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Optional return date for round trip
        
    Returns:
        JSON string with flight options
    """
    # Filter flights based on destination
    available_flights = [f for f in MOCK_FLIGHTS if destination.upper() in f["route"]]
    
    return json.dumps({
        "destination": destination,
        "departure_date": departure_date,
        "return_date": return_date,
        "flights": available_flights,
        "search_timestamp": datetime.now().isoformat()
    })

@tool 
def search_hotels(location: str, check_in: str, check_out: str, guests: int = 1) -> str:
    """
    Search for hotel accommodations in a specific location.
    
    Args:
        location: City or area to search for hotels
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format  
        guests: Number of guests
        
    Returns:
        JSON string with hotel options
    """
    # Calculate stay duration
    checkin_date = datetime.strptime(check_in, "%Y-%m-%d")
    checkout_date = datetime.strptime(check_out, "%Y-%m-%d")
    nights = (checkout_date - checkin_date).days
    
    # Filter hotels by location
    available_hotels = [h for h in MOCK_HOTELS if location.upper() in h["location"].upper()]
    
    # Add total cost calculation
    for hotel in available_hotels:
        hotel["total_cost"] = hotel["price_per_night"] * nights
        hotel["nights"] = nights
    
    return json.dumps({
        "location": location,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "guests": guests,
        "hotels": available_hotels
    })

@tool
def book_hotel(hotel_id: str, check_in: str, check_out: str, guest_name: str) -> str:
    """
    Book a hotel room. REQUIRES USER CONFIRMATION.
    
    Args:
        hotel_id: Hotel identifier from search results
        check_in: Check-in date
        check_out: Check-out date
        guest_name: Name for the reservation
        
    Returns:
        JSON string with booking confirmation
    """
    # Find hotel details
    hotel = next((h for h in MOCK_HOTELS if h["hotel_id"] == hotel_id), None)
    
    if not hotel:
        return json.dumps({"error": "Hotel not found", "hotel_id": hotel_id})
    
    # Generate booking confirmation
    confirmation_code = f"BK{random.randint(100000, 999999)}"
    
    return json.dumps({
        "status": "confirmed",
        "confirmation_code": confirmation_code,
        "hotel_name": hotel["name"],
        "guest_name": guest_name,
        "check_in": check_in,
        "check_out": check_out,
        "total_cost": hotel.get("total_cost", hotel["price_per_night"]),
        "booking_timestamp": datetime.now().isoformat()
    })

# Travel tools collection
travel_tools = [search_flights, search_hotels, book_hotel]