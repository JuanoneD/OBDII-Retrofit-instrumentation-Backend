from rest_framework import status
from rest_framework.test import APITestCase

from telemetry.models import Reading, Vehicle

MAC = "AA:BB:CC:DD:EE:FF"


def payload(**overrides):
    """JSON de exemplo igual ao que a ESP32 envia."""
    data = {
        "device_id": MAC,
        "rpm": 850,
        "speed": 0,
        "coolant_temp": 90,
        "engine_load": 25.5,
        "throttle_position": 12.0,
        "ltft": -2.3,
        "timing_advance": 10.0,
        "module_voltage": 13.8,
        "map_pressure": 35.0,
        "gasoline_level": 30.0,
        "tank_capacity": 45.0,
        "fuel_consumption_factor": 0.008,
        "total_distance": 1234.5,
        "trip_consumption": 4.2,
    }
    data.update(overrides)
    return data


class DeviceTests(APITestCase):
    def test_register_device_normalizes_mac(self):
        r = self.client.post("/api/devices/", {"device_id": "aa-bb-cc-dd-ee-ff", "name": "Gol"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        self.assertEqual(r.data["device_id"], MAC)
        self.assertEqual(r.data["gasoline_level"], 45.0)

    def test_register_duplicate_device(self):
        Vehicle.objects.create(device_id=MAC, name="Gol")
        r = self.client.post("/api/devices/", {"device_id": MAC, "name": "Outro"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_mac(self):
        r = self.client.post("/api/devices/", {"device_id": "123", "name": "Gol"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_device(self):
        Vehicle.objects.create(device_id=MAC, name="Gol")
        self.assertEqual(self.client.get(f"/api/devices/{MAC}/").status_code, 200)
        self.assertEqual(self.client.get("/api/devices/11:22:33:44:55:66/").status_code, 404)


class IngestTests(APITestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(device_id=MAC, name="Gol")

    def test_ingest_saves_reading_and_updates_vehicle(self):
        r = self.client.post("/api/telemetry/ingest/", payload(), format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        self.assertEqual(r.data["status"], "ok")
        self.assertIsNone(r.data["sync"])
        self.assertEqual(Reading.objects.count(), 1)

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.gasoline_level, 30.0)
        self.assertEqual(self.vehicle.trip_consumption, 4.2)
        self.assertEqual(self.vehicle.total_distance, 1234.5)
        self.assertIsNotNone(self.vehicle.last_seen_at)
        self.assertAlmostEqual(Reading.objects.get().fuel_percent, 66.7)

    def test_ingest_incomplete_json(self):
        data = payload()
        del data["rpm"]
        r = self.client.post("/api/telemetry/ingest/", data, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data["code"], "invalid_payload")
        self.assertIn("rpm", r.data["errors"])
        self.assertEqual(Reading.objects.count(), 0)

    def test_ingest_unknown_device(self):
        r = self.client.post("/api/telemetry/ingest/", payload(device_id="11:22:33:44:55:66"), format="json")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(r.data["code"], "device_not_registered")

    def test_ingest_inactive_device(self):
        self.vehicle.is_active = False
        self.vehicle.save()
        r = self.client.post("/api/telemetry/ingest/", payload(), format="json")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)


class ReadTests(APITestCase):
    def setUp(self):
        Vehicle.objects.create(device_id=MAC, name="Gol")

    def test_latest_without_readings(self):
        r = self.client.get("/api/telemetry/latest/", {"device_id": MAC})
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.data["reading"])

    def test_latest_and_history(self):
        for rpm in (800, 900, 1000):
            self.client.post("/api/telemetry/ingest/", payload(rpm=rpm), format="json")

        r = self.client.get("/api/telemetry/latest/", {"device_id": MAC})
        self.assertEqual(r.data["reading"]["rpm"], 1000)
        self.assertEqual(r.data["vehicle"]["name"], "Gol")

        r = self.client.get("/api/telemetry/history/", {"device_id": MAC, "limit": 2})
        self.assertEqual(r.data["count"], 2)
        self.assertEqual([x["rpm"] for x in r.data["results"]], [900, 1000])

    def test_read_requires_device_id(self):
        self.assertEqual(self.client.get("/api/telemetry/latest/").status_code, 400)
        r = self.client.get("/api/telemetry/history/", {"device_id": "11:22:33:44:55:66"})
        self.assertEqual(r.status_code, 404)

    def test_health(self):
        self.assertEqual(self.client.get("/api/health/").data, {"status": "ok"})
