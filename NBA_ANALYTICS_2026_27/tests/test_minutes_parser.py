import unittest

from collectors.nba_stats import _minutes_to_decimal


class TestMinutesParser(unittest.TestCase):
    def test_iso_duration(self):
        self.assertAlmostEqual(_minutes_to_decimal("PT34M12.00S"), 34.2, places=3)

    def test_clock_duration(self):
        self.assertAlmostEqual(_minutes_to_decimal("12:30"), 12.5, places=3)

    def test_missing(self):
        self.assertIsNone(_minutes_to_decimal(None))


if __name__ == "__main__":
    unittest.main()
