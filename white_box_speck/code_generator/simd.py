from .bit_packed import BitPackedCodeGenerator


class SIMDCodeGenerator(BitPackedCodeGenerator):
    """
    Generates output C code for white-box Speck implementations using the SIMD code generation strategy.
    """

    # TODO: make this value configurable
    _SIMD_SIZE = 256

    _SIMD_SET1S = {
        16: "_mm256_set1_epi16",
        32: "_mm256_set1_epi32",
        64: "_mm256_set1_epi64x",
    }

    _INCLUDE_IMMINTRIN = "#include <immintrin.h>\n"

    def _includes(self):
        return self._INCLUDE_INTTYPES + \
               self._INCLUDE_STDDEF + \
               self._INCLUDE_STDIO + \
               self._INCLUDE_STDLIB + \
               self._INCLUDE_IMMINTRIN

    def _define_simd_packed_count(self, simd_packed_count):
        return f"#define SIMD_PACKED_COUNT {simd_packed_count}\n"

    def _define_simd_type(self):
        return f"#define SIMD_TYPE __m256i\n"

    def _define_simd_set1(self, word_size):
        assert word_size in self._SIMD_SET1S, f"Unsupported word size {word_size}"

        return f"#define SIMD_SET1 {self._SIMD_SET1S[word_size]}\n"

    def _define_simd_and(self):
        return f"#define SIMD_AND _mm256_and_si256\n"

    def _define_simd_xor(self):
        return f"#define SIMD_XOR _mm256_xor_si256\n"

    def _defines(self, block_size, word_size, rounds):
        simd_packed_count = self._SIMD_SIZE // word_size
        return self._define_block_size(block_size) + \
               self._define_word_size(word_size) + \
               self._define_word_type(word_size) + \
               self._define_word_in_type(word_size) + \
               self._define_word_out_type(word_size) + \
               self._define_word_constant_type(word_size) + \
               self._define_word_parity_function(word_size) + \
               self._define_word_mask(word_size) + \
               self._define_rounds(rounds) + \
               self._define_simd_packed_count(simd_packed_count) + \
               self._define_simd_type() + \
               self._define_simd_set1(word_size) + \
               self._define_simd_and() + \
               self._define_simd_xor()

    def _matrices(self, matrices):
        s = (
            "typedef union simd_union {\n"
            "    WORD_TYPE words[SIMD_PACKED_COUNT];\n"
            "    SIMD_TYPE simd;\n"
            "} simd_union;\n"
            "\n"
        )

        s += "simd_union MATRICES[ROUNDS + 1][BLOCK_SIZE / SIMD_PACKED_COUNT][2] = {\n"
        for k, matrix in enumerate(matrices):
            s += "    {"
            simd_packed_count = self._SIMD_SIZE // (matrix.nrows() // 2)
            for i in range(0, matrix.nrows(), simd_packed_count):
                xparts = []
                yparts = []
                for j in range(simd_packed_count):
                    xparts.append(self._to_int_big_endian(matrix[i + j][:matrix.nrows() // 2]))
                    yparts.append(self._to_int_big_endian(matrix[i + j][matrix.nrows() // 2:]))
                xparts = ", ".join(map(lambda xpart: f"WORD_CONSTANT_TYPE({xpart})", xparts))
                yparts = ", ".join(map(lambda ypart: f"WORD_CONSTANT_TYPE({ypart})", yparts))
                s += f"{{{{{{{xparts}}}}}, {{{{{yparts}}}}}}}"
                if i + simd_packed_count < matrix.nrows():
                    s += ", "
            s += "}"
            if k + 1 < len(matrices):
                s += ","
            s += "\n"
        s += "};\n"
        return s

    def _matrix_vector_product(self, simd_packed_count):
        s = (
            "void matrix_vector_product(simd_union matrix[BLOCK_SIZE / SIMD_PACKED_COUNT][2], WORD_TYPE xy[2], WORD_TYPE res[2]) {\n"
            "    SIMD_TYPE xy0 = SIMD_SET1(xy[0]);\n"
            "    SIMD_TYPE xy1 = SIMD_SET1(xy[1]);\n"
            # We do a reverse loop here for performance reasons.
            "    for (size_t i = WORD_SIZE / SIMD_PACKED_COUNT; i-- > 0;) {\n"
        )

        s += "        simd_union inter0 = {.simd = SIMD_XOR(SIMD_AND(matrix[i][0].simd, xy0), SIMD_AND(matrix[i][1].simd, xy1))};\n"
        for i in reversed(range(simd_packed_count)):
            s += f"        res[0] = (res[0] << 1) | ((WORD_TYPE) WORD_PARITY_FUNCTION(inter0.words[{i}]));\n"

        s += "        simd_union inter1 = {.simd = SIMD_XOR(SIMD_AND(matrix[(WORD_SIZE / SIMD_PACKED_COUNT) + i][0].simd, xy0), SIMD_AND(matrix[(WORD_SIZE / SIMD_PACKED_COUNT) + i][1].simd, xy1))};\n"
        for i in reversed(range(simd_packed_count)):
            s += f"        res[1] = (res[1] << 1) | ((WORD_TYPE) WORD_PARITY_FUNCTION(inter1.words[{i}]));\n"

        s += "    }\n"
        s += "}\n"
        s += "\n"
        return s

    def _functions(self, block_size, word_size, rounds):
        simd_packed_count = self._SIMD_SIZE // word_size
        return self._matrix_vector_product(simd_packed_count) + \
               "\n" + \
               self._VECTOR_ADDITION + \
               "\n" + \
               self._MODULAR_ADDITION + \
               "\n" + \
               self._ENCRYPT
