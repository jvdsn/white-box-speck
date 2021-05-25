#!/bin/sh

python src/main.py --block-size 128 --key-size 256 1f1e1d1c1b1a1918 1716151413121110 0f0e0d0c0b0a0908 0706050403020100 
gcc -o inverse_input_external_encoding inverse_input_external_encoding.c
gcc -o inverse_output_external_encoding inverse_output_external_encoding.c

gcc -o speck default_white_box_speck.c
./inverse_output_external_encoding $(./speck $(./inverse_input_external_encoding 65736f6874206e49 202e72656e6f6f70))
rm speck

gcc -o speck sparse_matrix_white_box_speck.c
./inverse_output_external_encoding $(./speck $(./inverse_input_external_encoding 65736f6874206e49 202e72656e6f6f70))
rm speck

gcc -o speck inlined_white_box_speck.c
./inverse_output_external_encoding $(./speck $(./inverse_input_external_encoding 65736f6874206e49 202e72656e6f6f70))
rm speck

gcc -o speck bit_packed_white_box_speck.c
./inverse_output_external_encoding $(./speck $(./inverse_input_external_encoding 65736f6874206e49 202e72656e6f6f70))
rm speck

gcc -o speck inlined_bit_packed_white_box_speck.c
./inverse_output_external_encoding $(./speck $(./inverse_input_external_encoding 65736f6874206e49 202e72656e6f6f70))
rm speck

gcc -o speck -march=native simd_white_box_speck.c
./inverse_output_external_encoding $(./speck $(./inverse_input_external_encoding 65736f6874206e49 202e72656e6f6f70))
rm speck

rm inverse_input_external_encoding
rm inverse_output_external_encoding

rm inverse_input_external_encoding.c
rm inverse_output_external_encoding.c
rm default_white_box_speck.c
rm sparse_matrix_white_box_speck.c
rm inlined_white_box_speck.c
rm bit_packed_white_box_speck.c
rm inlined_bit_packed_white_box_speck.c
rm simd_white_box_speck.c
