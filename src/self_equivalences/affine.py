from abc import abstractmethod
from random import randint

from sage.all import GF
from sage.all import matrix
from sage.all import vector

from self_equivalences import SelfEquivalenceProvider

gf2 = GF(2)


class AffineSelfEquivalenceProvider(SelfEquivalenceProvider):
    """
    Generates affine self-equivalences.
    """

    @abstractmethod
    def __init__(self, word_size):
        """
        Initializes an instance of AffineSelfEquivalenceProvider with the provided parameters.
        :param word_size: the word size
        """
        assert word_size >= 3

        super().__init__(word_size)

    @abstractmethod
    def _self_equivalence_implicit(self, ring, coefficients):
        """
        Generates an affine self-equivalence of the implicit function f_H with coefficients.
        :param ring: the ring
        :param coefficients: the coefficients to use
        :return: a tuple containing the matrix A and the vector a of the self-equivalence
        """
        pass

    def self_equivalence(self, ring, coefficients):
        """
        Generates an affine self-equivalence of the function S(x, y) = (x + y, y) with coefficients.
        :param ring: the ring
        :param coefficients: the coefficients to use
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        A, a, L = self._self_equivalence_implicit(ring, coefficients)
        M = L * A * L.inverse()
        m = L * a
        A = M.submatrix(row=0, col=0, nrows=2 * self.word_size, ncols=2 * self.word_size)
        A.set_immutable()
        a = m[:2 * self.word_size]
        a.set_immutable()
        B = M.submatrix(row=2 * self.word_size, col=2 * self.word_size).inverse()
        B.set_immutable()
        b = B * m[2 * self.word_size:]
        b.set_immutable()
        return A, a, B, b


class Type1AffineSelfEquivalenceProvider(AffineSelfEquivalenceProvider):
    """
    Generates type 1 affine self-equivalences.
    """

    def __init__(self, word_size):
        """
        Initializes an instance of Type1AffineSelfEquivalenceProvider with the provided parameters.
        :param word_size: the word size
        """
        super().__init__(word_size)

    def _self_equivalence_implicit(self, ring, coefficients):
        """
        Generates a type 1 affine self-equivalence of the implicit function f_H with coefficients.
        :param coefficients: the coefficients to use
        :return: a tuple containing the matrix A and the vector a of the self-equivalence, and the matrix L
        """
        ws = self.word_size
        assert len(coefficients) == 2 * ws + 7

        zero = matrix(ring, ws)
        one = matrix.identity(ring, ws)

        C = matrix.identity(ring, ws)
        C[ws - 1, 0] = coefficients.pop()
        C[ws - 1, ws - 2] = coefficients.pop()

        D = matrix.identity(ring, ws)
        for i in range(1, ws):
            D[ws - 1, i] = coefficients.pop()

        E = matrix.identity(ring, ws)
        E[1, 0] = coefficients.pop()
        for i in range(1, ws - 1):
            E[ws - 1, i] = coefficients.pop()

        F = matrix.identity(ring, ws)
        F[1, 0] = coefficients.pop()
        F[ws - 1, 0] = coefficients.pop()
        F[ws - 1, ws - 2] = coefficients.pop()

        G = matrix(ring, ws)
        G[ws - 1, 0] = coefficients.pop()

        H = matrix(ring, ws)
        H[ws - 1, 0] = coefficients.pop()

        D[ws - 1, 0] = F[1, 0] + F[ws - 1, 0] + G[ws - 1, 0]

        for i in range(2, ws - 1):
            E[i, 0] = E[1, 0]
        E[ws - 1, 0] = C[ws - 1, 0] + E[1, 0] + G[ws - 1, 0]
        E[ws - 1, ws - 1] = D[ws - 1, ws - 1]

        for i in range(2, ws - 1):
            F[i, 0] = F[1, 0]
        for i in range(1, ws - 2):
            F[ws - 1, i] = D[ws - 1, i] + E[ws - 1, i]

        for i in range(1, ws - 1):
            G[ws - 1, i] = E[ws - 1, i]
        G[ws - 1, ws - 1] = D[ws - 1, ws - 1] + 1

        for i in range(1, ws - 1):
            H[i, 0] = E[1, 0] + F[1, 0]

        I = matrix(ring, ws)
        I[ws - 1, 0] = C[ws - 1, 0] + E[1, 0] + F[ws - 1, 0] + G[ws - 1, 0] + H[ws - 1, 0]
        for i in range(1, ws - 2):
            I[ws - 1, i] = D[ws - 1, i]
        I[ws - 1, ws - 2] = E[ws - 1, ws - 2] + F[ws - 1, ws - 2]
        I[ws - 1, ws - 1] = D[ws - 1, ws - 1] + 1

        J = matrix(ring, ws)
        for i in range(1, ws - 1):
            J[i, 0] = F[1, 0]
        J[ws - 1, 0] = F[1, 0] + G[ws - 1, 0]
        for i in range(1, ws - 2):
            J[ws - 1, i] = E[ws - 1, i]
        J[ws - 1, ws - 2] = D[ws - 1, ws - 2] + F[ws - 1, ws - 2]
        J[ws - 1, ws - 1] = D[ws - 1, ws - 1] + 1

        a = vector(ring, ws * 4)
        a[0] = F[1, 0]
        a[ws - 2] = D[ws - 1, ws - 2] + E[ws - 1, ws - 2] + F[ws - 1, ws - 2]
        a[ws - 1] = coefficients.pop()
        a[ws] = E[1, 0]
        a[2 * ws - 2] = C[ws - 1, ws - 2]
        a[2 * ws - 1] = coefficients.pop()
        a[2 * ws] = F[1, 0]
        for i in range(2 * ws + 1, 3 * ws - 2):
            a[i] = E[1, 0] * (F[1, 0] + 1)
        a[3 * ws - 2] = E[1, 0] * (F[1, 0] + 1) + D[ws - 1, ws - 2] + E[ws - 1, ws - 2] + F[ws - 1, ws - 2]
        a[3 * ws - 1] = E[1, 0] * (F[1, 0] + 1) + C[ws - 1, ws - 2] * (D[ws - 1, ws - 2] + E[ws - 1, ws - 2] + F[ws - 1, ws - 2] + 1) + a[ws - 1]
        a[3 * ws] = E[1, 0]
        a[4 * ws - 2] = C[ws - 1, ws - 2]
        a[4 * ws - 1] = a[2 * ws - 1]

        assert len(coefficients) == 0

        A = matrix.block(ring, [
            [C, zero, G, G],
            [zero, D, I, zero],
            [zero, J, E, zero],
            [H, J, zero, F]
        ])
        A.set_immutable()
        a.set_immutable()

        L = matrix.block(ring, [
            [one, zero, one, one],
            [zero, zero, one, one],
            [zero, zero, one, zero],
            [zero, one, one, zero]
        ])
        L.set_immutable()
        return A, a, L

    def random_self_equivalence(self, ring):
        """
        Generates a random affine self-equivalence of the function S(x, y) = (x + y, y).
        :param ring: the ring
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        assert ring == gf2

        coefficients = [randint(0, 1) for _ in range(2 * self.word_size + 7)]
        return self.self_equivalence(ring, coefficients)


class Type2AffineSelfEquivalenceProvider(AffineSelfEquivalenceProvider):
    """
    Generates type 2 affine self-equivalences.
    """

    def __init__(self, word_size):
        """
        Initializes an instance of Type2AffineSelfEquivalenceProvider with the provided parameters.
        :param word_size: the word size
        """
        super().__init__(word_size)

    def _self_equivalence_implicit(self, ring, coefficients):
        """
        Generates an affine self-equivalence of the implicit function f_H with coefficients.
        The coefficients coefficients[0] and coefficients[1] should not be equal to 0 at the same time.
        :param coefficients: the coefficients to use
        :return: a tuple containing the matrix A and the vector a of the self-equivalence, and the matrix L
        """
        ws = self.word_size
        assert len(coefficients) == 2 * ws + 7

        zero = matrix(ring, ws)
        one = matrix.identity(ring, ws)

        # Pop from the start of the list for the special coefficients.
        C00 = coefficients.pop(0)
        D00 = coefficients.pop(0)
        # Make sure the first two coefficients are not zero at the same time.
        assert not (C00 == 0 and D00 == 0)

        C = matrix.identity(ring, ws)
        C[0, 0] = C00
        C[ws - 1, 0] = coefficients.pop()

        D = matrix.identity(ring, ws)
        D[0, 0] = D00
        D[ws - 1, ws - 2] = coefficients.pop()

        E = matrix.identity(ring, ws)
        for i in range(1, ws - 1):
            E[ws - 1, i] = coefficients.pop()

        F = matrix.identity(ring, ws)
        F[ws - 1, 0] = coefficients.pop()

        G = matrix.identity(ring, ws)
        for i in range(1, ws):
            G[ws - 1, i] = coefficients.pop()

        H = matrix.identity(ring, ws)
        H[ws - 1, ws - 2] = coefficients.pop()

        I = matrix(ring, ws)
        I[ws - 1, 0] = coefficients.pop()

        J = matrix(ring, ws)
        J[ws - 1, 0] = coefficients.pop()

        K = matrix(ring, ws)
        K[0, 0] = D[0, 0] + C[0, 0]
        K[ws - 1, 0] = F[ws - 1, 0] * (C[0, 0] + D[0, 0]) + D[0, 0] * I[ws - 1, 0]

        D[ws - 1, 0] = C[0, 0] * J[ws - 1, 0] + D[0, 0] * (C[ws - 1, 0] + J[ws - 1, 0]) + K[ws - 1, 0] * (G[ws - 1, ws - 1] + 1)

        E[0, 0] = C[0, 0]
        E[ws - 1, 0] = C[0, 0] * F[ws - 1, 0] + I[ws - 1, 0] * (C[0, 0] + D[0, 0])

        F[0, 0] = D[0, 0]
        for i in range(1, ws - 1):
            F[ws - 1, i] = E[ws - 1, i]

        I[0, 0] = D[0, 0] + C[0, 0]

        J[0, 0] = D[0, 0] + C[0, 0]
        for i in range(1, ws - 2):
            J[ws - 1, i] = E[ws - 1, i] * G[ws - 1, ws - 1] + G[ws - 1, i]
        J[ws - 1, ws - 2] = D[ws - 1, ws - 2] + E[ws - 1, ws - 2] * (G[ws - 1, ws - 1] + 1) + H[ws - 1, ws - 2]
        J[ws - 1, ws - 1] = G[ws - 1, ws - 1] + 1

        L = matrix(ring, ws)
        L[0, 0] = D[0, 0] + C[0, 0]
        L[ws - 1, 0] = C[0, 0] * C[ws - 1, 0] + C[0, 0] * J[ws - 1, 0] + D[0, 0] * C[ws - 1, 0] + E[ws - 1, 0] * G[ws - 1, ws - 1] + E[ws - 1, 0]
        for i in range(1, ws - 2):
            L[ws - 1, i] = E[ws - 1, i] + G[ws - 1, i]
        L[ws - 1, ws - 2] = D[ws - 1, ws - 2] + E[ws - 1, ws - 2] + G[ws - 1, ws - 2]
        L[ws - 1, ws - 1] = G[ws - 1, ws - 1] + 1

        G[0, 0] = D[0, 0]
        G[ws - 1, 0] = E[ws - 1, 0] + L[ws - 1, 0]

        H[0, 0] = C[0, 0]
        for i in range(1, ws - 2):
            H[ws - 1, i] = E[ws - 1, i] + G[ws - 1, i]
        H[ws - 1, ws - 1] = G[ws - 1, ws - 1]
        H[ws - 1, 0] = D[ws - 1, 0] + L[ws - 1, 0]

        M = matrix(ring, ws)
        M[0, 0] = D[0, 0] + C[0, 0]
        M[ws - 1, 0] = D[ws - 1, 0] + E[ws - 1, 0] + K[ws - 1, 0] + L[ws - 1, 0]
        for i in range(1, ws - 2):
            M[ws - 1, i] = G[ws - 1, i]
        M[ws - 1, ws - 2] = E[ws - 1, ws - 2] + H[ws - 1, ws - 2]
        M[ws - 1, ws - 1] = G[ws - 1, ws - 1] + 1

        N = matrix(ring, ws)
        N[0, 0] = D[0, 0] + C[0, 0]
        N[ws - 1, 0] = L[ws - 1, 0]
        for i in range(1, ws - 1):
            N[ws - 1, i] = E[ws - 1, i] + G[ws - 1, i]
        N[ws - 1, ws - 1] = G[ws - 1, ws - 1] + 1

        O = matrix(ring, ws)
        O[ws - 1, 0] = D[ws - 1, 0] + H[ws - 1, 0] + M[ws - 1, 0]
        for i in range(1, ws - 2):
            O[ws - 1, i] = E[ws - 1, i]
        O[ws - 1, ws - 2] = D[ws - 1, ws - 2] + E[ws - 1, ws - 2]

        P = matrix(ring, ws)
        P[ws - 1, 0] = D[ws - 1, 0] + G[ws - 1, 0]
        for i in range(1, ws - 1):
            P[ws - 1, i] = G[ws - 1, i]
        P[ws - 1, ws - 1] = G[ws - 1, ws - 1] + 1

        Q = matrix(ring, ws)
        Q[ws - 1, 0] = E[ws - 1, 0] + G[ws - 1, 0] + K[ws - 1, 0]
        for i in range(1, ws - 1):
            Q[ws - 1, i] = E[ws - 1, i] + G[ws - 1, i]
        Q[ws - 1, ws - 1] = G[ws - 1, ws - 1] + 1

        R = matrix(ring, ws)
        R[ws - 1, 0] = K[ws - 1, 0] + M[ws - 1, 0]
        for i in range(1, ws - 2):
            R[ws - 1, i] = G[ws - 1, i]
        R[ws - 1, ws - 2] = E[ws - 1, ws - 2] + H[ws - 1, ws - 2]
        R[ws - 1, ws - 1] = G[ws - 1, ws - 1] + 1

        a = vector(ring, ws * 4)
        a[0] = D[0, 0] + C[0, 0]
        a[ws - 2] = E[ws - 1, ws - 2] + G[ws - 1, ws - 2] + H[ws - 1, ws - 2]
        a[ws - 1] = coefficients.pop()
        a[ws] = C[0, 0] + 1
        a[2 * ws - 2] = D[ws - 1, ws - 2]
        a[2 * ws - 1] = coefficients.pop()
        a[2 * ws] = D[0, 0] + C[0, 0]
        a[3 * ws - 2] = E[ws - 1, ws - 2] + G[ws - 1, ws - 2] + H[ws - 1, ws - 2]
        a[3 * ws - 1] = C[0, 0] * D[0, 0] + C[0, 0] + D[0, 0] + D[ws - 1, ws - 2] * (E[ws - 1, ws - 2] + G[ws - 1, ws - 2] + H[ws - 1, ws - 2] + 1) + a[ws - 1] + 1
        a[3 * ws] = C[0, 0] + 1
        a[4 * ws - 2] = D[ws - 1, ws - 2]
        a[4 * ws - 1] = a[2 * ws - 1]

        assert len(coefficients) == 0

        A = matrix.block([
            [D, L, P, O],
            [K, E, Q, R],
            [zero, zero, G, M],
            [zero, zero, N, H]
        ])
        A.set_immutable()
        a.set_immutable()

        L = matrix.block(ring, [
            [one, zero, one, one],
            [zero, one, one, zero],
            [zero, zero, one, zero],
            [zero, zero, one, one]
        ])
        L.set_immutable()
        return A, a, L

    def random_self_equivalence(self, ring):
        """
        Generates a random type 2 affine self-equivalence of the function S(x, y) = (x + y, y).
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        assert ring == gf2

        while True:
            coefficients = [randint(0, 1) for _ in range(2 * self.word_size + 7)]
            # Make sure the first two coefficients are not zero at the same time.
            if not (coefficients[0] == 0 and coefficients[1] == 0):
                break

        return self.self_equivalence(ring, coefficients)


if __name__ == "__main__":
    from sage.all import SR

    word_size = 64
    ring = SR

    self_equivalence_provider = Type1AffineSelfEquivalenceProvider(word_size)
    coefficients = [ring(f"x{i}") for i in range(2 * word_size + 7)]
    A, a, B, b = self_equivalence_provider.self_equivalence(ring, coefficients)
    A_vars = set(A.variables())
    a_vars = set(sum([x.variables() for x in a], ()))
    B_vars = set(B.variables())
    b_vars = set(sum([x.variables() for x in b], ()))
    print(len(A_vars), len(a_vars), len(B_vars), len(b_vars), len(A_vars | a_vars | B_vars | b_vars))

    self_equivalence_provider = Type2AffineSelfEquivalenceProvider(word_size)
    coefficients = [ring(f"x{i}") for i in range(2 * word_size + 7)]
    A, a, B, b = self_equivalence_provider.self_equivalence(ring, coefficients)
    A_vars = set(A.variables())
    a_vars = set(sum([x.variables() for x in a], ()))
    B_vars = set(B.variables())
    b_vars = set(sum([x.variables() for x in b], ()))
    print(len(A_vars), len(a_vars), len(B_vars), len(b_vars), len(A_vars | a_vars | B_vars | b_vars))
