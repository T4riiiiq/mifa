import unittest

from providers import (
    PROVIDERS,
    get_provider,
    list_providers,
)


class ProviderRegistryTests(
    unittest.TestCase
):
    def test_list_matches_registry(self):
        self.assertEqual(
            list(list_providers()),
            sorted(PROVIDERS),
        )

    def test_provider_ids_match_registry_keys(self):
        for provider_id in list_providers():
            provider = get_provider(
                provider_id
            )

            self.assertEqual(
                provider.provider_id,
                provider_id,
            )


if __name__ == "__main__":
    unittest.main()
