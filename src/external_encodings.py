from sage.all import GF
from sage.all import random_matrix
from sage.all import random_vector
from sage.all import vector

from code_generator.bit_packed import BitPackedCodeGenerator

ring = GF(2)


def random_affine_external_encoding(word_size):
    """
    Generates a random affine external encoding.
    :return: a random matrix M and vector v
    """
    while True:
        M = random_matrix(ring, 2 * word_size)
        if M.det() != 0:
            v = random_vector(ring, 2 * word_size)
            return M, v


def random_linear_external_encoding(word_size):
    """
    Generates a random linear external encoding.
    The returned vector v will necessarily be a zero vector.
    :return: a random matrix M and vector v
    """
    while True:
        M = random_matrix(ring, 2 * word_size)
        if M.det() != 0:
            v = vector(ring, 2 * word_size)
            return M, v


class InputExternalEncodingCodeGenerator(BitPackedCodeGenerator):
    _MODULAR_SUBTRACTION = (
        "void modular_subtraction(WORD_TYPE xy[2]) {\n"
        "    xy[0] -= xy[1];\n"
        "}\n"
    )

    def _functions(self, block_size, word_size, rounds):
        return self._MATRIX_VECTOR_PRODUCT + \
               "\n" + \
               self._VECTOR_ADDITION + \
               "\n" + \
               self._MODULAR_ADDITION + \
               "\n" + \
               self._MODULAR_SUBTRACTION

    def _main(self):
        return (
            f"int main(int argc, char *argv[]) {{\n"
            f"    WORD_TYPE xy[2];\n"
            f"    WORD_TYPE res[2];\n"
            f"    if (argc < 3) {{\n"
            f"        return -1;\n"
            f"    }} else {{\n"
            f"        sscanf(argv[1], \"%\" WORD_IN_TYPE, &xy[0]);\n"
            f"        sscanf(argv[2], \"%\" WORD_IN_TYPE, &xy[1]);\n"
            f"        res[0] = 0;\n"
            f"        res[1] = 0;\n"
            f"        matrix_vector_product(MATRICES[0], xy, res);\n"
            f"        vector_addition(VECTORS[0], res);\n"
            f"        modular_addition(res);\n"
            f"        vector_addition(VECTORS[1], res);\n"
            f"        xy[0] = 0;\n"
            f"        xy[1] = 0;\n"
            f"        matrix_vector_product(MATRICES[1], res, xy);\n"
            f"        modular_subtraction(xy);\n"
            f"        vector_addition(VECTORS[2], xy);\n"
            f"        res[0] = 0;\n"
            f"        res[1] = 0;\n"
            f"        matrix_vector_product(MATRICES[2], xy, res);\n"
            f"        printf(\"%\" WORD_OUT_TYPE \" %\" WORD_OUT_TYPE \"\\n\", res[0], res[1]);\n"
            f"    }}\n"
            f"}}\n"
        )

    def generate_code_inverse_input_external_encoding(self, matrix0, vector0, external_encoding):
        matrix, vector = external_encoding
        return self.generate_code([matrix0, matrix ** -1, matrix0 ** -1], [vector0, vector, vector0])


class OutputExternalEncodingCodeGenerator(BitPackedCodeGenerator):
    def _functions(self, block_size, word_size, rounds):
        return self._MATRIX_VECTOR_PRODUCT + \
               "\n" + \
               self._VECTOR_ADDITION + \
               "\n" + \
               self._MODULAR_ADDITION

    def _main(self):
        return (
            f"int main(int argc, char *argv[]) {{\n"
            f"    WORD_TYPE xy[2];\n"
            f"    WORD_TYPE res[2];\n"
            f"    if (argc < 3) {{\n"
            f"        return -1;\n"
            f"    }} else {{\n"
            f"        sscanf(argv[1], \"%\" WORD_IN_TYPE, &xy[0]);\n"
            f"        sscanf(argv[2], \"%\" WORD_IN_TYPE, &xy[1]);\n"
            f"        vector_addition(VECTORS[0], xy);\n"
            f"        res[0] = 0;\n"
            f"        res[1] = 0;\n"
            f"        matrix_vector_product(MATRICES[0], xy, res);\n"
            f"        printf(\"%\" WORD_OUT_TYPE \" %\" WORD_OUT_TYPE \"\\n\", res[0], res[1]);\n"
            f"    }}\n"
            f"}}\n"
        )

    def generate_code_inverse_output_external_encoding(self, external_encoding):
        matrix, vector = external_encoding
        return self.generate_code([matrix ** -1], [vector])
