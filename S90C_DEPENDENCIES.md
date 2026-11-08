# Dependency review — 2026-11-08

The manifest now pins all nine packages in this integration's runtime dependency closure with exact == versions. These are websocket-client 1.9.2, wakeonlan 3.3.0, aiofiles 25.1.0, casttube 0.2.1, requests 2.34.2, charset-normalizer 3.4.3, idna 3.20, urllib3 2.8.0 and certifi 2026.10.23.

Target checked: Home Assistant Core 2026.10.2, CPython 3.14, Linux musl ARM64. This is the previously reported HA version, not a live measurement of the installed system. Official HA constraints require Requests 2.34.2 and charset-normalizer 3.4.3 and allow aiofiles >=24.1.0. HA's integration requirements use wakeonlan 3.3.0; this was chosen over the current major version 4.0.0 to retain the expected API. Wheel source inspection confirmed send_magic_packet remains available.

Sources:
- https://github.com/home-assistant/core/blob/2026.10.2/homeassistant/package_constraints.txt
- https://github.com/home-assistant/core/blob/2026.10.2/requirements_all.txt
- https://github.com/home-assistant/core/blob/2026.10.2/pyproject.toml
- Package metadata and artifact SHA256 digests from https://pypi.org/pypi/NAME/VERSION/json
- OSV version queries: https://api.osv.dev/v1/querybatch (recorded in S90C_DEPENDENCY_AUDIT.json).

## Security result and removed dependency

OSV returned no known vulnerability matches for the nine pinned versions on the review date. This is a database result, not a malware or safety certification; it does not cover every package in Home Assistant.

Removed pillow-heif from the installation manifest because it is only used by the disabled Frame image-conversion path and is imported lazily there. This also avoids adding Pillow through that dependency. HA 2026.10.2 itself constrains Pillow to 12.3.0. OSV reports vulnerabilities for that version, including GHSA-22hg-r758-rrw9 (MIC/TIFF infinite loop, fixed in 13.0.0):
https://github.com/python-pillow/Pillow/security/advisories/GHSA-22hg-r758-rrw9

Do not override HA's shared Pillow version from this integration. Removing pillow-heif does not remove or repair Pillow already installed by HA or other integrations. Verify the current HA environment and an official compatible update before installation; do not claim the complete HA environment is vulnerability-free.

## Reproducibility and validation

requirements-s90c-arm64.lock contains the full nine-package closure and hashes for the selected ARM64/Python 3.14 wheels. A pip resolver dry-run succeeded against the official HA constraints. Downloading the full closure with --require-hashes and --only-binary=:all: also succeeded, verifying the selected files without installing or executing them. No source builds were needed.

Reproduce (download the referenced official HA constraints to ha-constraints.txt first):

```sh
python -m pip download --require-hashes --only-binary=:all: --platform musllinux_1_2_aarch64 --python-version 3.14 --implementation cp --abi cp314 --constraint ha-constraints.txt --requirement requirements-s90c-arm64.lock --dest verified-wheels
```

Home Assistant uses manifest requirements and does not enforce this separate hash lock. The manifest enforces exact package versions; the hash lock supplies independently verifiable artifact identities. Another integration or HA update can create a shared-environment conflict; revalidate when HA or these pins change. The development/test requirements files remain outside this runtime lock and must not be installed into HA OS.

No live HA startup, runtime dependency imports on ARM64, or TV writes were performed. Native-library vulnerabilities outside the queried PyPI records and the full HA dependency graph were not exhaustively audited. Pins need periodic review for security fixes; keeping old versions forever is not a security policy.
