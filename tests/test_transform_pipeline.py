import unittest

from core.transforms import TransformPipeline


class TransformPipelineTests(
    unittest.TestCase
):
    def setUp(self):
        self.engine = (
            TransformPipeline()
        )

        self.data = (
            b"Mifa payload pipeline "
            b"round-trip verification."
        )

    def verify_pipeline(
        self,
        **options
    ):
        output, metadata = (
            self.engine.apply(
                self.data,
                **options
            )
        )

        restored = (
            self.engine.reverse(
                output,
                metadata,
            )
        )

        self.assertEqual(
            restored,
            self.data,
        )

        self.assertTrue(
            metadata[
                "roundtrip_match"
            ]
        )

    def test_none(self):
        self.verify_pipeline()

    def test_xor(self):
        self.verify_pipeline(
            transform="xor"
        )

    def test_aes_256_cbc(self):
        self.verify_pipeline(
            transform="aes-256-cbc"
        )

    def test_aes_256_gcm(self):
        self.verify_pipeline(
            transform="aes-256-gcm"
        )

    def test_combined_pipeline(self):
        self.verify_pipeline(
            transform="aes-256-gcm",
            encoding="base64",
            compression="gzip",
        )


if __name__ == "__main__":
    unittest.main()
