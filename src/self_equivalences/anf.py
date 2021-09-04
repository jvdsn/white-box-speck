from abc import abstractmethod
from itertools import combinations
from os import path

from sage.all import GF
from sage.all import SR
from sage.all import load
from sage.all import matrix
from sage.all import prod
from sage.all import vector
from sage.rings.polynomial.pbori.pbori import BooleanPolynomialRing

from self_equivalences import CoefficientsSelfEquivalenceProvider

gf2 = GF(2)


class ANFSelfEquivalenceProvider(CoefficientsSelfEquivalenceProvider):
    """
    Generates self-equivalences using the Algebraic Normal Form.
    """

    @abstractmethod
    def __init__(self, word_size, sobj_prefix, degree=1):
        """
        Initializes an instance of ANFSelfEquivalenceProvider with the provided parameters.
        :param word_size: the word size
        :param sobj_prefix: the prefix of the sobj file containing expressions and constraints
        :param degree: the degree of the self-equivalences (default: 1)
        """
        assert word_size in [16, 24, 32, 48, 64]

        sobj_dir = path.join(path.dirname(path.dirname(path.dirname(__file__))), "sobj")
        expressions, self.constraints = load(path.join(sobj_dir, f"{sobj_prefix}{word_size}.sobj"))

        x_names = [f"x{i}" for i in range(4 * word_size)]
        coefficient_names = []
        for _, expression in expressions:
            for v in SR(expression).variables():
                if str(v) not in coefficient_names:
                    coefficient_names.append(str(v))

        super().__init__(word_size, len(coefficient_names))

        self.ring = BooleanPolynomialRing(names=x_names + coefficient_names)
        xs = [self.ring(x_name) for x_name in x_names]
        self.coefficients = [self.ring(coefficient_name) for coefficient_name in coefficient_names]

        zero = matrix(gf2, word_size)
        one = matrix.identity(gf2, word_size)
        am = matrix.block([
            [zero, one, one, zero],
            [one, one, one, zero],
            [zero, zero, one, zero],
            [one, zero, one, one]
        ])

        am_anf = self._matrix_to_anf(am, xs)
        am_anf_inv = self._matrix_to_anf(am.inverse(), xs)

        # The empty dict here can be used to fill in coefficients, but we wait until later.
        values = {**{}, **dict(expressions)}
        c = []
        for i in range(4 * word_size):
            f = self.ring.zero()
            for d in reversed(range(1, degree + 1)):
                for combination in combinations(range(4 * word_size), d):
                    coefficient = f"b{i}_" + "_".join(f"{j}" for j in combination)
                    if coefficient in values:
                        coefficient = values[coefficient]
                    monomial = prod([xs[j] for j in combination])
                    f += self.ring(coefficient) * monomial

                coefficient = f"b{i}"
                if coefficient in values:
                    coefficient = values[coefficient]
                f += self.ring(coefficient)
                c.append(f)

        c = vector(self.ring, c)
        l_c_l_inv = self._subs_vector(self.ring, c, {x: am_anf_inv[i] for i, x in enumerate(xs)})
        l_c_l_inv = self._subs_vector(self.ring, am_anf, {x: l_c_l_inv[i] for i, x in enumerate(xs)})

        a = self._subs_vector(self.ring, l_c_l_inv[:2 * word_size], {x: 0 for x in xs[2 * word_size:]})
        b_inv = self._subs_vector(self.ring, l_c_l_inv[2 * word_size:], {x: (0 if i < 2 * word_size else xs[i - 2 * word_size]) for i, x in enumerate(xs)})

        self.A = self._anf_to_matrix(a, xs[:2 * word_size])
        self.A.set_immutable()
        self.a = self._subs_vector(self.ring, a, {x: 0 for x in xs[:2 * word_size]})
        self.a.set_immutable()
        self.B = self._anf_to_matrix(b_inv, xs[:2 * word_size])
        self.B.set_immutable()
        self.b = self._subs_vector(self.ring, b_inv, {x: 0 for x in xs[:2 * word_size]})
        self.b.set_immutable()

    def _subs_matrix(self, ring, m, xs):
        res = matrix(ring, m.nrows(), m.ncols())
        for row in range(m.nrows()):
            for col in range(m.ncols()):
                if m[row, col] == 0 or m[row, col] == 1:
                    res[row, col] = m[row, col]
                else:
                    res[row, col] = m[row, col].subs(xs)
        return res

    def _subs_vector(self, ring, v, xs):
        res = vector(ring, len(v))
        for i in range(len(v)):
            if v[i] == 0 or v[i] == 1:
                res[i] = v[i]
            else:
                res[i] = v[i].subs(xs)
        return res

    def _matrix_to_anf(self, m, xs):
        anf = []
        for row in m.rows():
            f = self.ring.zero()
            for a, x in zip(row, xs):
                f += a * x

            anf.append(f)

        return vector(self.ring, anf)

    def _anf_to_matrix(self, anf, xs):
        gens = self.ring.gens()
        x_indexes = set(gens.index(x) for x in xs)
        rows = []
        for f in anf:
            coefficients = {}
            for monomial in f.monomials():
                x = self.ring.one()
                coefficient = self.ring.one()
                # iterindex is much faster than variables.
                for i in monomial.iterindex():
                    if i in x_indexes:
                        x *= gens[i]
                    else:
                        coefficient *= gens[i]

                coefficients[x] = coefficients.get(x, 0) + coefficient

            rows.append([coefficients.get(x, 0) for x in xs])

        return matrix(self.ring, rows)

    def _check_constraints(self, coefficients):
        if not super()._check_constraints(coefficients):
            return False

        coefficients = {self_coefficient: coefficient for self_coefficient, coefficient in zip(self.coefficients, coefficients)}
        for constraint in self.constraints:
            if self.ring(constraint).subs(coefficients) != 0:
                return False
        return True

    def self_equivalence(self, ring, coefficients):
        """
        Generates an affine or a linear self-equivalence of the function S(x, y) = (x + y, y) using coefficients.
        :param ring: the ring
        :param coefficients: the coefficients to use
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        coefficients = {self_coefficient: coefficient for self_coefficient, coefficient in zip(self.coefficients, coefficients)}
        A = self._subs_matrix(ring, self.A, coefficients)
        A.set_immutable()
        a = self._subs_vector(ring, self.a, coefficients)
        a.set_immutable()
        B = self._subs_matrix(ring, self.B, coefficients).inverse()
        B.set_immutable()
        b = B * self._subs_vector(ring, self.b, coefficients)
        b.set_immutable()
        return A, a, B, b


class AffineSelfEquivalenceProvider(ANFSelfEquivalenceProvider):
    """
    Generates affine self-equivalences.
    """

    def __init__(self, word_size):
        """
        Initializes an instance of AffineSelfEquivalenceProvider with the provided parameters.
        :param word_size: the word size
        """
        super().__init__(word_size, "anf_affine_w")


class LinearSelfEquivalenceProvider(ANFSelfEquivalenceProvider):
    """
    Generates linear self-equivalences.
    """

    def __init__(self, word_size):
        """
        Initializes an instance of LinearSelfEquivalenceProvider with the provided parameters.
        :param word_size: the word size
        """
        super().__init__(word_size, "anf_linear_w")
