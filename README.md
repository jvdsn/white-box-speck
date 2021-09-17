## Introduction 
This repository contains the code for my master's thesis: "A White-Box Speck Implementation using Self-Equivalence Encodings". The code can roughly be divided in six parts:
* `src/code_generator/`: this directory contains all code related to output code generation, including the different code generation strategies.
* `src/self_equivalences/`: this directory contains all code related to the generation of (random) linear and affine self-equivalences, as well as combining these self-equivalences.
* `src/white_box_speck.py`: this file contains the `WhiteBoxSpeck` class, responsible for generating the encoded matrices and vectors when a Speck key is provided.
* `src/external_encodings.py`: this file contains code generate random linear and affine external encodings, and the code required to output these encodings.
* `src/main.py`: the main Python file, containing miscellaneous code related to argument handling, logging, and directing the other components.
* `src/attacks`: this directory is special. It contains proof-of-concept implementations of attacks to recover self-equivalence encodings and external encodings from a white-box Speck implementation.

## Requirements
This project uses Python 3 and the [SageMath](https://www.sagemath.org/) package.

## Usage
The `test.sh` file included in this repository is a simple Bash script which tests the program using the Speck test vectors. Reading through this file is a good first introduction to the project.

To generate white-box Speck encryption implementations manually, you will need to execute the `main.py` file:
```
sage -python src/main.py -h
```
This will output the help dialogue with possible arguments, copied here for your convenience:
```
usage: main.py [-h] [--block-size [{32,48,64,96,128}]] [--key-size [{64,72,96,128,144,192,256}]] [--output-dir [OUTPUT_DIR]] [--self-equivalences [{affine,linear}]] [--debug] key [key ...]

Generate a white-box Speck implementation using self-equivalence encodings

positional arguments:
  key                   the key to use for the Speck implementation, a hexadecimal representation of the words

optional arguments:
  -h, --help            show this help message and exit
  --block-size [{32,48,64,96,128}]
                        the block size in bits of the Speck implementation (default: 128)
  --key-size [{64,72,96,128,144,192,256}]
                        the key size in bits of the Speck implementation (default: 256)
  --output-dir [OUTPUT_DIR]
                        the directory to output the C files to (default: .)
  --self-equivalences [{affine,linear}]
                        the type of self-equivalences to use (default: affine)
  --debug               log debug messages
```

After executing the program with your arguments, 8 files will be generated in the output directory:
* `inverse_input_external_encoding.c`: computes the inverse of the input external encoding.
* `inverse_output_external_encoding.c`: computes the inverse of the output external encoding.
* `default_white_box_speck.c`: a white-box Speck implementation using the default code generation strategy.
* `sparse_matrix_white_box_speck.c`: a white-box Speck implementation using the sparse matrix code generation strategy.
* `inlined_white_box_speck.c`: a white-box Speck implementation using the inlined code generation strategy.
* `bit_packed_white_box_speck.c`: a white-box Speck implementation using the bit-packed code generation strategy.
* `inlined_bit_packed_white_box_speck.c`: a white-box Speck implementation using the inlined bit-packed code generation strategy.
* `simd_white_box_speck.c`: a white-box Speck implementation using the SIMD code generation strategy.

All of these programs accept two input words *as arguments* and output the result to standard output. Consequently, you can do something like this:
```
gcc -o inverse_input_external_encoding inverse_input_external_encoding.c
gcc -o inverse_output_external_encoding inverse_output_external_encoding.c
gcc -march=native -o speck default_white_box_speck.c
./inverse_output_external_encoding $(./speck $(./inverse_input_external_encoding $PLAINTEXT))
```
This will properly chain the inverse input and output external encodings with the white-box implementation to present the expected ciphertext.

## Performance
In general, the bit-packed code generation strategy is the most efficient overall strategy. However, this depends on block size and your performance goals. For a comprehensive overview, refer to Implementation chapter of my master's thesis.

## Some examples

Generating a white-box `Speck32/64` implementation using only linear self-equivalences (just for demonstration purposes, linear self-equivalences are very insecure):
```
sage -python src/main.py --block-size 32 --key-size 64 --self-equivalences linear 1918 1110 0908 0100
```

Generating a white-box `Speck64/128` implementation with debug logging enabled:
```
sage -python src/main.py --block-size 64 --key-size 128 --debug 1b1a1918 13121110 0b0a0908 03020100
```

Generating a white-box `Speck128/256` implementation in the `out` directory:

```
sage -python src/main.py --block-size 128 --key-size 256 --output-dir out 1f1e1d1c1b1a1918 1716151413121110 0f0e0d0c0b0a0908 0706050403020100
```

## Attacks

As mentioned, `src/attacks` contains proof-of-concept implementations of attacks to recover self-equivalence encodings and external encodings from a white-box Speck implementation. The attacks can be tested using the `test_attacks.sh` script. This script will output the results of the attack (i.e. whether the master key and external encodings could be recovered), for each Speck parameter set.
