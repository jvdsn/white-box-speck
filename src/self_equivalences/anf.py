from abc import abstractmethod
from itertools import combinations
from random import randint

from sage.all import GF
from sage.all import SR
from sage.all import load
from sage.all import matrix
from sage.all import prod
from sage.all import vector
from sage.rings.polynomial.pbori.pbori import BooleanPolynomialRing

from self_equivalences import SelfEquivalenceProvider

ring = GF(2)


class ANFSelfEquivalenceProvider(SelfEquivalenceProvider):
    """
    Generates self-equivalences using the Algebraic Normal Form.
    """

    @abstractmethod
    def __init__(self, word_size, sobj_prefix, degree=1):
        """
        Initializes an instance of ANFSelfEquivalenceProvider with the provided parameters.
        :param word_size: the word size
        :param L: the matrix L
        """
        assert word_size in [16, 24, 32, 48, 64]

        expressions, self.constraints = load(f"sobj/{sobj_prefix}{word_size}.sobj")

        x_names = [f"x{i}" for i in range(4 * word_size)]
        self.coefficient_names = []
        for _, expression in expressions:
            for v in SR(expression).variables():
                if str(v) not in self.coefficient_names:
                    self.coefficient_names.append(str(v))

        self.bpr = BooleanPolynomialRing(names=x_names + self.coefficient_names)
        xs = [self.bpr(x_name) for x_name in x_names]

        zero = matrix(ring, word_size)
        one = matrix.identity(ring, word_size)
        am = matrix.block([
            [zero, one, one, zero],
            [one, one, one, zero],
            [zero, zero, one, zero],
            [one, zero, one, one]
        ])

        am_anf = self._matrix_to_anf(am, xs)
        am_anf_inv = self._matrix_to_anf(am.inverse(), xs)

        values = {**{}, **dict(expressions)}
        c = []
        for i in range(4 * word_size):
            f = self.bpr.zero()
            for d in reversed(range(1, degree + 1)):
                for combination in combinations(range(4 * word_size), d):
                    coefficient = f"b{i}_" + "_".join(f"{j}" for j in combination)
                    if coefficient in values:
                        coefficient = values[coefficient]
                    monomial = prod([xs[j] for j in combination])
                    f += self.bpr(coefficient) * monomial

                coefficient = f"b{i}"
                if coefficient in values:
                    coefficient = values[coefficient]
                f += self.bpr(coefficient)
                c.append(f)

        c = vector(self.bpr, c)
        l_c_l_inv = c.subs({x: am_anf_inv[i] for i, x in enumerate(xs)})
        l_c_l_inv = am_anf.subs({x: l_c_l_inv[i] for i, x in enumerate(xs)})

        a = l_c_l_inv[:2 * word_size].subs({x: 0 for x in xs[2 * word_size:]})
        b_inv = l_c_l_inv[2 * word_size:].subs({x: (0 if i < 2 * word_size else xs[i - 2 * word_size]) for i, x in enumerate(xs)})

        self.A = self._anf_to_matrix(a, xs[:2 * word_size])
        self.A.set_immutable()
        self.a = a.subs({x: 0 for x in xs[:2 * word_size]})
        self.a.set_immutable()
        self.B = self._anf_to_matrix(b_inv, xs[:2 * word_size])
        self.B.set_immutable()
        self.b = b_inv.subs({x: 0 for x in xs[:2 * word_size]})
        self.b.set_immutable()

    def _matrix_to_anf(self, m, xs):
        anf = []
        for row in m.rows():
            f = self.bpr.zero()
            for a, x in zip(row, xs):
                f += a * x

            anf.append(f)

        return vector(self.bpr, anf)

    def _anf_to_matrix(self, anf, xs):
        gens = self.bpr.gens()
        x_indexes = set(gens.index(x) for x in xs)
        rows = []
        for f in anf:
            coefficients = {}
            for monomial in f:
                x = self.bpr.one()
                coefficient = self.bpr.one()
                for i in monomial.iterindex():
                    if i in x_indexes:
                        x *= gens[i]
                    else:
                        coefficient *= gens[i]

                coefficients[x] = coefficients.get(x, 0) + coefficient

            rows.append([coefficients.get(x, 0) for x in xs])

        return matrix(self.bpr, rows)

    def _check_constraints(self, coefficients):
        for constraint in self.constraints:
            if self.bpr(constraint).subs(coefficients) != 0:
                return False
        return True

    def self_equivalence(self, coefficients):
        """
        Generates an affine or a linear self-equivalence of the function S(x, y) = (x + y, y) with coefficients.
        :param coefficients: the coefficients to use
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        A = self.A.subs(coefficients).change_ring(ring)
        A.set_immutable()
        # change_ring does not work on vectors over BPR...
        a = vector(ring, [ring(f.subs(coefficients)) for f in self.a])
        a.set_immutable()
        B = self.B.subs(coefficients).change_ring(ring).inverse()
        B.set_immutable()
        # change_ring does not work on vectors over BPR...
        b = B * vector(ring, [ring(f.subs(coefficients)) for f in self.b])
        b.set_immutable()
        return A, a, B, b

    def random_self_equivalence(self):
        """
        Generates a random affine or linear self-equivalence of the function S(x, y) = (x + y, y).
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        while True:
            coefficients = {self.bpr(coefficient_name): randint(0, 1) for coefficient_name in self.coefficient_names}
            if self._check_constraints(coefficients):
                break

        return self.self_equivalence(coefficients)


class AffineSelfEquivalenceProvider(ANFSelfEquivalenceProvider):
    """
    Generates affine self-equivalences.
    """

    def __init__(self, word_size):
        super().__init__(word_size, "anf_affine_w")


class LinearSelfEquivalenceProvider(ANFSelfEquivalenceProvider):
    """
    Generates linear self-equivalences.
    """

    def __init__(self, word_size):
        super().__init__(word_size, "anf_linear_w")
