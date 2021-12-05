#define BLOCK_SIZE 128
#define KEY_SIZE 256
#define WORD_TYPE uint64_t
#define WORD_IN_TYPE SCNx64
#define WORD_OUT_TYPE PRIx64
#define ALPHA 8
#define BETA 3
#define ROUNDS 34
#define KEY {0x1f1e1d1c1b1a1918, 0x1716151413121110, 0x0f0e0d0c0b0a0908, 0x0706050403020100}

#include "speck.c"
