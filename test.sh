#!/bin/bash

BLOCK_SIZES=(32 48 48 64 64 96 96 128 128 128)
KEY_SIZES=(64 72 96 96 128 96 144 128 192 256)
# From Speck test vectors.
KEYS=(
"1918 1110 0908 0100"
"121110 0a0908 020100"
"1a1918 121110 0a0908 020100"
"13121110 0b0a0908 03020100"
"1b1a1918 13121110 0b0a0908 03020100"
"0d0c0b0a0908 050403020100"
"151413121110 0d0c0b0a0908 050403020100"
"0f0e0d0c0b0a0908 0706050403020100"
"1716151413121110 0f0e0d0c0b0a0908 0706050403020100"
"1f1e1d1c1b1a1918 1716151413121110 0f0e0d0c0b0a0908 0706050403020100"
)
PLAINTEXTS=(
"6574 694c"
"20796c 6c6172"
"6d2073 696874"
"74614620 736e6165"
"3b726574 7475432d"
"65776f68202c 656761737520"
"656d6974206e 69202c726576"
"6c61766975716520 7469206564616d20"
"7261482066656968 43206f7420746e65"
"65736f6874206e49 202e72656e6f6f70"
)
CIPHERTEXTS=(
"a868 42f2"
"c049a5 385adc"
"735e10 b6445d"
"9f7952ec 4175946c"
"8c6fa548 454e028b"
"9e4d09ab7178 62bdde8f79aa"
"2bf31072228a 7ae440252ee6"
"a65d985179783265 7860fedf5c570d18"
"1be4cf3a13135566 f9bc185de03c1886"
"4109010405c0f53e 4eeeb48d9c188f43"
)

STRATEGIES=(
"default_white_box_speck.c"
"sparse_matrix_white_box_speck.c"
"inlined_white_box_speck.c"
"bit_packed_white_box_speck.c"
"inlined_bit_packed_white_box_speck.c"
"simd_white_box_speck.c"
)

for ((i = 0; i < ${#BLOCK_SIZES[@]}; i++)); do
    echo "Testing Speck${BLOCK_SIZES[i]}/${KEY_SIZES[i]} with key '${KEYS[i]}'"
    sage -python src/main.py --block-size ${BLOCK_SIZES[i]} --key-size ${KEY_SIZES[i]} --debug ${KEYS[i]}

    gcc -o inverse_input_external_encoding inverse_input_external_encoding.c
    gcc -o inverse_output_external_encoding inverse_output_external_encoding.c

    for strategy in "${STRATEGIES[@]}"; do
        if [ -f $strategy ]; then
            gcc -march=native -o speck $strategy
            ciphertext=$(./inverse_output_external_encoding $(./speck $(./inverse_input_external_encoding ${PLAINTEXTS[i]})))
            echo "Expected '${CIPHERTEXTS[i]}', got '$ciphertext'"
            rm speck
            rm $strategy
        fi
    done

    rm inverse_input_external_encoding
    rm inverse_output_external_encoding
    rm inverse_input_external_encoding.c
    rm inverse_output_external_encoding.c
done
