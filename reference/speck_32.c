#define BLOCK_SIZE 32
#define KEY_SIZE 64
#define WORD_TYPE uint16_t
#define WORD_IN_TYPE SCNx16
#define WORD_OUT_TYPE PRIx16
#define ALPHA 7
#define BETA 2
#define ROUNDS 22
#define KEY {0x1918, 0x1110, 0x0908, 0x0100}

#include "speck.c"
