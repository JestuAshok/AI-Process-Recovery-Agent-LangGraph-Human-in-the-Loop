import threading
import time
from typing import Dict, Any, Optional

# Simulated Products Catalog with specifications and suitable alternatives in INR (₹)
INITIAL_PRODUCTS = {
    "PROD-LAPTOP-X1": {
        "product_id": "PROD-LAPTOP-X1",
        "name": "Apple MacBook Air M3 (13.6-inch, 8GB RAM, 256GB SSD) - Space Grey",
        "available": True,
        "stock_quantity": 0,  # Out of stock at regional hub to demonstrate AI substitution
        "unit_price": 99900.00,
        "category": "Laptops & MacBooks",
        "specifications": {
            "processor": "Apple M3 8-Core Chip",
            "ram": "8GB Unified Memory",
            "storage": "256GB NVMe SSD",
            "display": "13.6-inch Liquid Retina Display",
            "battery": "18 Hours Battery Life"
        },
        "alternatives": ["PROD-LAPTOP-X2", "PROD-LAPTOP-ULTRA"]
    },
    "PROD-LAPTOP-X2": {
        "product_id": "PROD-LAPTOP-X2",
        "name": "Apple MacBook Air M3 (13.6-inch, 16GB RAM, 512GB SSD) - Space Grey [Upgrade Edition]",
        "available": True,
        "stock_quantity": 18,
        "unit_price": 99900.00,  # ₹0 price delta upgrade offered by AI to protect SLA
        "category": "Laptops & MacBooks",
        "specifications": {
            "processor": "Apple M3 8-Core Chip",
            "ram": "16GB Unified Memory (2x RAM)",
            "storage": "512GB NVMe SSD (2x Storage)",
            "display": "13.6-inch Liquid Retina Display",
            "battery": "18 Hours Battery Life"
        },
        "alternatives": ["PROD-LAPTOP-X1"]
    },
    "PROD-LAPTOP-ULTRA": {
        "product_id": "PROD-LAPTOP-ULTRA",
        "name": "Apple MacBook Pro 16-inch M3 Max (36GB RAM, 1TB SSD) - Space Black",
        "available": True,
        "stock_quantity": 5,
        "unit_price": 349900.00,
        "category": "Laptops & MacBooks",
        "specifications": {
            "processor": "Apple M3 Max 14-Core CPU, 30-Core GPU",
            "ram": "36GB Unified Memory",
            "storage": "1TB Superfast SSD",
            "display": "16.2-inch Liquid Retina XDR 120Hz ProMotion",
            "battery": "22 Hours Battery Life"
        },
        "alternatives": ["PROD-LAPTOP-X2"]
    },
    "PROD-PHONE-MAX": {
        "product_id": "PROD-PHONE-MAX",
        "name": "Apple iPhone 15 Pro Max (256 GB) - Natural Titanium",
        "available": True,
        "stock_quantity": 42,
        "unit_price": 144900.00,
        "category": "Smartphones",
        "specifications": {
            "display": "6.7-inch Super Retina XDR OLED 120Hz",
            "camera": "48MP Main + 5x Telephoto Optical Zoom",
            "storage": "256GB Internal Storage"
        },
        "alternatives": []
    },
    "PROD-MONITOR-4K": {
        "product_id": "PROD-MONITOR-4K",
        "name": "Samsung 32-inch 4K UHD Curved Smart Monitor (M8 Series)",
        "available": True,
        "stock_quantity": 12,
        "unit_price": 44999.00,
        "category": "Monitors & Smart Displays",
        "specifications": {
            "resolution": "3840 x 2160 (4K UHD)",
            "panel": "HDR10+ SlimFit Smart TV OS",
            "refresh_rate": "60Hz Adaptive Sound"
        },
        "alternatives": []
    }
}

# Delivery Carriers and simulated logistics routes in India
INITIAL_CARRIERS = {
    "Blue Dart Express": {"status": "OPERATIONAL", "avg_transit_days": 1, "cost": 150.0},
    "Delhivery Express": {"status": "OPERATIONAL", "avg_transit_days": 1, "cost": 120.0},
    "Ekart Logistics (Flipkart)": {"status": "OPERATIONAL", "avg_transit_days": 1, "cost": 99.0},
    "Amazon Shipping Priority": {"status": "OPERATIONAL", "avg_transit_days": 1, "cost": 110.0},
    "Shadowfax Local Express": {"status": "OPERATIONAL", "avg_transit_days": 2, "cost": 80.0}
}


class BusinessState:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BusinessState, cls).__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        self.products: Dict[str, Dict[str, Any]] = {k: v.copy() for k, v in INITIAL_PRODUCTS.items()}
        self.carriers: Dict[str, Dict[str, Any]] = {k: v.copy() for k, v in INITIAL_CARRIERS.items()}
        self.payments: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.deliveries: Dict[str, Dict[str, Any]] = {}
        self.notifications: list = []

        # Chaos / Fault Injection Flags
        # format: { "service_name": {"fault_type": str, "expires_at": float} }
        self.active_faults: Dict[str, Dict[str, Any]] = {}

        # Service metrics stats
        self.service_stats = {
            "payment": {"requests": 0, "failures": 0, "latency_ms": 42, "status": "HEALTHY"},
            "inventory": {"requests": 0, "failures": 0, "latency_ms": 35, "status": "HEALTHY"},
            "order": {"requests": 0, "failures": 0, "latency_ms": 28, "status": "HEALTHY"},
            "delivery": {"requests": 0, "failures": 0, "latency_ms": 50, "status": "HEALTHY"},
            "notification": {"requests": 0, "failures": 0, "latency_ms": 20, "status": "HEALTHY"}
        }

    def record_metric(self, service: str, success: bool, latency: int = 40):
        if service in self.service_stats:
            self.service_stats[service]["requests"] += 1
            if not success:
                self.service_stats[service]["failures"] += 1
                self.service_stats[service]["status"] = "DEGRADED"
            else:
                self.service_stats[service]["status"] = "HEALTHY"
            self.service_stats[service]["latency_ms"] = latency

    def inject_fault(self, service: str, fault_type: str, duration_seconds: int = 60):
        expires_at = time.time() + duration_seconds
        self.active_faults[service] = {
            "fault_type": fault_type,
            "expires_at": expires_at
        }
        if service in self.service_stats:
            self.service_stats[service]["status"] = "FAULT_INJECTED"

    def clear_fault(self, service: str):
        if service in self.active_faults:
            del self.active_faults[service]
        if service in self.service_stats:
            self.service_stats[service]["status"] = "HEALTHY"

    def clear_all_faults(self):
        self.active_faults.clear()
        for s in self.service_stats:
            self.service_stats[s]["status"] = "HEALTHY"

    def is_fault_active(self, service: str) -> Optional[str]:
        if service in self.active_faults:
            fault_data = self.active_faults[service]
            if time.time() < fault_data["expires_at"]:
                return fault_data["fault_type"]
            else:
                # Expired
                del self.active_faults[service]
                if service in self.service_stats:
                    self.service_stats[service]["status"] = "HEALTHY"
        return None

    def reset_state(self):
        self._init_state()


business_state = BusinessState()
