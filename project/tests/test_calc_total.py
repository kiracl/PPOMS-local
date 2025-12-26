import unittest
from calc import calc_total


class TestCalcTotal(unittest.TestCase):
    def test_empty(self):
        v, ok = calc_total("", "")
        self.assertFalse(ok)
        self.assertEqual(v, "")

    def test_zero(self):
        v, ok = calc_total("0", "100")
        self.assertTrue(ok)
        self.assertEqual(v, "0.00")

    def test_negative_price(self):
        v, ok = calc_total("-1", "2")
        self.assertFalse(ok)
        self.assertEqual(v, "")

    def test_negative_qty(self):
        v, ok = calc_total("1.50", "-2")
        self.assertFalse(ok)
        self.assertEqual(v, "")

    def test_decimal_round(self):
        v, ok = calc_total("1.235", "2")
        self.assertTrue(ok)
        self.assertEqual(v, "2.47")

    def test_large(self):
        v, ok = calc_total("123456.78", "9")
        self.assertTrue(ok)
        self.assertEqual(v, "1111111.02")


if __name__ == "__main__":
    unittest.main()

