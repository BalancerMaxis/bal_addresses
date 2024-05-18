import json
import os.path
from .errors import MultipleMatchesError, NoResultError
from typing import Dict
from typing import Optional
import requests
from munch import Munch
from web3 import Web3

from .utils import to_checksum_address


GITHUB_CODEREVIEW_RAW = "https://raw.githubusercontent.com/balancer/code-review/main"
GITHUB_CODEREVIEW_NICE = "https://github.com/balancer/code-review/blob/main"


class RateProviders:

    source_data = requests.get(
        f"{GITHUB_CODEREVIEW_RAW}/rate-providers/registry.json"
    ).json()
    SUPPORTED_CHAINS = source_data.keys()

    def __init__(self, chain):
        self.chain = "ethereum" if chain == "mainnet" else chain
        if self.chain not in self.SUPPORTED_CHAINS:
            print(f"WARNING: Chain {self.chain} has no reviewed rate providers")
            self.info_by_rate_provider = {}
            self.rate_providers_by_token = {}
        else:
            self.info_by_rate_provider = Munch(self.source_data.get(self.chain, {}))
            self.rate_providers_by_token = Munch(
                self.translate_source_data(self.info_by_rate_provider)
            )

    def get_review_for_safe_rate_provder(self, token_address) -> Optional[str]:
        """
        Check if the token has a safe rate provider and return the link to the review.
        return None if there is no safe rate provider found.
        """
        token_info = self.rate_providers_by_token.get(
            to_checksum_address(token_address)
        )
        if token_info and token_info.is_safe:
            return token_info.review_link
        return None

    def translate_source_data(self, chain_data):
        """
        Translate the source data into a more usable format
        """
        translated_data = {}
        for provider, infodict in chain_data.items():
            token_address = to_checksum_address(infodict["asset"])
            this = translated_data[token_address] = Munch({})
            this.rate_provider = to_checksum_address(provider)
            this.name = infodict.get("name")
            this.is_safe = infodict.get("summary") == "safe"
            this.warnings = infodict.get("warnings")
            this.factory = infodict.get("factory")
            this.review_link = infodict.get("review").replace(
                "./", f"{GITHUB_CODEREVIEW_NICE}/rate-providers/"
            )
        return translated_data
