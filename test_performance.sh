#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "Usage: ./test_performance.sh BLOCK_SIZE KEY_SIZE KEY TEST_ITERATIONS"
    exit 1
fi

BLOCK_SIZE=$1
KEY_SIZE=$2
KEY=$3
TEST_ITERATIONS=$4
# Only use affine encodings for performance testing.
SELF_EQUIVALENCES="affine"

STRATEGIES=(
"default_white_box_speck.c"
"sparse_matrix_white_box_speck.c"
"inlined_white_box_speck.c"
"bit_packed_white_box_speck.c"
"inlined_bit_packed_white_box_speck.c"
"simd_white_box_speck.c"
)

echo "Testing Speck$BLOCK_SIZE/$KEY_SIZE reference implementation with key '$KEY'"
gcc -march=native -o speck "reference/speck_$BLOCK_SIZE.c"
du -b speck
perf stat --detailed ./speck $TEST_ITERATIONS

sage -python -m white_box_speck --block-size $BLOCK_SIZE --key-size $KEY_SIZE --self-equivalences $SELF_EQUIVALENCES $KEY
# We don't use the external encodings
rm inverse_input_external_encoding.c
rm inverse_output_external_encoding.c

for strategy in "${STRATEGIES[@]}"; do
    if [ -f $strategy ]; then
        echo "Testing Speck$BLOCK_SIZE/$KEY_SIZE $strategy with key '$KEY'"
        gcc -march=native -o speck $strategy
        du -b speck
        perf stat --detailed ./speck $TEST_ITERATIONS
        rm speck
        rm $strategy
    fi
done
