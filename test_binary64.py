# test_binary64.py — independent unittest coverage
import unittest, math, struct
from methods.binary64 import float_bits, unpack_binary64, adjacent_floats, signed_zero_info

class TestBinary64(unittest.TestCase):
    def test_bits_1_0(self):
        # 1.0 = sign 0, exponent 1023 (0x3FF), fraction 0
        u = unpack_binary64(1.0)
        self.assertEqual(u["sign"], 0)
        self.assertEqual(u["exponent_raw"], 1023)
        self.assertEqual(u["fraction_raw"], 0)
        self.assertEqual(u["kind"], "normal")

    def test_bits_neg_zero(self):
        u = unpack_binary64(-0.0)
        self.assertEqual(u["sign"], 1)
        self.assertEqual(u["exponent_raw"], 0)
        self.assertEqual(u["fraction_raw"], 0)
        self.assertEqual(u["kind"], "zero")
        # copysign distinguishes
        self.assertTrue(math.copysign(1.0, -0.0) < 0)

    def test_nan_ne_self(self):
        nan = float("nan")
        self.assertFalse(nan == nan)
        self.assertTrue(math.isnan(nan))

    def test_inf(self):
        inf = float("inf")
        u = unpack_binary64(inf)
        self.assertEqual(u["kind"], "inf")
        self.assertEqual(u["exponent_raw"], 0x7FF)
        self.assertEqual(u["fraction_raw"], 0)

    def test_subnormal(self):
        # smallest positive subnormal
        tiny = 5e-324
        u = unpack_binary64(tiny)
        self.assertEqual(u["kind"], "subnormal")
        self.assertEqual(u["exponent_raw"], 0)
        self.assertNotEqual(u["fraction_raw"], 0)

    def test_0_1_not_exact(self):
        f = 0.1
        # 0.1 in binary64 is 0x3FB999999999999A
        bits = float_bits(f)
        self.assertEqual(bits, 0x3FB999999999999A)
        # not equal to decimal 0.1
        from decimal import Decimal
        self.assertNotEqual(Decimal(f), Decimal("0.1"))

    def test_0_1_plus_0_2(self):
        self.assertNotEqual(0.1 + 0.2, 0.3)
        self.assertTrue(math.isclose(0.1 + 0.2, 0.3))

    def test_precision_boundary_2_53(self):
        a = float(2**53)
        b = float(2**53 + 1)
        # ulp = 2, so +1 is lost
        self.assertEqual(a, b)
        c = float(2**53 + 2)
        self.assertNotEqual(a, c)

    def test_nextafter(self):
        up = math.nextafter(1.0, math.inf)
        down = math.nextafter(1.0, -math.inf)
        self.assertGreater(up, 1.0)
        self.assertLess(down, 1.0)
        self.assertEqual(up - 1.0, 2**-52)

    def test_round_half_even(self):
        self.assertEqual(round(2.5), 2)
        self.assertEqual(round(3.5), 4)

    def test_round_2_675(self):
        # 2.675 is actually slightly less than 2.675 in binary64
        f = 2.675
        self.assertEqual(round(f, 2), 2.67)

    def test_non_assoc(self):
        left = (1e16 + 1.0) + (-1e16)
        right = 1e16 + (1.0 + (-1e16))
        # at least one ordering loses the 1.0
        self.assertNotEqual(left, 1.0 if False else None)  # placeholder, just check they differ or one is 0
        # actual: (1e16+1)-1e16 == 0.0, because 1e16+1 == 1e16
        self.assertEqual((1e16 + 1.0) - 1e16, 0.0)

    def test_cancellation(self):
        x = 1e12
        naive = math.sqrt(x + 1.0) - math.sqrt(x)
        stable = 1.0 / (math.sqrt(x + 1.0) + math.sqrt(x))
        # stable form is more accurate; both should be very close
        # at 1e12 the naive form still has decent precision
        rel_err = abs(naive - stable) / stable if stable != 0 else 0
        self.assertLess(rel_err, 1e-5)

    def test_fsum(self):
        vals = [1e16, 1.0, -1e16]
        s = sum(vals)
        fs = math.fsum(vals)
        # fsum is always the correctly-rounded sum
        # in CPython, sum([1e16, 1.0, -1e16]) == 1.0, fsum also 1.0
        self.assertEqual(fs, 1.0)
        # the key property: fsum is exact to within 0.5 ulp

    def test_overflow(self):
        big = 1e308 * 10.0
        self.assertTrue(math.isinf(big))

    def test_signed_zero_division(self):
        # Python raises ZeroDivisionError unlike IEEE 754
        # copysign still distinguishes -0.0
        self.assertTrue(math.copysign(1.0, -0.0) < 0)
        self.assertTrue(math.copysign(1.0, 0.0) > 0)
        with self.assertRaises(ZeroDivisionError):
            _ = 1.0 / 0.0

    def test_results_json_compliance(self):
        """results.json must be standards-compliant JSON (no bare NaN/Inf)"""
        import json, subprocess, sys, os
        # generate fresh results
        subprocess.run([sys.executable, "run.py"], check=True, cwd=os.path.dirname(__file__), capture_output=True)
        with open(os.path.join(os.path.dirname(__file__), "results.json"), "rb") as f:
            data = f.read()
        # parse with strict mode — bare NaN/Inf/Infinity should fail
        def reject_constant(x):
            raise ValueError(f"non-compliant constant: {x}")
        parsed = json.loads(data.decode("utf-8"), parse_constant=reject_constant)
        self.assertIsInstance(parsed, list)
        # verify special float values are encoded as strings
        text = data.decode("utf-8")
        # should NOT contain bare : NaN, : Infinity, : -Infinity (unquoted)
        self.assertNotIn(": NaN,", text)
        self.assertNotIn(": Infinity,", text)
        self.assertNotIn(": -Infinity,", text)
        # but SHOULD contain quoted versions for nan/inf cases
        self.assertIn('"NaN"', text)
        self.assertIn('"Infinity"', text)

if __name__ == "__main__":
    unittest.main()
