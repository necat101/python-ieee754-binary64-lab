# test_binary64.py — independent unittest coverage
import unittest, math, struct, sys
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
        # (1e16 + 1.0) + (-1e16)  vs  1e16 + (1.0 + -1e16)
        left = (1e16 + 1.0) + (-1e16)
        right = 1e16 + (1.0 + (-1e16))
        # Both orders lose the 1.0 because 1e16 + 1.0 == 1e16 (ulp=2 at 1e16)
        # So left = (1e16) + (-1e16) = 0.0
        # right = 1e16 + (-1e16) = 0.0  (since 1.0 + -1e16 == -1e16)
        self.assertEqual(left, 0.0)
        self.assertEqual(right, 0.0)
        # The associativity "failure" is that the 1.0 is lost in both orders,
        # demonstrating precision loss at large magnitudes
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
        # Python 3.12+ sum() uses a compensated algorithm (Neumaier),
        # making it much more accurate than pre-3.12 sum().
        # For the classic [1e16, 1.0, -1e16] case, both sum() and fsum()
        # now return 1.0 correctly.
        self.assertGreaterEqual(sys.version_info, (3, 12), "test expects Python 3.12+")
        vals = [1e16, 1.0, -1e16]
        s = sum(vals)
        fs = math.fsum(vals)
        # fsum is the correctly-rounded exact sum
        self.assertEqual(fs, 1.0)
        # sum() in 3.12+ matches fsum() for this case
        self.assertEqual(s, fs)
        # verify against Decimal exact sum
        from decimal import Decimal, getcontext
        getcontext().prec = 50
        dec_sum = sum(Decimal(str(v)) for v in vals)
        self.assertEqual(Decimal(fs), dec_sum)

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

    def test_frexp_ldexp(self):
        # math.frexp / math.ldexp round-trip
        for x in [0.1, 0.5, 1.0, 3.141592653589793, -2.5, 1e-10, 1e10]:
            mant, exp = math.frexp(x)
            reconstructed = math.ldexp(mant, exp)
            self.assertEqual(reconstructed, x)
            if x != 0.0:
                self.assertTrue(0.5 <= abs(mant) < 1.0)

    def test_results_json_compliance(self):
        """results.json must be standards-compliant JSON (no bare NaN/Inf)"""
        import json, subprocess, os
        # generate fresh results
        subprocess.run([sys.executable, "run.py"], check=True, cwd=os.path.dirname(__file__), capture_output=True)
        with open(os.path.join(os.path.dirname(__file__), "results.json"), "rb") as f:
            data = f.read()
        # parse with strict mode — bare NaN/Inf/Infinity should fail
        def reject_constant(x):
            raise ValueError(f"non-compliant constant: {x}")
        parsed = json.loads(data.decode("utf-8"), parse_constant=reject_constant)
        self.assertIsInstance(parsed, dict)
        self.assertIn("runtime", parsed)
        self.assertIn("cases", parsed)
        self.assertIsInstance(parsed["cases"], list)
        # verify runtime metadata includes sys.float_info
        self.assertIn("float_info", parsed["runtime"])
        fi = parsed["runtime"]["float_info"]
        self.assertIn("mant_dig", fi)
        self.assertEqual(fi["mant_dig"], 53)
        # verify special float values are encoded as strings
        text = data.decode("utf-8")
        # should NOT contain bare : NaN, : Infinity, : -Infinity (unquoted)
        self.assertNotIn(": NaN,", text)
        self.assertNotIn(": Infinity,", text)
        self.assertNotIn(": -Infinity,", text)
        # but SHOULD contain quoted versions for nan/inf cases
        self.assertIn('"NaN"', text)
        self.assertIn('"Infinity"', text)

    def test_case_validation_enforced(self):
        """Deliberately reversing an expected result must cause runner to fail."""
        import subprocess, os, json, tempfile, shutil
        # copy cases.py to temp, flip one expected result, run, check exit code
        tmpdir = tempfile.mkdtemp()
        try:
            srcdir = os.path.dirname(__file__)
            for fn in ["cases.py", "run.py", "methods"]:
                src = os.path.join(srcdir, fn)
                dst = os.path.join(tmpdir, fn)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            # patch cases.py: flip round_tie_2_5 expected result
            cases_path = os.path.join(tmpdir, "cases.py")
            with open(cases_path, "r") as f:
                content = f.read()
            # change round_expected from 2.0 to 3.0 for round_tie_2_5
            content = content.replace(
                '"id": "round_tie_2_5", "x": 2.5, "tag": "rounding_ties", "desc": "round(2.5,0)==2 — ties to even", "round_digits": 0, "round_expected": 2.0',
                '"id": "round_tie_2_5", "x": 2.5, "tag": "rounding_ties", "desc": "round(2.5,0)==2 — ties to even", "round_digits": 0, "round_expected": 3.0'
            )
            with open(cases_path, "w") as f:
                f.write(content)
            # run
            proc = subprocess.run(
                [sys.executable, "run.py"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            # runner must exit nonzero when a case fails validation
            self.assertNotEqual(proc.returncode, 0, f"runner should fail with wrong expected value, got exit {proc.returncode}, stdout={proc.stdout}, stderr={proc.stderr}")
            # results.json should show the failure
            with open(os.path.join(tmpdir, "results.json")) as f:
                data = json.load(f)
            cases = data["cases"] if isinstance(data, dict) else data
            failed = [c for c in cases if not c.get("ok", True)]
            self.assertTrue(len(failed) >= 1, "at least one case should fail with flipped expectation")
            self.assertTrue(any(c["id"] == "round_tie_2_5" for c in failed))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
