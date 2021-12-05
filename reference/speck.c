#include <inttypes.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

#define WORD_SIZE (BLOCK_SIZE / 2)
#define KEY_WORDS (KEY_SIZE / WORD_SIZE)
#define ROTATE_RIGHT(x, pos) ((x >> pos) | (x << (WORD_SIZE - pos)))
#define ROTATE_LEFT(x, pos) ((x << pos) | (x >> (WORD_SIZE - pos)))
#define ROUND(k, x, y) ( \
    x = ROTATE_RIGHT(x, ALPHA), \
    x += y, \
    x ^= k, \
    y = ROTATE_LEFT(y, BETA), \
    y ^= x \
)


void key_expansion(WORD_TYPE key[KEY_WORDS], WORD_TYPE k[ROUNDS]) {
    k[0] = key[KEY_WORDS - 1];

    WORD_TYPE l[KEY_WORDS - 1 + ROUNDS - 1];
    for (size_t i = 1; i < KEY_WORDS; i++) {
        l[i - 1] = key[KEY_WORDS - 1 - i];
    }

    for (size_t i = 0; i < ROUNDS - 1; i++) {
        l[KEY_WORDS - 2 + i + 1] = l[i];
        k[i + 1] = k[i];
        ROUND(i, l[KEY_WORDS - 2 + i + 1], k[i + 1]);
    }
}


void encrypt(WORD_TYPE k[ROUNDS], WORD_TYPE p[2], WORD_TYPE c[2]) {
    c[0] = p[0];
    c[1] = p[1];

    for (size_t i = 0; i < ROUNDS; i++) {
        ROUND(k[i], c[0], c[1]);
    }
}

int main(int argc, char *argv[]) {
    WORD_TYPE key[KEY_WORDS] = KEY;
    WORD_TYPE k[ROUNDS];
    key_expansion(key, k);

    if (argc < 2) {
        return -1;
    }
    WORD_TYPE p[2];
    WORD_TYPE c[2];
    if (argc < 3) {
        size_t iterations;
        sscanf(argv[1], "%zu", &iterations);
        for (int i = 0; i < iterations; i++) {
            p[0] = (((WORD_TYPE) rand()) << (WORD_SIZE / 2)) | ((WORD_TYPE) rand());
            p[1] = (((WORD_TYPE) rand()) << (WORD_SIZE / 2)) | ((WORD_TYPE) rand());
            encrypt(k, p, c);
        }
    } else {
        sscanf(argv[1], "%" WORD_IN_TYPE, &p[0]);
        sscanf(argv[2], "%" WORD_IN_TYPE, &p[1]);
        encrypt(k, p, c);
        printf("%" WORD_OUT_TYPE " %" WORD_OUT_TYPE "\n", c[0], c[1]);
    }
}
