from code_generator import CodeGenerator


class DefaultCodeGenerator(CodeGenerator):
    """
    Generates output C code for white-box Speck implementations using the default code generation strategy.
    """

    def _matrices(self, matrices):
        s = "uint8_t MATRICES[ROUNDS + 1][BLOCK_SIZE][BLOCK_SIZE] = {\n"
        for k, matrix in enumerate(matrices):
            s += "    {\n"
            for i in range(matrix.nrows()):
                s += "        {"
                for j in range(matrix.ncols()):
                    s += str(matrix[i][j])
                    if j + 1 < matrix.ncols():
                        s += ", "
                s += "}"
                if i + 1 < matrix.nrows():
                    s += ","
                s += "\n"
            s += "    }"
            if k + 1 < len(matrices):
                s += ","
            s += "\n"
        s += "};\n"
        return s

    def _vectors(self, vectors):
        s = "uint8_t VECTORS[ROUNDS + 1][BLOCK_SIZE] = {\n"
        for k, vector in enumerate(vectors):
            s += "    {"
            for i in range(len(vector)):
                s += str(vector[i])
                if i + 1 < len(vector):
                    s += ", "
            s += "}"
            if k + 1 < len(vectors):
                s += ","
            s += "\n"
        s += "};\n"
        return s
