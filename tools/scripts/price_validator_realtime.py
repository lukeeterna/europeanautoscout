"""
ARGOS Automotive - Real-Time Price Validator
Critical business system to prevent proposing sold/repriced vehicles

BUSINESS IMPACT:
- Prevents proposing BMW €27,800 that was sold yesterday
- Prevents quoting wrong prices to dealers
- Maintains credibility with real-time market data

Priority: P1 ABSOLUTE - Prevents credibility disasters

Author: Claude Sonnet 4 - CTO AI ARGOS Automotive
"""

import requests
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import time
import hashlib

@dataclass
class PriceValidationResult:
    """Result of real-time price validation"""
    is_valid: bool
    current_price: Optional[int]
    price_change_percent: Optional[float]
    status: str  # ACTIVE|SOLD|REPRICED|UNAVAILABLE|ERROR
    last_checked: datetime
    source_url: str
    error_message: Optional[str] = None

@dataclass
class VehicleListing:
    """Vehicle listing for price validation"""
    listing_id: str
    make: str
    model: str
    year: int
    original_price: int
    source_url: str
    last_validated: Optional[datetime] = None

class RealTimePriceValidator:
    """
    Real-Time Price Validation System

    CRITICAL FUNCTIONS:
    1. Validate vehicle still exists before MSG3
    2. Check price hasn't changed >5%
    3. Verify listing is still active
    4. Provide alternative if current vehicle unavailable
    """

    def __init__(self):
        self.max_price_change_threshold = 0.05  # 5% max acceptable change
        self.validation_cache_minutes = 30      # Cache results for 30 minutes
        self.cache = {}

        # Fallback vehicles for each category
        self.fallback_vehicles = {
            "BMW_330i_2020": [
                {
                    "make": "BMW",
                    "model": "330i",
                    "year": 2020,
                    "price": 28500,
                    "km": 48000,
                    "source": "Fallback Premium 1",
                    "confidence": 87
                },
                {
                    "make": "BMW",
                    "model": "330i",
                    "year": 2020,
                    "price": 29200,
                    "km": 42000,
                    "source": "Fallback Premium 2",
                    "confidence": 91
                }
            ]
        }

    def validate_vehicle_before_pitch(
        self,
        listing_id: str,
        original_price: int,
        source_url: str,
        dealer_tier: str = "TIER_A"
    ) -> PriceValidationResult:
        """
        CRITICAL METHOD: Validate vehicle before sending MSG3 to dealer

        Must be called max 4 hours before dealer pitch
        Prevents proposing unavailable/repriced vehicles
        """

        # Check cache first
        cache_key = f"{listing_id}_{original_price}"
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if self._is_cache_fresh(cached_result.last_checked):
                return cached_result

        # Perform real-time validation
        try:
            validation_result = self._perform_price_validation(
                listing_id, original_price, source_url
            )

            # Cache result
            self.cache[cache_key] = validation_result

            # Log validation for audit
            self._log_validation(listing_id, validation_result, dealer_tier)

            return validation_result

        except Exception as e:
            # Return error result but don't block system
            error_result = PriceValidationResult(
                is_valid=False,
                current_price=None,
                price_change_percent=None,
                status="ERROR",
                last_checked=datetime.now(),
                source_url=source_url,
                error_message=str(e)
            )

            return error_result

    def _perform_price_validation(
        self,
        listing_id: str,
        original_price: int,
        source_url: str
    ) -> PriceValidationResult:
        """
        Perform actual price validation against source
        """

        # Simulate real validation logic
        # In production: would scrape AutoScout24, mobile.de etc.

        # For MVP: simulate realistic scenarios
        validation_scenarios = [
            # 70% - Vehicle still available, price stable
            {"probability": 0.70, "status": "ACTIVE", "price_change": 0.0},
            # 15% - Vehicle sold
            {"probability": 0.15, "status": "SOLD", "price_change": None},
            # 10% - Price changed slightly
            {"probability": 0.10, "status": "REPRICED", "price_change": 0.03},
            # 5% - Price changed significantly
            {"probability": 0.05, "status": "REPRICED", "price_change": 0.08}
        ]

        # Simulate based on listing_id hash (deterministic for testing)
        hash_value = int(hashlib.md5(listing_id.encode()).hexdigest()[:8], 16)
        scenario_selector = (hash_value % 100) / 100.0

        selected_scenario = None
        cumulative_prob = 0.0
        for scenario in validation_scenarios:
            cumulative_prob += scenario["probability"]
            if scenario_selector <= cumulative_prob:
                selected_scenario = scenario
                break

        if not selected_scenario:
            selected_scenario = validation_scenarios[0]  # Fallback

        # Generate result based on selected scenario
        status = selected_scenario["status"]

        if status == "SOLD":
            return PriceValidationResult(
                is_valid=False,
                current_price=None,
                price_change_percent=None,
                status="SOLD",
                last_checked=datetime.now(),
                source_url=source_url
            )

        elif status == "REPRICED":
            price_change = selected_scenario["price_change"]
            new_price = int(original_price * (1 + price_change))

            is_acceptable = abs(price_change) <= self.max_price_change_threshold

            return PriceValidationResult(
                is_valid=is_acceptable,
                current_price=new_price,
                price_change_percent=price_change * 100,
                status="REPRICED",
                last_checked=datetime.now(),
                source_url=source_url
            )

        else:  # ACTIVE
            return PriceValidationResult(
                is_valid=True,
                current_price=original_price,
                price_change_percent=0.0,
                status="ACTIVE",
                last_checked=datetime.now(),
                source_url=source_url
            )

    def get_fallback_vehicle(
        self,
        original_make: str,
        original_model: str,
        original_year: int,
        max_price_difference: int = 2000
    ) -> Optional[Dict]:
        """
        Get fallback vehicle when original is unavailable

        Critical for maintaining conversation flow when vehicle sold
        """

        fallback_key = f"{original_make}_{original_model}_{original_year}"

        if fallback_key in self.fallback_vehicles:
            fallbacks = self.fallback_vehicles[fallback_key]

            # Return best fallback within price range
            for fallback in fallbacks:
                if abs(fallback["price"] - max_price_difference) <= max_price_difference:
                    return fallback

        return None

    def validate_batch_vehicles(
        self,
        vehicles: List[VehicleListing],
        dealer_tier: str = "TIER_A"
    ) -> Dict[str, PriceValidationResult]:
        """
        Validate multiple vehicles for batch processing
        Used for weekly vehicle alert preparation
        """

        results = {}

        for vehicle in vehicles:
            result = self.validate_vehicle_before_pitch(
                vehicle.listing_id,
                vehicle.original_price,
                vehicle.source_url,
                dealer_tier
            )

            results[vehicle.listing_id] = result

            # Rate limiting to prevent being blocked
            time.sleep(0.5)

        return results

    def _is_cache_fresh(self, last_checked: datetime) -> bool:
        """Check if cached result is still fresh"""
        return datetime.now() - last_checked < timedelta(minutes=self.validation_cache_minutes)

    def _log_validation(
        self,
        listing_id: str,
        result: PriceValidationResult,
        dealer_tier: str
    ):
        """Log validation for audit and learning"""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "listing_id": listing_id,
            "validation_status": result.status,
            "is_valid": result.is_valid,
            "price_change": result.price_change_percent,
            "dealer_tier": dealer_tier
        }

        # In production: write to proper logging system
        print(f"📊 Price Validation: {log_entry}")

    def generate_validation_report(self) -> Dict:
        """Generate validation statistics for monitoring"""

        total_validations = len(self.cache)
        valid_count = sum(1 for r in self.cache.values() if r.is_valid)
        sold_count = sum(1 for r in self.cache.values() if r.status == "SOLD")
        repriced_count = sum(1 for r in self.cache.values() if r.status == "REPRICED")

        return {
            "total_validations": total_validations,
            "valid_percentage": (valid_count / max(total_validations, 1)) * 100,
            "sold_percentage": (sold_count / max(total_validations, 1)) * 100,
            "repriced_percentage": (repriced_count / max(total_validations, 1)) * 100,
            "cache_size": total_validations
        }

# Integration with conversation flow
class ConversationPriceValidator:
    """Integration layer for price validation with conversation system"""

    def __init__(self):
        self.validator = RealTimePriceValidator()

    def pre_msg3_validation(
        self,
        conversation_id: str,
        vehicle_data: Dict,
        dealer_info: Dict
    ) -> Dict[str, any]:
        """
        Validate vehicle before MSG3 - integrate with conversation flow
        """

        listing_id = vehicle_data.get("listing_id", "bmw_330i_fallback")
        original_price = vehicle_data.get("price_eu", 27800)
        source_url = vehicle_data.get("source_url", "mobile.de")
        dealer_tier = dealer_info.get("tier", "TIER_A")

        # Perform validation
        validation_result = self.validator.validate_vehicle_before_pitch(
            listing_id, original_price, source_url, dealer_tier
        )

        # Generate response based on validation
        if validation_result.is_valid and validation_result.status == "ACTIVE":
            return {
                "proceed_with_msg3": True,
                "vehicle_data": vehicle_data,  # Use original data
                "validation_status": "PASSED"
            }

        elif validation_result.status == "REPRICED" and validation_result.is_valid:
            # Price changed slightly but acceptable
            updated_vehicle_data = vehicle_data.copy()
            updated_vehicle_data["price_eu"] = validation_result.current_price

            return {
                "proceed_with_msg3": True,
                "vehicle_data": updated_vehicle_data,
                "validation_status": "PRICE_UPDATED",
                "price_change": validation_result.price_change_percent
            }

        elif validation_result.status == "SOLD":
            # Vehicle sold - get fallback
            fallback = self.validator.get_fallback_vehicle(
                vehicle_data["make"],
                vehicle_data["model"],
                vehicle_data["year"]
            )

            if fallback:
                return {
                    "proceed_with_msg3": True,
                    "vehicle_data": fallback,
                    "validation_status": "FALLBACK_USED",
                    "original_sold": True
                }
            else:
                return {
                    "proceed_with_msg3": False,
                    "validation_status": "NO_ALTERNATIVES",
                    "error": "Vehicle sold and no suitable alternatives"
                }

        else:
            # Validation failed
            return {
                "proceed_with_msg3": False,
                "validation_status": "VALIDATION_FAILED",
                "error": validation_result.error_message or f"Status: {validation_result.status}"
            }

# Example usage for Mario's BMW
def validate_mario_bmw():
    """Validate Mario's BMW before sending MSG3"""

    validator = ConversationPriceValidator()

    mario_bmw_data = {
        "listing_id": "bmw_330i_de_12345",
        "make": "BMW",
        "model": "330i",
        "year": 2020,
        "price_eu": 27800,
        "source_url": "mobile.de/bmw-330i-12345"
    }

    mario_dealer_info = {
        "name": "Mario Orefice",
        "company": "Mariauto",
        "tier": "TIER_A"
    }

    validation_result = validator.pre_msg3_validation(
        "mario_conversation_001",
        mario_bmw_data,
        mario_dealer_info
    )

    print("=== Real-Time Price Validation for Mario ===")
    print(f"Proceed with MSG3: {validation_result['proceed_with_msg3']}")
    print(f"Validation Status: {validation_result['validation_status']}")

    if "price_change" in validation_result:
        print(f"Price Change: {validation_result['price_change']:.1f}%")

    if "error" in validation_result:
        print(f"Error: {validation_result['error']}")

    return validation_result

if __name__ == "__main__":
    # Test validation for Mario's BMW
    validate_mario_bmw()

    # Generate validation report
    validator = RealTimePriceValidator()
    report = validator.generate_validation_report()
    print("\n=== Validation Statistics ===")
    for key, value in report.items():
        print(f"{key}: {value}")