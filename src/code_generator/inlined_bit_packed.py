from code_generator.bit_packed import BitPackedCodeGenerator


class InlinedBitPackedCodeGenerator(BitPackedCodeGenerator):
    """
    Generates output C code for white-box Speck implementations using the inlined bit-packed code generation strategy.
    """

    _ENCRYPT = (
        "void encrypt(WORD_TYPE p[2], WORD_TYPE c[2]) {\n"
        "    WORD_TYPE res[2];\n"
        "    c[0] = p[0];\n"
        "    c[1] = p[1];\n"
        "    for (size_t i = 0; i < ROUNDS; i++) {\n"
        "        res[0] = 0;\n"
        "        res[1] = 0;\n"
        "        MATRIX_VECTOR_PRODUCTS[i](c, res);\n"
        "        VECTOR_ADDITIONS[i](res);\n"
        "        modular_addition(res);\n"
        "        c[0] = res[0];\n"
        "        c[1] = res[1];\n"
        "    }\n"
        "\n"
        "    res[0] = 0;\n"
        "    res[1] = 0;\n"
        "    MATRIX_VECTOR_PRODUCTS[ROUNDS](c, res);\n"
        "    VECTOR_ADDITIONS[ROUNDS](res);\n"
        "    c[0] = res[0];\n"
        "    c[1] = res[1];\n"
        "}\n"
    )

    def _matrices(self, matrices):
        s1 = ""
        s2 = "void (*MATRIX_VECTOR_PRODUCTS[ROUNDS + 1])(WORD_TYPE[2], WORD_TYPE[2]) = {"
        for k, matrix in enumerate(matrices):
            s1 += f"void matrix_vector_product_{k}(WORD_TYPE xy[2], WORD_TYPE res[2]) {{\n"
            word_size = matrix.nrows() // 2
            for i in range(word_size):
                s1 += "    res[0] |= (0"
                for j in range(word_size):
                    if matrix[i][j] != 0:
                        s1 += f" ^ ((xy[0] >> {j}) & 1)"
                for j in range(word_size):
                    if matrix[i][word_size + j] != 0:
                        s1 += f" ^ ((xy[1] >> {j}) & 1)"
                s1 += ") << %d;\n" % i
            for i in range(word_size):
                s1 += "    res[1] |= (0"
                for j in range(word_size):
                    if matrix[word_size + i][j] != 0:
                        s1 += f" ^ ((xy[0] >> {j}) & 1)"
                for j in range(word_size):
                    if matrix[word_size + i][word_size + j] != 0:
                        s1 += f" ^ ((xy[1] >> {j}) & 1)"
                s1 += f") << {i};\n"
            s1 += "}\n\n"

            s2 += f"matrix_vector_product_{k}"
            if k < len(matrices) - 1:
                s2 += ", "

        s2 += "};\n"
        return s1 + s2

    def _vectors(self, vectors):
        s1 = ""
        s2 = "void (*VECTOR_ADDITIONS[ROUNDS + 1])(WORD_TYPE[2]) = {"
        for k, vector in enumerate(vectors):
            xpart = self._to_int_big_endian(vector[:len(vector) // 2])
            ypart = self._to_int_big_endian(vector[len(vector) // 2:])
            s1 += f"void vector_addition_{k}(WORD_TYPE xy[2]) {{\n"
            s1 += f"    xy[0] ^= WORD_CONSTANT_TYPE({xpart});\n"
            s1 += f"    xy[1] ^= WORD_CONSTANT_TYPE({ypart});\n"
            s1 += "}\n\n"

            s2 += f"vector_addition_{k}"
            if k < len(vectors) - 1:
                s2 += ", "

        s2 += "};\n"
        return s1 + s2
