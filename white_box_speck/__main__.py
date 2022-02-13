import logging
from argparse import ArgumentParser
from pathlib import Path

from . import WhiteBoxSpeck
from .code_generator.bit_packed import BitPackedCodeGenerator
from .code_generator.default import DefaultCodeGenerator
from .code_generator.inlined import InlinedCodeGenerator
from .code_generator.inlined_bit_packed import InlinedBitPackedCodeGenerator
from .code_generator.simd import SIMDCodeGenerator
from .code_generator.sparse_matrix import SparseMatrixCodeGenerator
from .external_encodings import InputExternalEncodingCodeGenerator
from .external_encodings import OutputExternalEncodingCodeGenerator
from .external_encodings import random_affine_external_encoding
from .external_encodings import random_linear_external_encoding
from .self_equivalences.anf import AffineSelfEquivalenceProvider
from .self_equivalences.anf import LinearSelfEquivalenceProvider

parser = ArgumentParser(prog="sage -python -m white_box_speck", description="Generate a white-box Speck implementation using self-equivalence encodings")
parser.add_argument("key", nargs="+", help="the key to use for the Speck implementation, a hexadecimal representation of the words")
parser.add_argument("--block-size", type=int, default=128, choices=[32, 48, 64, 96, 128], help="the block size in bits of the Speck implementation (default: %(default)i)")
parser.add_argument("--key-size", type=int, default=256, choices=[64, 72, 96, 128, 144, 192, 256], help="the key size in bits of the Speck implementation (default: %(default)i)")
parser.add_argument("--output-dir", default=".", help="the directory to output the C files to (default: %(default)s)")
parser.add_argument("--self-equivalences", default="affine", choices=["affine", "linear"], help="the type of self-equivalences to use (default: %(default)s)")
parser.add_argument("--debug", action="store_true", help="log debug messages")

args = parser.parse_args()

if args.debug:
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s %(message)s', datefmt='%Y-%m-%d,%H:%M:%S', level=logging.DEBUG)

word_size = args.block_size // 2

white_box_speck = WhiteBoxSpeck(args.block_size, args.key_size, list(map(lambda k: int(k, 16), args.key)))

logging.debug(f"Generating random external encodings...")
if args.self_equivalences == "affine":
    self_equivalence_provider = AffineSelfEquivalenceProvider(word_size)
    input_external_encoding = random_affine_external_encoding(word_size)
    output_external_encoding = random_affine_external_encoding(word_size)
else:
    self_equivalence_provider = LinearSelfEquivalenceProvider(word_size)
    input_external_encoding = random_linear_external_encoding(word_size)
    output_external_encoding = random_linear_external_encoding(word_size)

logging.debug(f"Generating matrices and vectors using {args.self_equivalences} self-equivalences...")
matrices, vectors = white_box_speck.affine_layers(input_external_encoding, output_external_encoding, self_equivalence_provider)

if args.output_dir:
    # Make sure the output directory exists.
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

logging.debug("Generating default code...")
with open(args.output_dir + "/default_white_box_speck.c", "w") as f:
    f.write(DefaultCodeGenerator().generate_code(matrices, vectors))

logging.debug("Generating sparse matrix code...")
with open(args.output_dir + "/sparse_matrix_white_box_speck.c", "w") as f:
    f.write(SparseMatrixCodeGenerator().generate_code(matrices, vectors))

logging.debug("Generating inlined code...")
with open(args.output_dir + "/inlined_white_box_speck.c", "w") as f:
    f.write(InlinedCodeGenerator().generate_code(matrices, vectors))

logging.debug("Generating bit-packed code...")
with open(args.output_dir + "/bit_packed_white_box_speck.c", "w") as f:
    f.write(BitPackedCodeGenerator().generate_code(matrices, vectors))

logging.debug("Generating inlined bit-packed code...")
with open(args.output_dir + "/inlined_bit_packed_white_box_speck.c", "w") as f:
    f.write(InlinedBitPackedCodeGenerator().generate_code(matrices, vectors))

# SIMD code does not accept n = 24 or n = 48
if word_size != 24 and word_size != 48:
    logging.debug("Generating SIMD code...")
    with open(args.output_dir + "/simd_white_box_speck.c", "w") as f:
        f.write(SIMDCodeGenerator().generate_code(matrices, vectors))

logging.debug("Generating external encodings code...")
with open(args.output_dir + "/inverse_input_external_encoding.c", "w") as f:
    f.write(InputExternalEncodingCodeGenerator().generate_code_inverse_input_external_encoding(matrices[0], vectors[0], input_external_encoding))

with open(args.output_dir + "/inverse_output_external_encoding.c", "w") as f:
    f.write(OutputExternalEncodingCodeGenerator().generate_code_inverse_output_external_encoding(output_external_encoding))

logging.debug("Done!")
