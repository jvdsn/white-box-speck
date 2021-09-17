from . import CodeGenerator


class SparseMatrixCodeGenerator(CodeGenerator):
    """
    Generates output C code for white-box Speck implementations using the sparse matrix code generation strategy.
    """

    _MATRIX_VECTOR_PRODUCT = (
        "void matrix_vector_product(uint8_t sparse_matrix[][2], uint16_t sparse_matrix_entries, uint8_t xy[BLOCK_SIZE], uint8_t res[BLOCK_SIZE]) {\n"
        "    for (uint16_t i = 0; i < sparse_matrix_entries; i++) {\n"
        "        res[sparse_matrix[i][0]] ^= xy[sparse_matrix[i][1]];\n"
        "    }\n"
        "}\n"
    )

    _VECTOR_ADDITION = (
        "void vector_addition(uint8_t sparse_vector[], uint8_t sparse_vector_entries, uint8_t xy[BLOCK_SIZE]) {\n"
        "    for (uint8_t i = 0; i < sparse_vector_entries; i++) {\n"
        "        xy[sparse_vector[i]] ^= 1;\n"
        "    }\n"
        "}\n"
    )

    _ENCRYPT = (
        "void encrypt(WORD_TYPE p[2], WORD_TYPE c[2]) {\n"
        "    uint8_t xy[BLOCK_SIZE];\n"
        "    uint8_t res[BLOCK_SIZE];\n"
        "    to_bits(p[0], p[1], xy);\n"
        "    for (size_t i = 0; i < ROUNDS; i++) {\n"
        "        memset(&res, 0, BLOCK_SIZE);\n"
        "        matrix_vector_product(SPARSE_MATRICES[i], SPARSE_MATRIX_ENTRIES[i], xy, res);\n"
        "        vector_addition(SPARSE_VECTORS[i], SPARSE_VECTOR_ENTRIES[i], res);\n"
        "        modular_addition(res);\n"
        "        memcpy(&xy, &res, sizeof(res));\n"
        "    }\n"
        "\n"
        "    memset(&res, 0, BLOCK_SIZE);\n"
        "    matrix_vector_product(SPARSE_MATRICES[ROUNDS], SPARSE_MATRIX_ENTRIES[ROUNDS], xy, res);\n"
        "    vector_addition(SPARSE_VECTORS[ROUNDS], SPARSE_VECTOR_ENTRIES[ROUNDS], res);\n"
        "    from_bits(res, &c[0], &c[1]);\n"
        "}\n"
    )

    def _matrices(self, matrices):
        s = ""
        s1 = "uint16_t SPARSE_MATRIX_ENTRIES[ROUNDS + 1] = {"
        s2 = "uint8_t (*SPARSE_MATRICES[ROUNDS + 1])[2] = {"
        for k, matrix in enumerate(matrices):
            sparse_matrix = matrix.nonzero_positions()
            s += f"uint8_t SPARSE_MATRIX_{k}[{len(sparse_matrix)}][2] = {{"
            for l, (i, j) in enumerate(sparse_matrix):
                s += f"{{{i}, {j}}}"
                if l + 1 < len(sparse_matrix):
                    s += ", "
            s += "};\n"
            s1 += str(len(sparse_matrix))
            s2 += f"SPARSE_MATRIX_{k}"
            if k + 1 < len(matrices):
                s1 += ", "
                s2 += ", "

        s1 += "};\n"
        s2 += "};\n"
        return s + "\n" + s1 + "\n" + s2

    def _vectors(self, vectors):
        s = ""
        s1 = "uint8_t SPARSE_VECTOR_ENTRIES[ROUNDS + 1] = {"
        s2 = "uint8_t *SPARSE_VECTORS[ROUNDS + 1] = {"
        for k, vector in enumerate(vectors):
            sparse_vector = vector.nonzero_positions()
            s += f"uint8_t SPARSE_VECTOR_{k}[{len(sparse_vector)}] = {{"
            for l, i in enumerate(sparse_vector):
                s += f"{i}"
                if l + 1 < len(sparse_vector):
                    s += ", "
            s += "};\n"
            s1 += str(len(sparse_vector))
            s2 += f"SPARSE_VECTOR_{k}"
            if k + 1 < len(vectors):
                s1 += ", "
                s2 += ", "

        s1 += "};\n"
        s2 += "};\n"
        return s + "\n" + s1 + "\n" + s2
