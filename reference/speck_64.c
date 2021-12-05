#define BLOCK_SIZE 64
#define KEY_SIZE 128
#define WORD_TYPE uint32_t
#define WORD_IN_TYPE SCNx32
#define WORD_OUT_TYPE PRIx32
#define ALPHA 8
#define BETA 3
#define ROUNDS 27
#define KEY {0x1b1a1918, 0x13121110, 0x0b0a0908, 0x03020100}

#include "speck.c"
