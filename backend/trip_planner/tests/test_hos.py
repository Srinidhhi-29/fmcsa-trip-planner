from django.test import SimpleTestCase

from trip_planner.services.hos import simulate_trip


class HosSimulationTests(SimpleTestCase):
    def test_generates_break_for_long_day(self):
        result = simulate_trip(700, 0, route_path=[[41.8, -87.6], [32.7, -96.7]])
        stops = [stop["type"] for stop in result["stops"]]

        self.assertIn("break", stops)
        self.assertGreaterEqual(len(result["logs"]), 1)

    def test_respects_cycle_limit_with_restart(self):
        result = simulate_trip(1200, 68, route_path=[[41.8, -87.6], [32.7, -96.7]])
        stops = [stop["type"] for stop in result["stops"]]

        self.assertIn("cycle_reset", stops)

    def test_adds_fuel_stop_every_thousand_miles(self):
        result = simulate_trip(1400, 10, route_path=[[41.8, -87.6], [34.0, -118.2]])
        fuel_stops = [stop for stop in result["stops"] if stop["type"] == "fuel"]

        self.assertEqual(len(fuel_stops), 1)
        self.assertEqual(fuel_stops[0]["rule_code"], "FUEL_1000_MILES")

    def test_returns_compliance_proof(self):
        result = simulate_trip(700, 0, route_path=[[41.8, -87.6], [32.7, -96.7]])

        self.assertTrue(result["compliance"]["is_compliant"])
        self.assertEqual(result["summary"]["compliance_status"], "VALID")
        self.assertTrue(result["compliance"]["checks"])
