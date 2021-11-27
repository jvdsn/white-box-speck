import logging
import os
import sys
from itertools import product
from random import randint

from sage.all import GF
from sage.all import vector
from sage.rings.polynomial.pbori.pbori import BooleanPolynomialRing

path = os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__))))
if sys.path[1] != path:
    sys.path.insert(1, path)

from attacks import inverse_key_schedule
from white_box_speck.external_encodings import random_linear_external_encoding
from white_box_speck.self_equivalences.anf import AffineSelfEquivalenceProvider
from white_box_speck.self_equivalences.anf import LinearSelfEquivalenceProvider
from white_box_speck import WhiteBoxSpeck

gf2 = GF(2)


def recover_coefficients_affine(sep, ring, M_, M, A, B, v_, v, a, b):
    # We use M' * B = A * M instead of M' = A * M * B^-1.
    # Sage has issues with calculating the inverse of a matrix in a BPR.
    left = M_ * B
    right = A * M
    f = []
    for row in range(left.nrows()):
        for col in range(left.ncols()):
            f.append(left[row, col] + right[row, col])

    basis = ring.ideal(f).groebner_basis()
    c = {}
    extra = []
    for p in basis:
        if p.n_vars() == 1:
            c[p.variable(0)] = p.constant_coefficient()
        else:
            extra.append(p)

    # The recovered coefficients and quotient ring can be used to fully determine A and B.
    quot = ring.quotient_ring(ring.ideal(extra))
    v = v.change_ring(quot)
    A = sep._subs_matrix(quot, A, c).change_ring(gf2)
    B = sep._subs_matrix(quot, B, c).change_ring(gf2)
    # Additionally, we greatly simplify a and b.
    a = sep._subs_vector(quot, a, c)
    b = B.inverse() * sep._subs_vector(quot, b, c)

    # We couldn't use v previously, because we would have to calculate B^-1.
    # Sage has issues with calculating the inverse of a matrix in a BPR.
    left = v_
    right = A * (M * (v + b)) + a
    f = basis[:]
    for i in range(len(left)):
        f.append(left[i] + right[i])

    basis = ring.ideal(f).groebner_basis()
    c = {}
    extra = []
    for p in basis:
        if p.n_vars() == 1:
            c[p.variable(0)] = p.constant_coefficient()
        else:
            extra.append(p)

    # We have to guess here, no more information.
    print(c)
    print(extra[0].variables())
    assert len(c) == ring.ngens() - 2
    assert len(extra) == 1 and extra[0].n_vars() == 2
    v = extra[0].variable(0)
    p1 = extra[0].subs({v: 0})
    p2 = extra[0].subs({v: 1})
    c1 = c | {v: 0, p1.variable(0): p1.constant_coefficient()}
    c2 = c | {v: 1, p2.variable(0): p2.constant_coefficient()}
    return [c1, c2]


def attack_affine_encodings(block_size, key_size, matrices, vectors):
    """
    Recovers the master key and affine external encodings from the encoded matrices and vectors.
    :param block_size: the block size
    :param key_size: the key size
    :param matrices: the encoded matrices
    :param vectors: the encoded vectors
    :return: a generator generating tuples containing the master key, the input external encoding, and the output external encoding
    """
    word_size = block_size // 2
    key_words = key_size // word_size
    key = [0] * key_words
    wbs = WhiteBoxSpeck(block_size, key_size, key)
    sep = AffineSelfEquivalenceProvider(word_size)

    rotate_x_right = wbs._rotate_right_matrix(wbs.alpha, 0)
    rotate_y_left = wbs._rotate_left_matrix(0, wbs.beta)
    xor_xy = wbs._xor_xy_matrix()
    m_mid = rotate_x_right * xor_xy * rotate_y_left
    m_last = xor_xy * rotate_y_left

    k_names = [f"k{i}" for i in range(word_size)]
    I_names = [f"I{i}" for i in range(sep.coefficients_size)]
    O_names = [f"O{i}" for i in range(sep.coefficients_size)]
    ring = BooleanPolynomialRing(names=k_names + I_names + O_names)
    I_coefficients = {sep_coefficient: ring(I_name) for sep_coefficient, I_name in zip(sep.coefficients, I_names)}
    O_coefficients = {sep_coefficient: ring(O_name) for sep_coefficient, O_name in zip(sep.coefficients, O_names)}
    A = sep._subs_matrix(ring, sep.A, O_coefficients)
    B = sep._subs_matrix(ring, sep.B, I_coefficients)
    v = vector(ring, [ring(k_name) for k_name in k_names] + [0] * word_size)
    a = sep._subs_vector(ring, sep.a, O_coefficients)
    b = sep._subs_vector(ring, sep.b, I_coefficients)

    # This list contains lists of maps: guesses of recovered coefficients.
    recovered_coefficients_guesses = []
    recovered_coefficients_guesses.append(recover_coefficients_affine(sep, ring, matrices[2], m_mid, A, B, vectors[2], v, a, b))
    for i in range(3, key_words + 2):
        recovered_coefficients_guesses.append(recover_coefficients_affine(sep, ring, matrices[i], m_mid, A, B, vectors[i], v, a, b))
    recovered_coefficients_guesses.append(recover_coefficients_affine(sep, ring, matrices[wbs.rounds - 1], m_mid, A, B, vectors[wbs.rounds - 1], v, a, b))
    print(key_words, len(recovered_coefficients_guesses))

    # Here, recovered_coefficients will be a tuple of maps, representing a possible guessed configuration.
    for recovered_coefficients in product(*recovered_coefficients_guesses):
        k = []
        for r in range(key_words):
            k.append(0)
            for j in range(word_size):
                k[r] |= int(recovered_coefficients[r][ring(k_names[j])]) << j

        # We need skipped=1 here because we recovered the k coefficients for r = 1, 2, ..., m.
        key = inverse_key_schedule(word_size, wbs.alpha, wbs.beta, k, skipped=1)

        # We need the full key expansion to recover the constant parts of the external encodings.
        k = wbs._key_expansion(key)

        # Recovering the input external encoding.
        c = {ring(O_name): recovered_coefficients[0][ring(I_name)] for I_name, O_name in zip(I_names, O_names)}
        O = sep._subs_matrix(gf2, A, c)
        o = sep._subs_vector(gf2, a, c)
        v = wbs._xor_round_key_vector(k[0])
        input_external_encoding_matrix = (O * m_mid).inverse() * matrices[1]
        input_external_encoding_vector = (O * m_mid).inverse() * (vectors[1] + o) + v
        input_external_encoding = (input_external_encoding_matrix, input_external_encoding_vector)

        # Recovering the output external encoding.
        c = {ring(I_name): recovered_coefficients[key_words][ring(O_name)] for I_name, O_name in zip(I_names, O_names)}
        I = sep._subs_matrix(gf2, B, c).inverse()
        i = I * sep._subs_vector(gf2, b, c)
        v = wbs._xor_round_key_vector(k[wbs.rounds - 1])
        output_external_encoding_matrix = matrices[wbs.rounds] * (m_last * I).inverse()
        output_external_encoding_vector = output_external_encoding_matrix * m_last * (v + i) + vectors[wbs.rounds]
        output_external_encoding = (output_external_encoding_matrix, output_external_encoding_vector)

        yield key, input_external_encoding, output_external_encoding


def attack_affine_encodings_test(block_size, key_size):
    logging.info(f"Setting up attack on affine self-equivalence encodings with Speck{block_size}/{key_size}...")
    word_size = block_size // 2
    key_words = key_size // word_size
    key = [randint(0, 2 ** word_size) for _ in range(key_words)]
    wbs = WhiteBoxSpeck(block_size, key_size, key)
    input_external_encoding = random_linear_external_encoding(word_size)
    output_external_encoding = random_linear_external_encoding(word_size)
    matrices, vectors = wbs.affine_layers(input_external_encoding, output_external_encoding, AffineSelfEquivalenceProvider(word_size))

    logging.info(f"Testing attack on affine self-equivalence encodings with Speck{block_size}/{key_size}...")
    for key_, input_external_encoding_, output_external_encoding_ in attack_affine_encodings(block_size, key_size, matrices, vectors):
        if key_ == key and input_external_encoding_ == input_external_encoding and output_external_encoding_ == output_external_encoding:
            logging.info(f"Recovered key? {key_ == key}")
            logging.info(f"Recovered input external encoding? {input_external_encoding_ == input_external_encoding}")
            logging.info(f"Recovered output external encoding? {output_external_encoding_ == output_external_encoding}")
            break
    else:
        logging.info(f"Recovered key? {False}")
        logging.info(f"Recovered input external encoding? {False}")
        logging.info(f"Recovered output external encoding? {False}")


def recover_coefficients_linear(ring, M_, M, A, B):
    # We use M' * B = A * M instead of M' = A * M * B^-1.
    # Sage has issues with calculating the inverse of a matrix in a BPR.
    left = M_ * B
    right = A * M
    f = []
    for row in range(left.nrows()):
        for col in range(left.ncols()):
            f.append(left[row, col] + right[row, col])

    basis = ring.ideal(f).groebner_basis()
    c = {}
    for p in basis:
        assert p.n_vars() == 1
        c[p.variable(0)] = p.constant_coefficient()

    assert len(c) == ring.ngens()
    return c


def attack_linear_encodings(block_size, key_size, matrices, vectors):
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

    I_names = [f"I{i}" for i in range(sep.coefficients_size)]
    O_names = [f"O{i}" for i in range(sep.coefficients_size)]
    ring = BooleanPolynomialRing(names=I_names + O_names)
    I_coefficients = {sep_coefficient: ring(I_name) for sep_coefficient, I_name in zip(sep.coefficients, I_names)}
    O_coefficients = {sep_coefficient: ring(O_name) for sep_coefficient, O_name in zip(sep.coefficients, O_names)}
    A = sep._subs_matrix(ring, sep.A, O_coefficients)
    B = sep._subs_matrix(ring, sep.B, I_coefficients)

    # We store the coefficients for efficiency reasons (but it probably doesn't matter too much).
    recovered_coefficients = []
    recovered_coefficients.append(recover_coefficients_linear(ring, matrices[2], m_mid, A, B))
    for i in range(3, key_words + 2):
        recovered_coefficients.append(recover_coefficients_linear(ring, matrices[i], m_mid, A, B))
    recovered_coefficients.append(recover_coefficients_linear(ring, matrices[wbs.rounds - 1], m_mid, A, B))

    # Recovering the round keys.
    k = []
    for r in range(key_words):
        c = {ring(O_name): recovered_coefficients[r][ring(I_name)] for I_name, O_name in zip(I_names, O_names)}
        O = sep._subs_matrix(gf2, A, c)
        v = (O * m_mid).inverse() * vectors[r + 1]
        k.append(0)
        for j in range(word_size):
            k[r] |= int(v[j]) << j

    key = inverse_key_schedule(word_size, wbs.alpha, wbs.beta, k)

    # Recovering the input external encoding.
    c = {ring(O_name): recovered_coefficients[0][ring(I_name)] for I_name, O_name in zip(I_names, O_names)}
    O = sep._subs_matrix(gf2, A, c)
    input_external_encoding = (O * m_mid).inverse() * matrices[1]
    input_external_encoding = (input_external_encoding, vector(gf2, 2 * word_size))

    # Recovering the output external encoding.
    c = {ring(I_name): recovered_coefficients[key_words][ring(O_name)] for I_name, O_name in zip(I_names, O_names)}
    I = sep._subs_matrix(gf2, B, c).inverse()
    output_external_encoding = matrices[wbs.rounds] * (m_last * I).inverse()
    output_external_encoding = (output_external_encoding, vector(gf2, 2 * word_size))

    return key, input_external_encoding, output_external_encoding


def attack_linear_encodings_test(block_size, key_size):
    logging.info(f"Setting up attack on linear self-equivalence encodings with Speck{block_size}/{key_size}...")
    word_size = block_size // 2
    key_words = key_size // word_size
    key = [randint(0, 2 ** word_size) for _ in range(key_words)]
    wbs = WhiteBoxSpeck(block_size, key_size, key)
    input_external_encoding = random_linear_external_encoding(word_size)
    output_external_encoding = random_linear_external_encoding(word_size)
    matrices, vectors = wbs.affine_layers(input_external_encoding, output_external_encoding, LinearSelfEquivalenceProvider(word_size))

    logging.info(f"Testing attack on linear self-equivalence encodings with Speck{block_size}/{key_size}...")
    key_, input_external_encoding_, output_external_encoding_ = attack_linear_encodings(block_size, key_size, matrices, vectors)
    logging.info(f"Recovered key? {key_ == key}")
    logging.info(f"Recovered input external encoding? {input_external_encoding_ == input_external_encoding}")
    logging.info(f"Recovered output external encoding? {output_external_encoding_ == output_external_encoding}")


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s %(message)s', datefmt='%Y-%m-%d,%H:%M:%S', level=logging.INFO)

#    attack_linear_encodings_test(32, 64)
#    attack_linear_encodings_test(48, 72)
#    attack_linear_encodings_test(48, 96)
#    attack_linear_encodings_test(64, 96)
#    attack_linear_encodings_test(64, 128)
#    attack_linear_encodings_test(96, 96)
#    attack_linear_encodings_test(96, 144)
#    attack_linear_encodings_test(128, 128)
#    attack_linear_encodings_test(128, 192)
#    attack_linear_encodings_test(128, 256)
    attack_affine_encodings_test(32, 64)
    attack_affine_encodings_test(48, 72)
    attack_affine_encodings_test(48, 96)
    attack_affine_encodings_test(64, 96)
    attack_affine_encodings_test(64, 128)
    attack_affine_encodings_test(96, 96)
    attack_affine_encodings_test(96, 144)
    attack_affine_encodings_test(128, 128)
    attack_affine_encodings_test(128, 192)
    attack_affine_encodings_test(128, 256)
