from django.conf import settings
from django.core.management.base import BaseCommand
import json
import os
import requests


class Command(BaseCommand):
    help = "Download and write all the official identity providers metadata XML files"

    def handle(self, *args, **options):
        self.write_identity_providers_metadata()

    def write_identity_providers_metadata(self):
        identity_providers = self.download_identity_providers()

        self.print(
            f"Starting writing of IdPs metadata XML files "
            f"into {settings.SPID_IDENTITY_PROVIDERS_METADATA_DIR}:"
        )

        for identity_provider in identity_providers:
            idp_entity_code = identity_provider["ipa_entity_code"]
            idp_entity_name = identity_provider["entity_name"]
            idp_metadata = identity_provider["metadata"]
            metadata_file_path = os.path.join(
                settings.SPID_IDENTITY_PROVIDERS_METADATA_DIR, f"{idp_entity_code}.xml"
            )

            self.print(
                f"Writing metadata XML file for IdP {idp_entity_name} "
                f"into {metadata_file_path}",
                indentation_level=1,
            )

            with open(metadata_file_path, "w", encoding="utf8") as metadata_file:
                metadata_file.write(idp_metadata)

        self.print_success(
            f"Successfully wrote all IdPs metadata XML files "
            f"into {settings.SPID_IDENTITY_PROVIDERS_METADATA_DIR}"
        )

    def download_identity_providers(self):
        self.print(
            f"Starting download of identity providers (IdPs) "
            f"official list from {settings.SPID_IDENTITY_PROVIDERS_URL}"
        )

        with requests.get(
            settings.SPID_IDENTITY_PROVIDERS_URL, verify=True
        ) as response:
            identity_providers = json.loads(response.content)["data"]

        self.print("Downloaded IdPs official list, starting IdPs metadata download:")

        for identity_provider in identity_providers:
            idp_entity_name = identity_provider["entity_name"]
            idp_metadata_url = identity_provider["metadata_url"]

            self.print(
                f"Downloading metadata for IdP {idp_entity_name} "
                f"from {idp_metadata_url}",
                indentation_level=1,
            )

            with requests.get(idp_metadata_url, verify=True) as response:
                identity_provider["metadata"] = response.text

        self.print_success("All IdPs metadata downloaded successfully")

        return identity_providers

    def print(self, string, *, indentation_level=0):
        indentation = "  " * indentation_level
        self.stdout.write(indentation + string)

    def print_success(self, string, *, indentation_level=0):
        self.print(self.style.SUCCESS(string), indentation_level=indentation_level)
