import unittest
import gwasprs
import numpy as np
import jax.numpy as jnp


class SumUpTestCase(unittest.TestCase):

    def setUp(self):
        self.A = np.random.rand(2, 3, 4)
        self.B = np.random.rand(2, 3, 4)
        self.C = np.random.rand(2, 3, 4)

    def tearDown(self):
        self.A = None
        self.B = None
        self.C = None

    def test_sum_of_numpy_arrays(self):
        result = gwasprs.aggregations.SumUp()(self.A, self.B, self.C)
        ans = self.A + self.B + self.C
        np.testing.assert_array_almost_equal(ans, result)

    def test_sum_of_jax_arrays(self):
        result = gwasprs.aggregations.SumUp()(jnp.array(self.A), jnp.array(self.B), jnp.array(self.C))
        ans = jnp.array(self.A) + jnp.array(self.B) + jnp.array(self.C)
        np.testing.assert_array_almost_equal(ans, result)

    def test_sum_of_numbers(self):
        result = gwasprs.aggregations.SumUp()(1, 2.5, 3.4)
        ans = 6.9
        self.assertEqual(ans, result)

    def test_sum_of_list_of_numpy_arrays(self):
        result = gwasprs.aggregations.SumUp()([self.A, self.B], [self.C, self.C])
        ans = [self.A + self.C, self.B + self.C]
        np.testing.assert_array_almost_equal(ans, result)

    def test_sum_of_list_of_jax_arrays(self):
        result = gwasprs.aggregations.SumUp()([jnp.array(self.A), jnp.array(self.B)], [jnp.array(self.C), jnp.array(self.C)])
        ans = [jnp.array(self.A + self.C), jnp.array(self.B + self.C)]
        np.testing.assert_array_almost_equal(ans, result)


class IntersectTestCase(unittest.TestCase):

    def setUp(self):
        self.A = np.array([2, 2, 5, 1, 7, 0, 10])
        self.B = np.array([1, 2, 3, 4, 4, 5, 7, 10, 0])
        self.C = np.array([0, 1, 2, 3, 4, 5, 6, 7, 10])

    def tearDown(self):
        self.A = None
        self.B = None
        self.C = None

    def test_intersect_of_numpy_arrays(self):
        result = gwasprs.aggregations.Intersect()(self.A, self.B, self.C)
        ans = np.array([2, 5, 1, 7, 0, 10])
        np.testing.assert_array_equal(ans, result)

    def test_intersect_of_jax_arrays(self):
        result = gwasprs.aggregations.Intersect()(jnp.array(self.A), jnp.array(self.B), jnp.array(self.C))
        ans = jnp.array([2, 5, 1, 7, 0, 10])
        np.testing.assert_array_equal(ans, result)

    def test_intersect_of_numbers(self):
        result = lambda : gwasprs.aggregations.Intersect()(1, 2.5, 3.4)
        self.assertRaises(NotImplementedError, result)

    def test_intersect_of_list_of_numpy_arrays(self):
        result = lambda : gwasprs.aggregations.Intersect()([self.A, self.B], [self.C, self.C])
        self.assertRaises(NotImplementedError, result)

    def test_intersect_of_list_of_jax_arrays(self):
        result = lambda : gwasprs.aggregations.Intersect()([jnp.array(self.A), jnp.array(self.B)], [jnp.array(self.C), jnp.array(self.C)])
        self.assertRaises(NotImplementedError, result)
