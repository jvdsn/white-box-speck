from code_generator import CodeGenerator


class BitPackedCodeGenerator(CodeGenerator):
    """
    Generates output C code for white-box Speck implementations using the bit-packed code generation strategy.
    """

    _WORD_CONSTANT_TYPES = {
        16: "UINT16_C",
        24: "UINT32_C",
        32: "UINT32_C",
        48: "UINT64_C",
        64: "UINT64_C",
    }

    _WORD_PARITY_FUNCTIONS = {
        16: "__builtin_parity",
        24: "__builtin_parityl",
        32: "__builtin_parityl",
        48: "__builtin_parityll",
        64: "__builtin_parityll",
    }

    _MATRIX_VECTOR_PRODUCT = (
        "void matrix_vector_product(WORD_TYPE matrix[BLOCK_SIZE][2], WORD_TYPE xy[2], WORD_TYPE res[2]) {\n"
        # We do a reverse loop here for performance reasons.
        "    for (size_t i = WORD_SIZE; i-- > 0;) {\n"
        "        res[0] = (res[0] << 1) | ((WORD_TYPE) WORD_PARITY_FUNCTION((matrix[i][0] & xy[0]) ^ (matrix[i][1] & xy[1])));\n"
        "        res[1] = (res[1] << 1) | ((WORD_TYPE) WORD_PARITY_FUNCTION((matrix[WORD_SIZE + i][0] & xy[0]) ^ (matrix[WORD_SIZE + i][1] & xy[1])));\n"
        "    }\n"
        "}\n"
    )

    _VECTOR_ADDITION = (
        "void vector_addition(WORD_TYPE vector[2], WORD_TYPE xy[2]) {\n"
        "    xy[0] ^= vector[0];\n"
        "    xy[1] ^= vector[1];\n"
        "}\n"
    )

    _MODULAR_ADDITION = (
        "void modular_addition(WORD_TYPE xy[2]) {\n"
        "    xy[0] = (xy[0] + xy[1]) & WORD_MASK;\n"
        "}\n"
    )

    _ENCRYPT = (
        "void encrypt(WORD_TYPE p[2], WORD_TYPE c[2]) {\n"
        "    WORD_TYPE res[2];\n"
        "    c[0] = p[0];\n"
        "    c[1] = p[1];\n"
        "    for (size_t i = 0; i < ROUNDS; i++) {\n"
        "        res[0] = 0;\n"
        "        res[1] = 0;\n"
        "        matrix_vector_product(MATRICES[i], c, res);\n"
        "        vector_addition(VECTORS[i], res);\n"
        "        modular_addition(res);\n"
        "        c[0] = res[0];\n"
        "        c[1] = res[1];\n"
        "    }\n"
        "\n"
        "    res[0] = 0;\n"
        "    res[1] = 0;\n"
        "    matrix_vector_product(MATRICES[ROUNDS], c, res);\n"
        "    vector_addition(VECTORS[ROUNDS], res);\n"
        "    c[0] = res[0];\n"
        "    c[1] = res[1];\n"
        "}\n"
    )

    def _to_int_big_endian(self, bits):
        ans = 0
        for b in reversed(bits):
            ans <<= 1
            ans |= int(b)

        return ans

    def _includes(self):
        return self._INCLUDE_INTTYPES + \
               self._INCLUDE_STDDEF + \
               self._INCLUDE_STDIO

    def _define_word_constant_type(self, word_size):
        assert word_size in self._WORD_TYPES, f"Invalid or unsupported word size {word_size}"

        return f"#define WORD_CONSTANT_TYPE {self._WORD_CONSTANT_TYPES[word_size]}\n"

    def _define_word_parity_function(self, word_size):
        assert word_size in self._WORD_PARITY_FUNCTIONS, f"Invalid or unsupported word size {word_size}"

        return f"#define WORD_PARITY_FUNCTION {self._WORD_PARITY_FUNCTIONS[word_size]}\n"

    def _define_word_mask(self, word_size):
        return f"#define WORD_MASK 0x{(1 << word_size) - 1:02x}\n"

    def _defines(self, block_size, word_size, rounds):
        return self._define_block_size(block_size) + \
               self._define_word_size(word_size) + \
               self._define_word_type(word_size) + \
               self._define_word_in_type(word_size) + \
               self._define_word_out_type(word_size) + \
               self._define_word_constant_type(word_size) + \
               self._define_word_parity_function(word_size) + \
               self._define_word_mask(word_size) + \
               self._define_rounds(rounds)

    def _matrices(self, matrices):
        s = "WORD_TYPE MATRICES[ROUNDS + 1][BLOCK_SIZE][2] = {\n"
        for k, matrix in enumerate(matrices):
            s += "    {"
            for i in range(matrix.nrows()):
                xpart = self._to_int_big_endian(matrix[i][:matrix.nrows() // 2])
                ypart = self._to_int_big_endian(matrix[i][matrix.nrows() // 2:])
                s += f"{{WORD_CONSTANT_TYPE({xpart}), WORD_CONSTANT_TYPE({ypart})}}"
                if i + 1 < matrix.nrows():
                    s += ", "
            s += "}"
            if k + 1 < len(matrices):
                s += ","
            s += "\n"
        s += "};\n"
        return s

    def _vectors(self, vectors):
        s = "WORD_TYPE VECTORS[ROUNDS + 1][2] = {"
        for k, vector in enumerate(vectors):
            xpart = self._to_int_big_endian(vector[:len(vector) // 2])
            ypart = self._to_int_big_endian(vector[len(vector) // 2:])
            s += f"{{WORD_CONSTANT_TYPE({xpart}), WORD_CONSTANT_TYPE({ypart})}}"
            if k + 1 < len(vectors):
                s += ", "
        s += "};\n"
        return s

    def _functions(self, block_size, word_size, rounds):
        return self._MATRIX_VECTOR_PRODUCT + \
               "\n" + \
               self._VECTOR_ADDITION + \
               "\n" + \
               self._MODULAR_ADDITION + \
               "\n" + \
               self._ENCRYPT
