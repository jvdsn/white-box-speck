import logging
import os
import sys
from random import randint

from sage.all import GF
from sage.all import vector

path = os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__))))
if sys.path[1] != path:
    sys.path.insert(1, path)

from attacks import inverse_key_schedule
from white_box_speck.external_encodings import random_linear_external_encoding
from white_box_speck.self_equivalences.linear import LinearSelfEquivalenceProvider
from white_box_speck import WhiteBoxSpeck

gf2 = GF(2)


def recover_1(word_size, alpha, beta, M):
    """
    Recovers the coefficients used to generate the linear input encoding from an encoded matrix.
    :param word_size: the word size
    :param alpha: the parameter alpha
    :param beta: the parameter beta
    :param M: the encoded matrix
    :return: the coefficients
    """
    c = [0] * (2 * word_size)
    for i in range(1, word_size - 1):
        c[2 * word_size - 1 - i] = M[word_size - 1 - alpha][word_size + i]
        c[word_size - i] = M[word_size - 1 + beta][word_size + i] + c[2 * word_size - 1 - i]
    c[1] = M[word_size - 1 - alpha][word_size]
    c[word_size] = M[word_size - 1 + beta][word_size] + c[1]
    c[2 * word_size - 1] = M[word_size - 1 - alpha][0] + c[1]
    c[0] = M[word_size - 1 + beta][0] + c[word_size] + c[2 * word_size - 1]
    return c


def recover_2(word_size, O):
    """
    Recovers the coefficients used to generate the linear output encoding from the output encoding.
    :param word_size: the word size
    :param O: the output encoding
    :return: the coefficients
    """
    c = [0] * (2 * word_size)
    for i in range(1, word_size - 1):
        c[word_size - i] = O[word_size - 1][word_size + i]
        c[2 * word_size - 1 - i] = O[2 * word_size - 1][word_size + i] + c[word_size - i]
    c[word_size] = O[word_size - 1][0] + O[word_size - 1][word_size]
    c[1] = O[2 * word_size - 1][0] + O[2 * word_size - 1][word_size] + c[word_size]
    c[0] = O[word_size - 1][word_size] + c[1]
    c[2 * word_size - 1] = O[2 * word_size - 1][word_size] + O[word_size - 1][word_size]
    return c


def attack(block_size, key_size, matrices, vectors):
    """
    Recovers the master key and linear external encodings from the encoded matrices and vectors.
    :param block_size: the block size
    :param key_size: the key size
    :param matrices: the encoded matrices
    :param vectors: the encoded vectors
    :return: a tuple containing the master key, the input external encoding, and the output external encoding
    """
    word_size = block_size // 2
    key_words = key_size // word_size
    key = [0] * key_words
    wbs = WhiteBoxSpeck(block_size, key_size, key)
    sep = LinearSelfEquivalenceProvider(word_size)

    rotate_x_right = wbs._rotate_right_matrix(wbs.alpha, 0)
    rotate_y_left = wbs._rotate_left_matrix(0, wbs.beta)
    xor_xy = wbs._xor_xy_matrix()
    m_mid = rotate_x_right * xor_xy * rotate_y_left
    m_last = xor_xy * rotate_y_left

    # Recovering the round keys.
    k = []
    for r in range(key_words):
        c = recover_1(word_size, wbs.alpha, wbs.beta, matrices[r + 2])
        O, _, _, _ = sep.self_equivalence(gf2, c)
        v = (O * m_mid).inverse() * vectors[r + 1]
        k.append(0)
        for j in range(word_size):
            k[r] |= int(v[j]) << j

    key = inverse_key_schedule(word_size, wbs.alpha, wbs.beta, k)

    # Recovering the input external encoding.
    c = recover_1(word_size, wbs.alpha, wbs.beta, matrices[2])
    O, _, _, _ = sep.self_equivalence(gf2, c)
    input_external_encoding = (O * m_mid).inverse() * matrices[1]
    input_external_encoding = (input_external_encoding, vector(gf2, 2 * word_size))

    # Recovering the output external encoding.
    c = recover_1(word_size, wbs.alpha, wbs.beta, matrices[wbs.rounds - 1])
    _, _, I, _ = sep.self_equivalence(gf2, c)
    # O is the output encoding of the second-to-last round.
    O = matrices[wbs.rounds - 1] * (m_mid * I).inverse()
    # We need to recover the coefficients of the input encoding of the last round from O.
    c = recover_2(word_size, O)
    _, _, I, _ = sep.self_equivalence(gf2, c)
    output_external_encoding = matrices[wbs.rounds] * (m_last * I).inverse()
    output_external_encoding = (output_external_encoding, vector(gf2, 2 * word_size))

    return key, input_external_encoding, output_external_encoding


def attack_test(block_size, key_size):
    logging.info(f"Setting up attack on linear self-equivalence encodings with Speck{block_size}/{key_size}...")
    word_size = block_size // 2
    key_words = key_size // word_size
    key = [randint(0, 2 ** word_size) for _ in range(key_words)]
    wbs = WhiteBoxSpeck(block_size, key_size, key)
    input_external_encoding = random_linear_external_encoding(word_size)
    output_external_encoding = random_linear_external_encoding(word_size)
    matrices, vectors = wbs.affine_layers(input_external_encoding, output_external_encoding, LinearSelfEquivalenceProvider(word_size))

    logging.info(f"Testing attack on linear self-equivalence encodings with Speck{block_size}/{key_size}...")
    key_, input_external_encoding_, output_external_encoding_ = attack(block_size, key_size, matrices, vectors)
    logging.info(f"Recovered key? {key_ == key}")
    logging.info(f"Recovered input external encoding? {input_external_encoding_ == input_external_encoding}")
    logging.info(f"Recovered output external encoding? {output_external_encoding_ == output_external_encoding}")


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s %(message)s', datefmt='%Y-%m-%d,%H:%M:%S', level=logging.INFO)

    attack_test(32, 64)
    attack_test(48, 72)
    attack_test(48, 96)
    attack_test(64, 96)
    attack_test(64, 128)
    attack_test(96, 96)
    attack_test(96, 144)
    attack_test(128, 128)
    attack_test(128, 192)
    attack_test(128, 256)
