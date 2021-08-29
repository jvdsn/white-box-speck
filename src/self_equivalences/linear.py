import random

from sage.all import GF
from sage.all import matrix
from sage.all import vector

from self_equivalences import SelfEquivalenceProvider

gf2 = GF(2)


class LinearSelfEquivalenceProvider(SelfEquivalenceProvider):
    """
    Generates linear self-equivalences.
    """

    def __init__(self, word_size):
        """
        Initializes an instance of LinearSelfEquivalenceProvider with the provided parameters.
        :param word_size: the word size
        """
        super().__init__(word_size)

    def _self_equivalence_implicit(self, ring, coefficients):
        """
        Generates a linear self-equivalence of the implicit function f_H with coefficients.
        :param ring: the ring
        :param coefficients: the coefficients to use
        :return: a tuple containing the matrix A of the self-equivalence, and the matrix L
        """
        ws = self.word_size
        assert len(coefficients) == 2 * ws

        zero = matrix(ring, ws)
        one = matrix.identity(ring, ws)

        C0 = matrix.identity(ring, ws)
        for i in range(ws - 1):
            C0[ws - 1, i] = coefficients.pop()

        C1 = matrix.identity(ring, ws)
        for i in range(ws - 1):
            C1[ws - 1, i] = coefficients.pop()

        D0 = matrix(ring, ws)
        D0[ws - 1, 0] = coefficients.pop()
        for i in range(1, ws - 1):
            D0[ws - 1, i] = C0[ws - 1, i]

        D1 = matrix(ring, ws)
        D1[ws - 1, 0] = coefficients.pop()
        for i in range(1, ws - 1):
            D1[ws - 1, i] = C0[ws - 1, i] + C1[ws - 1, i]

        assert len(coefficients) == 0

        A = matrix.block(ring, [
            [C0, D0, D0, zero],
            [D1, C1, C0 + C1, D0],
            [D0, zero, C0, D0],
            [C0 + C1, D0, D1, C1]
        ])
        A.set_immutable()

        L = matrix.block(ring, [
            [zero, one, one, zero],
            [one, one, one, zero],
            [zero, zero, one, zero],
            [one, zero, one, one]
        ])
        L.set_immutable()
        return A, L

    def self_equivalence(self, ring, coefficients):
        """
        Generates a linear self-equivalence of the function S(x, y) = (x + y, y) with coefficients.
        :param ring: the ring
        :param coefficients: the coefficients to use
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        A, L = self._self_equivalence_implicit(ring, coefficients)
        M = L * A * L.inverse()
        A = M.submatrix(row=0, col=0, nrows=2 * self.word_size, ncols=2 * self.word_size)
        A.set_immutable()
        a = vector(ring, 2 * self.word_size)
        a.set_immutable()
        B = M.submatrix(row=2 * self.word_size, col=2 * self.word_size).inverse()
        B.set_immutable()
        b = vector(ring, 2 * self.word_size)
        b.set_immutable()
        return A, a, B, b

    def random_self_equivalence(self, ring):
        """
        Generates a random linear self-equivalence of the function S(x, y) = (x + y, y).
        The returned vector a and vector b will necessarily be zero vectors.
        :param ring: the ring
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        assert ring == gf2

        coefficients = [random.randint(0, 1) for _ in range(2 * self.word_size)]
        return self.self_equivalence(ring, coefficients)


if __name__ == "__main__":
    from sage.all import SR

    word_size = 64
    ring = SR

    self_equivalence_provider = LinearSelfEquivalenceProvider(word_size)
    coefficients = [ring(f"x{i}") for i in range(2 * word_size)]
    A, a, B, b = self_equivalence_provider.self_equivalence(ring, coefficients)
    A_vars = set(A.variables())
    B_vars = set(B.variables())
    print(len(A_vars), len(B_vars), len(A_vars | B_vars))
