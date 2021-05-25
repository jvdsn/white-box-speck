from abc import ABC
from abc import abstractmethod


class CodeGenerator(ABC):
    """
    Generates output C code for white-box Speck implementations.
    """

    _WORD_TYPES = {
        16: "uint16_t",
        32: "uint32_t",
        64: "uint64_t",
    }

    _WORD_IN_TYPES = {
        16: "SCNx16",
        32: "SCNx32",
        64: "SCNx64",
    }

    _WORD_OUT_TYPES = {
        16: "PRIx16",
        32: "PRIx32",
        64: "PRIx64",
    }

    _INCLUDE_INTTYPES = "#include <inttypes.h>\n"
    _INCLUDE_STDDEF = "#include <stddef.h>\n"
    _INCLUDE_STDIO = "#include <stdio.h>\n"
    _INCLUDE_STRING = "#include <string.h>\n"

    _FROM_BITS = (
        "void from_bits(uint8_t bits[BLOCK_SIZE], WORD_TYPE *x, WORD_TYPE *y) {\n"
        "    *x = 0;\n"
        "    *y = 0;\n"
        "    for (size_t i = 0; i < WORD_SIZE; i++) {\n"
        "        *x |= ((WORD_TYPE) bits[i]) << i;\n"
        "        *y |= ((WORD_TYPE) bits[WORD_SIZE + i]) << i;\n"
        "    }\n"
        "}\n"
    )

    _TO_BITS = (
        "void to_bits(WORD_TYPE x, WORD_TYPE y, uint8_t bits[BLOCK_SIZE]) {\n"
        "    for (size_t i = 0; i < WORD_SIZE; i++) {\n"
        "        bits[i] = (x >> i) & 1;\n"
        "        bits[WORD_SIZE + i] = (y >> i) & 1;\n"
        "    }\n"
        "}\n"
    )

    _MATRIX_VECTOR_PRODUCT = (
        "void matrix_vector_product(uint8_t matrix[BLOCK_SIZE][BLOCK_SIZE], uint8_t xy[BLOCK_SIZE], uint8_t res[BLOCK_SIZE]) {\n"
        "    for (size_t i = 0; i < BLOCK_SIZE; i++) {\n"
        "        for (size_t j = 0; j < BLOCK_SIZE; j++) {\n"
        "            res[i] ^= matrix[i][j] * xy[j];\n"
        "        }\n"
        "    }\n"
        "}\n"
    )

    _VECTOR_ADDITION = (
        "void vector_addition(uint8_t vector[BLOCK_SIZE], uint8_t xy[BLOCK_SIZE]) {\n"
        "    for (size_t i = 0; i < BLOCK_SIZE; i++) {\n"
        "        xy[i] ^= vector[i];\n"
        "    }\n"
        "}\n"
    )

    _MODULAR_ADDITION = (
        "void modular_addition(uint8_t xy[BLOCK_SIZE]) {\n"
        "    uint8_t carry = 0;\n"
        "    for (size_t i = 0; i < WORD_SIZE; i++) {\n"
        "        xy[i] = xy[i] + xy[WORD_SIZE + i] + carry;\n"
        "        carry = xy[i] > 1;\n"
        "        xy[i] &= 1;\n"
        "    }\n"
        "}\n"
    )

    _ENCRYPT = (
        "void encrypt(WORD_TYPE p[2], WORD_TYPE c[2]) {\n"
        "    uint8_t xy[BLOCK_SIZE];\n"
        "    uint8_t res[BLOCK_SIZE];\n"
        "    to_bits(p[0], p[1], xy);\n"
        "    for (size_t i = 0; i < ROUNDS; i++) {\n"
        "        memset(&res, 0, BLOCK_SIZE * sizeof(uint8_t));\n"
        "        matrix_vector_product(MATRICES[i], xy, res);\n"
        "        vector_addition(VECTORS[i], res);\n"
        "        modular_addition(res);\n"
        "        memcpy(&xy, &res, BLOCK_SIZE * sizeof(uint8_t));\n"
        "    }\n"
        "\n"
        "    memset(&res, 0, BLOCK_SIZE * sizeof(uint8_t));\n"
        "    matrix_vector_product(MATRICES[ROUNDS], xy, res);\n"
        "    vector_addition(VECTORS[ROUNDS], res);\n"
        "    from_bits(res, &c[0], &c[1]);\n"
        "}\n"
    )

    def _includes(self):
        return self._INCLUDE_INTTYPES + \
               self._INCLUDE_STDDEF + \
               self._INCLUDE_STDIO + \
               self._INCLUDE_STRING

    def _define_block_size(self, block_size):
        return f"#define BLOCK_SIZE {block_size}\n"

    def _define_word_size(self, word_size):
        return f"#define WORD_SIZE {word_size}\n"

    def _define_word_type(self, word_size):
        assert word_size in self._WORD_TYPES, f"Invalid or unsupported word size {word_size}"

        return f"#define WORD_TYPE {self._WORD_TYPES[word_size]}\n"

    def _define_word_in_type(self, word_size):
        assert word_size in self._WORD_IN_TYPES, f"Invalid or unsupported word size {word_size}"

        return f"#define WORD_IN_TYPE {self._WORD_IN_TYPES[word_size]}\n"

    def _define_word_out_type(self, word_size):
        assert word_size in self._WORD_OUT_TYPES, f"Invalid or unsupported word size {word_size}"

        return f"#define WORD_OUT_TYPE {self._WORD_OUT_TYPES[word_size]}\n"

    def _define_rounds(self, rounds):
        return f"#define ROUNDS {rounds}\n"

    def _defines(self, block_size, word_size, rounds):
        return self._define_block_size(block_size) + \
               self._define_word_size(word_size) + \
               self._define_word_type(word_size) + \
               self._define_word_in_type(word_size) + \
               self._define_word_out_type(word_size) + \
               self._define_rounds(rounds)

    @abstractmethod
    def _matrices(self, matrices):
        pass

    @abstractmethod
    def _vectors(self, vectors):
        pass

    def _functions(self, block_size, word_size, rounds):
        return self._FROM_BITS + \
               "\n" + \
               self._TO_BITS + \
               "\n" + \
               self._MATRIX_VECTOR_PRODUCT + \
               "\n" + \
               self._VECTOR_ADDITION + \
               "\n" + \
               self._MODULAR_ADDITION + \
               "\n" + \
               self._ENCRYPT

    def _main(self):
        return (
            f"int main(int argc, char *argv[]) {{\n"
            f"    WORD_TYPE p[2];\n"
            f"    WORD_TYPE c[2];\n"
            f"    if (argc < 3) {{\n"
            f"        return -1;\n"
            f"    }} else {{\n"
            f"        sscanf(argv[1], \"%\" WORD_IN_TYPE, &p[0]);\n"
            f"        sscanf(argv[2], \"%\" WORD_IN_TYPE, &p[1]);\n"
            f"        encrypt(p, c);\n"
            f"        printf(\"%\" WORD_OUT_TYPE \" %\" WORD_OUT_TYPE \"\\n\", c[0], c[1]);\n"
            f"    }}\n"
            f"}}\n"
        )

    def generate_code(self, matrices, vectors):
        assert len(matrices) > 0
        assert len(vectors) > 0
        assert len(matrices) == len(vectors)

        block_size = matrices[0].nrows()
        word_size = block_size // 2
        rounds = len(matrices) - 1

        return self._includes() + \
               "\n" + \
               self._defines(block_size, word_size, rounds) + \
               "\n" + \
               self._matrices(matrices) + \
               "\n" + \
               self._vectors(vectors) + \
               "\n" + \
               self._functions(block_size, word_size, rounds) + \
               "\n" + \
               self._main()
