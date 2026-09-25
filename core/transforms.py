import base64
import binascii
import gzip
import hashlib
import os
import zlib

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class TransformPipeline:
    TRANSFORMS = {
        "none",
        "xor",
        "aes-256-cbc",
        "aes-256-gcm",
    }

    ENCODINGS = {
        "none",
        "base64",
        "hex",
    }

    COMPRESSIONS = {
        "none",
        "gzip",
        "deflate",
    }

    def _sha256(self, data):
        return hashlib.sha256(
            data
        ).hexdigest()

    def _decode_hex_key(
        self,
        value,
        required_size=None
    ):
        try:
            key = bytes.fromhex(
                value
            )

        except ValueError as exc:
            raise ValueError(
                "Key must be valid hexadecimal"
            ) from exc

        if not key:
            raise ValueError(
                "Key cannot be empty"
            )

        if (
            required_size is not None
            and len(key) != required_size
        ):
            raise ValueError(
                f"Key must be exactly "
                f"{required_size} bytes"
            )

        return key

    def _compress(
        self,
        data,
        method
    ):
        if method == "none":
            return data

        if method == "gzip":
            return gzip.compress(
                data,
                mtime=0,
            )

        if method == "deflate":
            return zlib.compress(
                data
            )

        raise ValueError(
            f"Unsupported compression: {method}"
        )

    def _decompress(
        self,
        data,
        method
    ):
        if method == "none":
            return data

        if method == "gzip":
            return gzip.decompress(
                data
            )

        if method == "deflate":
            return zlib.decompress(
                data
            )

        raise ValueError(
            f"Unsupported compression: {method}"
        )

    def _encode(
        self,
        data,
        method
    ):
        if method == "none":
            return data

        if method == "base64":
            return base64.b64encode(
                data
            )

        if method == "hex":
            return binascii.hexlify(
                data
            )

        raise ValueError(
            f"Unsupported encoding: {method}"
        )

    def _decode(
        self,
        data,
        method
    ):
        if method == "none":
            return data

        if method == "base64":
            return base64.b64decode(
                data,
                validate=True,
            )

        if method == "hex":
            return binascii.unhexlify(
                data
            )

        raise ValueError(
            f"Unsupported encoding: {method}"
        )

    def _transform(
        self,
        data,
        method,
        key_hex=None
    ):
        if method == "none":
            return data, {}

        if method == "xor":
            if key_hex:
                key = self._decode_hex_key(
                    key_hex
                )
            else:
                key = os.urandom(
                    16
                )

            output = bytes(
                value
                ^ key[
                    index % len(key)
                ]
                for index, value
                in enumerate(data)
            )

            return output, {
                "key_hex":
                    key.hex(),
            }

        if method == "aes-256-cbc":
            if key_hex:
                key = self._decode_hex_key(
                    key_hex,
                    required_size=32,
                )
            else:
                key = os.urandom(
                    32
                )

            iv = os.urandom(
                16
            )

            padder = padding.PKCS7(
                128
            ).padder()

            padded = (
                padder.update(
                    data
                )
                + padder.finalize()
            )

            cipher = Cipher(
                algorithms.AES(
                    key
                ),
                modes.CBC(
                    iv
                ),
            )

            encryptor = cipher.encryptor()

            output = (
                encryptor.update(
                    padded
                )
                + encryptor.finalize()
            )

            return output, {
                "key_hex":
                    key.hex(),

                "iv_hex":
                    iv.hex(),
            }

        if method == "aes-256-gcm":
            if key_hex:
                key = self._decode_hex_key(
                    key_hex,
                    required_size=32,
                )
            else:
                key = os.urandom(
                    32
                )

            nonce = os.urandom(
                12
            )

            output = AESGCM(
                key
            ).encrypt(
                nonce,
                data,
                None,
            )

            return output, {
                "key_hex":
                    key.hex(),

                "nonce_hex":
                    nonce.hex(),
            }

        raise ValueError(
            f"Unsupported transform: {method}"
        )

    def _reverse_transform(
        self,
        data,
        method,
        metadata
    ):
        if method == "none":
            return data

        if method == "xor":
            key = bytes.fromhex(
                metadata[
                    "key_hex"
                ]
            )

            return bytes(
                value
                ^ key[
                    index % len(key)
                ]
                for index, value
                in enumerate(data)
            )

        if method == "aes-256-cbc":
            key = bytes.fromhex(
                metadata[
                    "key_hex"
                ]
            )

            iv = bytes.fromhex(
                metadata[
                    "iv_hex"
                ]
            )

            cipher = Cipher(
                algorithms.AES(
                    key
                ),
                modes.CBC(
                    iv
                ),
            )

            decryptor = cipher.decryptor()

            padded = (
                decryptor.update(
                    data
                )
                + decryptor.finalize()
            )

            unpadder = padding.PKCS7(
                128
            ).unpadder()

            return (
                unpadder.update(
                    padded
                )
                + unpadder.finalize()
            )

        if method == "aes-256-gcm":
            key = bytes.fromhex(
                metadata[
                    "key_hex"
                ]
            )

            nonce = bytes.fromhex(
                metadata[
                    "nonce_hex"
                ]
            )

            return AESGCM(
                key
            ).decrypt(
                nonce,
                data,
                None,
            )

        raise ValueError(
            f"Unsupported transform: {method}"
        )

    def reverse(
        self,
        data,
        metadata
    ):
        decoded = self._decode(
            data,
            metadata[
                "encoding"
            ],
        )

        transformed = (
            self._reverse_transform(
                decoded,
                metadata[
                    "transform"
                ],
                metadata,
            )
        )

        return self._decompress(
            transformed,
            metadata[
                "compression"
            ],
        )

    def apply(
        self,
        data,
        transform="none",
        encoding="none",
        compression="none",
        key_hex=None
    ):
        transform = (
            transform or "none"
        )

        encoding = (
            encoding or "none"
        )

        compression = (
            compression or "none"
        )

        if transform not in self.TRANSFORMS:
            raise ValueError(
                f"Unsupported transform: {transform}"
            )

        if encoding not in self.ENCODINGS:
            raise ValueError(
                f"Unsupported encoding: {encoding}"
            )

        if compression not in self.COMPRESSIONS:
            raise ValueError(
                f"Unsupported compression: "
                f"{compression}"
            )

        input_sha256 = self._sha256(
            data
        )

        compressed = self._compress(
            data,
            compression,
        )

        transformed, secret_data = (
            self._transform(
                compressed,
                transform,
                key_hex=key_hex,
            )
        )

        output = self._encode(
            transformed,
            encoding,
        )

        metadata = {
            "transform":
                transform,

            "encoding":
                encoding,

            "compression":
                compression,

            "processing_order": [
                "compression",
                "transform",
                "encoding",
            ],

            "input_size":
                len(data),

            "output_size":
                len(output),

            "input_sha256":
                input_sha256,

            "output_sha256":
                self._sha256(
                    output
                ),
        }

        metadata.update(
            secret_data
        )

        restored = self.reverse(
            output,
            metadata,
        )

        metadata[
            "roundtrip_sha256"
        ] = self._sha256(
            restored
        )

        metadata[
            "roundtrip_match"
        ] = (
            restored == data
        )

        if not metadata[
            "roundtrip_match"
        ]:
            raise RuntimeError(
                "Payload round-trip verification failed"
            )

        return output, metadata
