from random import randint

from sage.all import GF
from sage.all import vector

import external_encodings
from self_equivalences.linear import LinearSelfEquivalenceProvider
from white_box_speck import WhiteBoxSpeck

gf2 = GF(2)


def inverse_key_schedule(word_size, alpha, beta, k):
    """
    Computes the inverse key schedule for Speck.
    :param word_size: the word size
    :param alpha: the parameter alpha
    :param beta: the parameter beta
    :param k: the array k containing the first round keys
    """
    key = [k[0]]
    word_size_mod = 2 ** word_size
    for i in range(len(k) - 1):
        l = (((k[i] << beta) % word_size_mod) | (k[i] >> (word_size - beta))) ^ k[i + 1]
        l = ((l ^ i) - k[i]) % word_size_mod
        l = (((l << alpha) % word_size_mod) | (l >> (word_size - alpha)))
        key.append(l)
    return key[::-1]


def recover_coefficients_linear_1(word_size, alpha, beta, M):
    """
    Recovers the coefficients used to generate the linear input encoding from an encoded matrix.
    :param word_size: the word size
    :param alpha: the parameter alpha
    :param beta: the parameter beta
    :param M: the encoded matrix
    """
    c = vector(gf2, 2 * word_size)
    for i in range(1, word_size - 1):
        c[2 * word_size - 1 - i] = M[word_size - 1 - alpha][word_size + i]
        c[word_size - i] = M[word_size - 1 + beta][word_size + i] + c[2 * word_size - 1 - i]

    c[1] = M[word_size - 1 - alpha][word_size]
    c[word_size] = M[word_size - 1 + beta][word_size] + c[1]
    c[2 * word_size - 1] = M[word_size - 1 - alpha][0] + c[1]
    c[0] = M[word_size - 1 + beta][0] + c[word_size] + c[2 * word_size - 1]
    return list(map(lambda x: int(x), c))


def recover_coefficients_linear_2(word_size, O):
    """
    Recovers the coefficients used to generate the linear output encoding from the output encoding.
    :param word_size: the word size
    :param O: the output encoding
    """
    c = vector(gf2, 2 * word_size)
    for i in range(1, word_size - 1):
        c[word_size - i] = O[word_size - 1][word_size + i]
        c[2 * word_size - 1 - i] = O[2 * word_size - 1][word_size + i] + c[word_size - i]
    c[word_size] = O[word_size - 1][0] + O[word_size - 1][word_size]
    c[1] = O[2 * word_size - 1][0] + O[2 * word_size - 1][word_size] + c[word_size]
    c[0] = O[word_size - 1][word_size] + c[1]
    c[2 * word_size - 1] = O[2 * word_size - 1][word_size] + O[word_size - 1][word_size]
    return list(map(lambda x: int(x), c))


def attack_linear_encodings(block_size, key_size, matrices, vectors):
    """
    Recovers the master key and linear external encodings from the encoded matrices and vectors.
    :param block_size: the block size
    :param key_size: the key size
    :param matrices: the encoded matrices
    :param vectors: the encoded vectors
    """
    word_size = block_size // 2
    key_words = key_size // word_size
    key = [0] * key_words
    wb = WhiteBoxSpeck(block_size, key_size, key)
    self_equivalence_provider = LinearSelfEquivalenceProvider(word_size)

    rotate_x_right = wb._rotate_right_matrix(wb.alpha, 0)
    rotate_y_left = wb._rotate_left_matrix(0, wb.beta)
    xor_xy = wb._xor_xy_matrix()

    c = recover_coefficients_linear_1(word_size, wb.alpha, wb.beta, matrices[2])
    O, _, _, _ = self_equivalence_provider.self_equivalence(gf2, c)
    input_external_encoding = (O * rotate_x_right * xor_xy * rotate_y_left) ** -1 * matrices[1]
    input_external_encoding = (input_external_encoding, vector(gf2, 2 * word_size))

    c = recover_coefficients_linear_1(word_size, wb.alpha, wb.beta, matrices[wb.rounds - 1])
    _, _, I, _ = self_equivalence_provider.self_equivalence(gf2, c)
    O = matrices[wb.rounds - 1] * (rotate_x_right * xor_xy * rotate_y_left * I) ** -1
    c = recover_coefficients_linear_2(word_size, O)
    _, _, I, _ = self_equivalence_provider.self_equivalence(gf2, c)
    output_external_encoding = matrices[wb.rounds] * (xor_xy * rotate_y_left * I) ** -1
    output_external_encoding = (output_external_encoding, vector(gf2, 2 * word_size))

    k = []
    for i in range(key_words):
        c = recover_coefficients_linear_1(word_size, wb.alpha, wb.beta, matrices[i + 2])
        O, _, _, _ = self_equivalence_provider.self_equivalence(gf2, c)
        v = (O * rotate_x_right * xor_xy * rotate_y_left) ** -1 * vectors[i + 1]
        k.append(0)
        for j in range(word_size):
            k[i] |= int(v[j]) << j

    key = inverse_key_schedule(word_size, wb.alpha, wb.beta, k)
    return key, input_external_encoding, output_external_encoding


def test_attack_linear_encodings(block_size, key_size):
    print(f"Testing attack on linear self-equivalence encodings with Speck{block_size}/{key_size}")
    word_size = block_size // 2
    key_words = key_size // word_size
    key = []
    for _ in range(key_words):
        key.append(randint(0, 2 ** word_size))

    wb = WhiteBoxSpeck(block_size, key_size, key)
    input_external_encoding = external_encodings.random_linear_external_encoding(word_size)
    output_external_encoding = external_encodings.random_linear_external_encoding(word_size)
    matrices, vectors = wb.affine_layers(input_external_encoding, output_external_encoding, LinearSelfEquivalenceProvider(word_size))
    key_, input_external_encoding_, output_external_encoding_ = attack_linear_encodings(block_size, key_size, matrices, vectors)
    print("Recovered key?", key_ == key)
    print("Recovered input external encoding?", input_external_encoding_ == input_external_encoding)
    print("Recovered output external encoding?", output_external_encoding_ == output_external_encoding)


if __name__ == "__main__":
    test_attack_linear_encodings(32, 64)
    test_attack_linear_encodings(48, 72)
    test_attack_linear_encodings(48, 96)
    test_attack_linear_encodings(64, 96)
    test_attack_linear_encodings(64, 128)
    test_attack_linear_encodings(96, 96)
    test_attack_linear_encodings(96, 144)
    test_attack_linear_encodings(128, 128)
    test_attack_linear_encodings(128, 192)
    test_attack_linear_encodings(128, 256)
