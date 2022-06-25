## Introduction 
This repository contains the code for the paper "A White-Box Speck Implementation using Self-Equivalence Encodings", [published at ACNS 2022](https://doi.org/10.1007/978-3-031-09234-3_38), with a full version [available on IACR ePrint](https://eprint.iacr.org/2022/444). The main code can roughly be divided in five parts:
* `white_box_speck/code_generator/`: this directory contains all code related to output code generation, including the different code generation strategies.
* `white_box_speck/self_equivalences/`: this directory contains all code related to the generation of (random) linear and affine self-equivalences, as well as combining these self-equivalences.
* `white_box_speck/__init__.py`: this file contains the `WhiteBoxSpeck` class, responsible for generating the encoded matrices and vectors when a Speck key is provided.
* `white_box_speck/__main__.py`: the main Python file, containing miscellaneous code related to argument handling, logging, and directing the other components.
* `white_box_speck/external_encodings.py`: this file contains code generate random linear and affine external encodings, and the code required to output these encodings.

Additionally, this repository also contains proof-of-concept implementations of attacks to recover self-equivalence encodings and external encodings from a white-box Speck implementation. These attacks can be found in the `attacks` directory.

## Requirements
This project uses Python 3 and the [SageMath](https://www.sagemath.org/) package.

## Usage
The `test.sh` file included in this repository is a simple Bash script which tests the program using the Speck test vectors. Reading through this file is a good first introduction to the project.

To generate white-box Speck encryption implementations manually, you will need to execute the `main.py` file:
```
$ sage -python -m white_box_speck -h
```
This will output the help dialogue with possible arguments, copied here for your convenience:
```
usage: sage -python -m white_box_speck [-h] [--block-size {32,48,64,96,128}] [--key-size {64,72,96,128,144,192,256}] [--output-dir OUTPUT_DIR] [--self-equivalences {affine,linear}] [--debug] key [key ...]

Generate a white-box Speck implementation using self-equivalence encodings

positional arguments:
  key                   the key to use for the Speck implementation, a hexadecimal representation of the words

options:
  -h, --help            show this help message and exit
  --block-size {32,48,64,96,128}
                        the block size in bits of the Speck implementation (default: 128)
  --key-size {64,72,96,128,144,192,256}
                        the key size in bits of the Speck implementation (default: 256)
  --output-dir OUTPUT_DIR
                        the directory to output the C files to (default: .)
  --self-equivalences {affine,linear}
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
$ gcc -o inverse_input_external_encoding inverse_input_external_encoding.c
$ gcc -o inverse_output_external_encoding inverse_output_external_encoding.c
$ gcc -march=native -o speck default_white_box_speck.c
$ ./inverse_output_external_encoding $(./speck $(./inverse_input_external_encoding $PLAINTEXT))
```
This will properly chain the inverse input and output external encodings with the white-box implementation to present the expected ciphertext.

## Performance
In general, the bit-packed code generation strategy is the most efficient overall strategy. However, this depends on block size and your performance goals. For a comprehensive overview, refer to Implementation section of https://eprint.iacr.org/2022/444.

The performance of a specific strategy can be tested by providing an iterations argument to a `speck` executable. The following example will perform Speck encryption 1000000 times:
```
$ gcc -march=native -o speck default_white_box_speck.c
$ perf stat --detailed ./speck 1000000
```

Additionally, we include a convenient script to test the performance of all strategies and compare them to a reference implementation:
```
$ ./test_performance.sh 32 64 '1918 1110 0908 0100' 1000000
```
Note: this script only works for Speck implementations with block size 32, 64, and 128.

## Some examples

Generating a white-box `Speck32/64` implementation using only linear self-equivalences (just for demonstration purposes, linear self-equivalences are very insecure):
```
$ sage -python -m white_box_speck --block-size 32 --key-size 64 --self-equivalences linear 1918 1110 0908 0100
```

Generating a white-box `Speck64/128` implementation with debug logging enabled:
```
$ sage -python -m white_box_speck --block-size 64 --key-size 128 --debug 1b1a1918 13121110 0b0a0908 03020100
```

Generating a white-box `Speck128/256` implementation in the `out` directory:

```
$ sage -python -m white_box_speck --block-size 128 --key-size 256 --output-dir out 1f1e1d1c1b1a1918 1716151413121110 0f0e0d0c0b0a0908 0706050403020100
```

## Attacks

As mentioned, the `attacks` directory contains proof-of-concept implementations of attacks to recover self-equivalence encodings and external encodings from a white-box Speck implementation. The attacks can be tested by running the Python scripts:
```
$ sage -python attacks/linear.py
```
or
```
$ sage -python attacks/anf.py
```

This will output the results of the attack (i.e. whether the master key and external encodings could be recovered), for each Speck parameter set.
