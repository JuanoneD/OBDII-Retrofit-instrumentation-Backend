from rest_framework import status
from rest_framework.test import APITestCase

from fuel.models import Refuel
from telemetry.models import Vehicle
from telemetry.tests.test_api import MAC, payload


class RecalculateTests(APITestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            device_id=MAC,
            name="Gol",
            tank_capacity=45,
            gasoline_level=20,
            fuel_consumption_factor=0.008,
            trip_consumption=10,
        )

    def recalc(self, liters):
        return self.client.post(
            "/api/fuel/recalculate/", {"device_id": MAC, "litrosInseridos": liters}, format="json"
        )

    def test_formula_and_reset(self):
        # Sistema achou que gastou 10 L, mas couberam 12 L -> fator sobe 20%
        r = self.recalc(12)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertAlmostEqual(r.data["old_factor"], 0.008)
        self.assertAlmostEqual(r.data["new_factor"], 0.008 * 12 / 10)

        self.vehicle.refresh_from_db()
        self.assertAlmostEqual(self.vehicle.fuel_consumption_factor, 0.0096)
        self.assertEqual(self.vehicle.trip_consumption, 0)
        self.assertEqual(self.vehicle.gasoline_level, 32)
        self.assertTrue(self.vehicle.pending_sync)
        self.assertEqual(Refuel.objects.count(), 1)

    def test_level_never_exceeds_capacity(self):
        self.recalc(40)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.gasoline_level, 45)

    def test_no_consumption_recorded(self):
        self.vehicle.trip_consumption = 0
        self.vehicle.save()
        r = self.recalc(10)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data["code"], "no_consumption_recorded")

    def test_invalid_input(self):
        self.assertEqual(self.recalc(0).status_code, 400)
        self.assertEqual(self.recalc(100).status_code, 400)
        r = self.client.post(
            "/api/fuel/recalculate/",
            {"device_id": "11:22:33:44:55:66", "litrosInseridos": 5},
            format="json",
        )
        self.assertEqual(r.status_code, 404)

    def test_status(self):
        r = self.client.get("/api/fuel/status/", {"device_id": MAC})
        self.assertEqual(r.data["fuel_consumption_factor"], 0.008)
        self.assertEqual(r.data["liters_spent_system"], 10)

    def test_esp32_sync_after_recalculate(self):
        self.recalc(12)

        # ESP32 ainda com valores antigos (sync_version 0): o backend não aceita
        # os valores velhos de combustível e manda os novos na resposta.
        r = self.client.post(
            "/api/telemetry/ingest/", payload(trip_consumption=10.5, gasoline_level=19), format="json"
        )
        self.assertEqual(r.data["sync"]["sync_version"], 1)
        self.assertAlmostEqual(r.data["sync"]["fuel_consumption_factor"], 0.0096)
        self.assertEqual(r.data["sync"]["trip_consumption"], 0)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.trip_consumption, 0)
        self.assertEqual(self.vehicle.gasoline_level, 32)

        # ESP32 aplicou e confirma com sync_version 1: volta ao normal.
        r = self.client.post(
            "/api/telemetry/ingest/",
            payload(sync_version=1, fuel_consumption_factor=0.0096, trip_consumption=0.3, gasoline_level=31.7),
            format="json",
        )
        self.assertIsNone(r.data["sync"])
        self.vehicle.refresh_from_db()
        self.assertFalse(self.vehicle.pending_sync)
        self.assertEqual(self.vehicle.trip_consumption, 0.3)
