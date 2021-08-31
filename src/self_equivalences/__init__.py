from abc import ABC
from abc import abstractmethod
from random import randint

from sage.all import GF


class SelfEquivalenceProvider(ABC):
    """
    Provides methods to generate self-equivalences of the function S(x, y) = (x + y, y).
    """

    @abstractmethod
    def __init__(self, word_size):
        """
        Initializes an instance of SelfEquivalenceProvider with the provided parameters.
        :param word_size: the word size
        """
        self.word_size = word_size

    @abstractmethod
    def random_self_equivalence(self, ring):
        """
        Generates a random self-equivalence of the function S(x, y) = (x + y, y).
        :param ring: the ring
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        pass


class CoefficientsSelfEquivalenceProvider(SelfEquivalenceProvider):
    """
    Provides methods to generate self-equivalences based on coefficients.
    """

    @abstractmethod
    def __init__(self, word_size, coefficients_size):
        """
        Initializes an instance of SelfEquivalenceProvider with the provided parameters.
        :param word_size: the word size
        :param coefficients_size: the number of coefficients required
        """
        self.word_size = word_size
        self.coefficients_size = coefficients_size

    def _check_constraints(self, coefficients):
        """
        Checks if the coefficients meet the constraints.
        :param coefficients: the coefficients
        :return: True if the coefficients meet the constraints, False otherwise
        """
        return len(coefficients) == self.coefficients_size

    @abstractmethod
    def self_equivalence(self, ring, coefficients):
        """
        Generates a self-equivalence of the function S(x, y) = (x + y, y) using coefficients.
        :param ring: the ring
        :param coefficients: the coefficients to use
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        :raises ValueError: if the coefficients do not meet the constraints
        """
        pass

    def random_self_equivalence(self, ring):
        """
        Generates a random self-equivalence of the function S(x, y) = (x + y, y).
        :param ring: the ring
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        assert ring == GF(2)

        while True:
            try:
                return self.self_equivalence(ring, [randint(0, 1) for _ in range(self.coefficients_size)])
            except ValueError:
                pass
