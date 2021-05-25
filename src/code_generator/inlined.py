from code_generator import CodeGenerator


class InlinedCodeGenerator(CodeGenerator):
    """
    Generates output C code for white-box Speck implementations using the inlined code generation strategy.
    """

    _ENCRYPT = (
        "void encrypt(WORD_TYPE p[2], WORD_TYPE c[2]) {\n"
        "    uint8_t xy[BLOCK_SIZE];\n"
        "    uint8_t res[BLOCK_SIZE];\n"
        "    to_bits(p[0], p[1], xy);\n"
        "    for (size_t i = 0; i < ROUNDS; i++) {\n"
        "        memset(&res, 0, BLOCK_SIZE * sizeof(uint8_t));\n"
        "        MATRIX_VECTOR_PRODUCTS[i](xy, res);\n"
        "        VECTOR_ADDITIONS[i](res);\n"
        "        modular_addition(res);\n"
        "        memcpy(&xy, &res, BLOCK_SIZE * sizeof(uint8_t));\n"
        "    }\n"
        "\n"
        "    memset(&res, 0, BLOCK_SIZE * sizeof(uint8_t));\n"
        "    MATRIX_VECTOR_PRODUCTS[ROUNDS](xy, res);\n"
        "    VECTOR_ADDITIONS[ROUNDS](res);\n"
        "    from_bits(res, &c[0], &c[1]);\n"
        "}\n"
    )

    def _matrices(self, matrices):
        s1 = ""
        s2 = "void (*MATRIX_VECTOR_PRODUCTS[ROUNDS + 1])(uint8_t[BLOCK_SIZE], uint8_t[BLOCK_SIZE]) = {"
        for k, matrix in enumerate(matrices):
            s1 += f"void matrix_vector_product_{k}(uint8_t xy[BLOCK_SIZE], uint8_t res[BLOCK_SIZE]) {{\n"
            for i in range(matrix.nrows()):
                s1 += f"    res[{i}] ^= 0"
                for j in range(matrix.ncols()):
                    if matrix[i][j] != 0:
                        s1 += f" ^ xy[{j}]"
                s1 += ";\n"
            s1 += "}\n\n"

            s2 += f"matrix_vector_product_{k}"
            if k < len(matrices) - 1:
                s2 += ", "

        s2 += "};\n"
        return s1 + s2

    def _vectors(self, vectors):
        s1 = ""
        s2 = "void (*VECTOR_ADDITIONS[ROUNDS + 1])(uint8_t[BLOCK_SIZE]) = {"
        for k, vector in enumerate(vectors):
            s1 += f"void vector_addition_{k}(uint8_t xy[BLOCK_SIZE]) {{\n"
            for i in range(len(vector)):
                if vector[i] != 0:
                    s1 += f"    xy[{i}] ^= 1;\n"
            s1 += "}\n\n"

            s2 += f"vector_addition_{k}"
            if k < len(vectors) - 1:
                s2 += ", "

        s2 += "};\n"
        return s1 + s2

    def _functions(self, block_size, word_size, rounds):
        return self._FROM_BITS + \
               "\n" + \
               self._TO_BITS + \
               "\n" + \
               self._MODULAR_ADDITION + \
               "\n" + \
               self._ENCRYPT
