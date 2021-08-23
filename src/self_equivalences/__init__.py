from abc import ABC
from abc import abstractmethod


class SelfEquivalenceProvider(ABC):
    """
    Provides methods to generate self-equivalences of the function S(x, y) = (x + y, y).
    """

    @abstractmethod
    def __init__(self, ring, word_size):
        """
        Initializes an instance of SelfEquivalenceProvider with the provided parameters.
        :param ring: the ring
        :param word_size: the word size
        """
        self.ring = ring
        self.word_size = word_size

    @abstractmethod
    def random_self_equivalence(self):
        """
        Generates a random self-equivalence of the function S(x, y) = (x + y, y).
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        pass
