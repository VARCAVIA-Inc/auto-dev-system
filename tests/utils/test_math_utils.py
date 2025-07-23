import unittest

def add(a, b):
    return a + b

class TestAddFunction(unittest.TestCase):

    def test_add_positive_numbers(self):
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(10, 20), 30)

    def test_add_negative_numbers(self):
        self.assertEqual(add(-2, -3), -5)
        self.assertEqual(add(-10, -20), -30)

    def test_add_positive_and_negative(self):
        self.assertEqual(add(5, -2), 3)
        self.assertEqual(add(-5, 2), -3)
        self.assertEqual(add(10, -10), 0)

    def test_add_zero(self):
        self.assertEqual(add(0, 7), 7)
        self.assertEqual(add(7, 0), 7)
        self.assertEqual(add(0, 0), 0)

    def test_add_float_numbers(self):
        self.assertAlmostEqual(add(0.1, 0.2), 0.3)
        self.assertAlmostEqual(add(1.5, 2.5), 4.0)
        self.assertAlmostEqual(add(-0.1, -0.2), -0.3)

    def test_add_large_numbers(self):
        self.assertEqual(add(1000000, 2000000), 3000000)
        self.assertEqual(add(999999999, 1), 1000000000)

if __name__ == '__main__':
    unittest.main()