from sage.all import GF
from sage.all import matrix
from sage.all import vector


class WhiteBoxSpeck:
    """
    Class to generate matrices and vectors for a white-box Speck implementation.
    """
    _ROUNDS = {
        (32, 64): 22,
        (48, 72): 22,
        (48, 96): 23,
        (64, 96): 26,
        (64, 128): 27,
        (96, 96): 28,
        (96, 144): 29,
        (128, 128): 32,
        (128, 192): 33,
        (128, 256): 34,
    }

    def __init__(self, block_size, key_size, key):
        """
        Initializes an instance of WhiteBoxSpeck with the provided parameters.
        :param block_size: the block size
        :param key_size: the key size
        :param key: the key to protect
        """
        assert (block_size, key_size) in self._ROUNDS, f"Invalid or unsupported block size and key size combination: {block_size}/{key_size}"

        self.block_size = block_size
        self.key_size = key_size
        self.word_size = block_size // 2
        self.key_words = key_size // self.word_size
        self.rounds = self._ROUNDS[(block_size, key_size)]
        self.alpha = 7 if self.word_size == 16 else 8
        self.beta = 2 if self.word_size == 16 else 3

        assert len(key) == self.key_words, f"Expected {self.key_words} key words but got {len(key)} key words"

        self._k = self._key_expansion(key)

    def _key_expansion(self, key):
        """
        Performs Speck key expansion.
        :param key: the key
        :return: a list containing the round keys
        """
        k = key[self.key_words - 1:]
        l = key[self.key_words - 2::-1]
        for i in range(self.rounds - 1):
            x = l[i]
            y = k[i]

            # Round function is used to calculate round key.
            x = (x >> self.alpha) | ((x << (self.word_size - self.alpha)) % (2 ** self.word_size))
            x = (x + y) % (2 ** self.word_size)
            x ^= i
            y = ((y << self.beta) % (2 ** self.word_size)) | (y >> (self.word_size - self.beta))
            y ^= x

            l.append(x)
            k.append(y)

        return k

    def _rotate_right_matrix(self, x_pos, y_pos):
        """
        Returns a matrix which corresponds to a right bit rotation of x and y.
        :param x_pos: the amount of positions the x value should be rotated right
        :param y_pos: the amount of positions the y value should be rotated right
        :return: a matrix M such that Mv corresponds to a right bit rotation of x and y if v contains the bits of x and y (little endian)
        """
        m = matrix(GF(2), self.block_size)

        for i in range(self.word_size):
            # This corresponds to a right rotation of x_pos bits.
            m[i, (i + x_pos) % self.word_size] = 1
            # This corresponds to a right rotation of y_pos bits.
            m[self.word_size + i, self.word_size + (i + y_pos) % self.word_size] = 1

        return m

    def _rotate_left_matrix(self, x_pos, y_pos):
        """
        Returns a matrix which corresponds to a left bit rotation of x and y.
        :param x_pos: the amount of positions the x value should be rotated left
        :param y_pos: the amount of positions the y value should be rotated left
        :return: a matrix M such that Mv corresponds to a right bit rotation of x and y if v contains the bits of x and y (little endian)
        """
        # Left rotation is just right notation over negative positions.
        return self._rotate_right_matrix(-x_pos, -y_pos)

    def _xor_xy_matrix(self):
        """
        Returns a matrix which corresponds to y = x ^ y.
        :return: a matrix M such that Mv corresponds to y = x ^ y if v contains the bits of x and y (little endian)
        """
        m = matrix(GF(2), self.block_size)

        for i in range(self.word_size):
            # Output x bit at position i will be input x bit at position i.
            m[i, i] = 1
            # Output y bit at position i will be input x bit + input y bit at position i.
            m[self.word_size + i, i] = 1
            m[self.word_size + i, self.word_size + i] = 1

        return m

    def _xor_round_key_vector(self, k):
        """
        Returns a vector which corresponds to x = x ^ k.
        :param k: the round key
        :return: a vector w such that v ^ w corresponds to x = x ^ k if v contains the bits of x and y (little endian)
        """
        v = vector(GF(2), self.block_size)
        for i in range(self.word_size):
            v[i] = (k >> i) & 1

        return v

    def affine_layers(self, input_external_encoding, output_external_encoding, self_equivalence_provider):
        """
        Constructs the encoded matrices and vectors corresponding to the affine layers of Speck.
        :param input_external_encoding: the input external encoding, a tuple consisting of a matrix and a vector
        :param output_external_encoding: the output external encoding, a tuple consisting of a matrix and a vector
        :param self_equivalence_provider: the self-equivalence provider used to generate self-equivalences
        :return: a tuple containing the matrices and vectors
        """
        rotate_x_right = self._rotate_right_matrix(self.alpha, 0)
        rotate_y_left = self._rotate_left_matrix(0, self.beta)
        xor_xy = self._xor_xy_matrix()

        m_first = rotate_x_right
        m_mid = rotate_x_right * xor_xy * rotate_y_left
        m_last = xor_xy * rotate_y_left

        matrices = []
        vectors = []

        matrices.append(m_first)
        vectors.append(vector(GF(2), self.block_size))

        # No need to generate self-equivalences here as the previous layer does not contain any key material.
        matrices.append(m_mid * input_external_encoding[0])
        vectors.append(m_mid * (self._xor_round_key_vector(self._k[0]) + input_external_encoding[1]))

        for r in range(2, self.rounds + 1):
            # Generating self-equivalences and applying them to previous linear layer.
            O, o, I, i = self_equivalence_provider.random_self_equivalence()
            matrices[r - 1] = O * matrices[r - 1]
            vectors[r - 1] = O * vectors[r - 1] + o
            if r < self.rounds:
                matrices.append(m_mid * I)
                vectors.append(m_mid * (self._xor_round_key_vector(self._k[r - 1]) + i))
            else:
                matrices.append(m_last * I)
                vectors.append(m_last * (self._xor_round_key_vector(self._k[r - 1]) + i))

        matrices[self.rounds] = output_external_encoding[0] * matrices[self.rounds]
        vectors[self.rounds] = output_external_encoding[0] * vectors[self.rounds] + output_external_encoding[1]

        return matrices, vectors
