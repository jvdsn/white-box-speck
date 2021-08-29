from sage.all import matrix
from sage.all import vector

from self_equivalences import SelfEquivalenceProvider


class CombinedSelfEquivalenceProvider(SelfEquivalenceProvider):
    """
    Combines multiple delegate SelfEquivalenceProviders.
    """

    def __init__(self, word_size, delegates):
        """
        Initializes an instance of CombinedSelfEquivalenceProvider with the provided parameters.
        :param word_size: the word size
        :param delegates: the delegate SelfEquivalenceProviders
        """
        super().__init__(word_size)
        self.delegates = delegates

    def random_self_equivalence(self, ring):
        """
        Generates a random self-equivalence of the function S(x, y) = (x + y, y).
        This method combines random self-equivalences generated by each of the delegates to obtain the final self-equivalence.
        :param ring: the ring
        :return: a tuple of matrix A, vector a, matrix B, and vector b, such that S = (b o B) o S o (a o A)
        """
        A = matrix.identity(ring, 2 * self.word_size)
        a = vector(ring, 2 * self.word_size)
        B = matrix.identity(ring, 2 * self.word_size)
        b = vector(ring, 2 * self.word_size)
        for delegate in self.delegates:
            assert delegate.word_size == self.word_size, "Delegates should have the same word size"

            A_, a_, B_, b_ = delegate.random_self_equivalence(ring)
            A, a, B, b = A * A_, A * a_ + a, B_ * B, B_ * b + b_

        return A, a, B, b
