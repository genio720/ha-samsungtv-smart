# S90C fork: changes awaiting Home Assistant validation

Base: TheFab21/ha-samsungtv-smart at `d1b16c7d6e882704651f2bd1275c7875ec543203` (manifest 9.2.0).

This branch is a review candidate, not a security certification or an installation release.

## Changes

- `fork_policy.py` disables Frame features at build level. Startup does not register artwork HTTP endpoints or bundled gallery/upload frontend resources. Cached Frame flags cannot enable the corresponding entities. The Art API refuses support, opening and requests; artwork identification refuses work before accessing HA or cloud services.
- Artwork thumbnail filenames are allowlisted and resolved paths checked for containment, including pre-existing symlink escapes. This does not defend against a local attacker able to change filesystem links concurrently.
- Gallery text, image metadata and editor fields, plus upload-card names and title, are escaped before insertion in HTML. Gallery CSS configuration is constrained to supported numeric/length/ratio values.
- MobileBFF protocol implementation and the Game Mode selection behavior are unchanged. The existing upstream remote/control and optional SmartThings functionality remain; this is not a complete local-only rewrite.

## Validation

Run from the repository root:

```sh
python tests/test_s90c_hardening_standalone.py
node tests/test_s90c_cards.cjs
node --check custom_components/samsungtv_smart/www/folder-gallery-card.js
node --check custom_components/samsungtv_smart/www/samsung-art-upload-card.js
git diff --check
```

Locally: four Python tests passed, one symlink test skipped due to Windows permissions; JS rendering/escape/CSS assertions passed; all 38 component Python files parsed and both JS files passed syntax checks. The Python gate tests execute the real function bodies independently and verify they return before runtime/network access. The JS tests use minimal DOM stand-ins, not a complete browser.

Not run: full upstream HA test suite, actual HA startup, Linux/ARM64 install, or TV writes. Existing upstream Art tests assume Art is enabled; they need an explicit enabled-policy test fixture before being used to validate the retained Art implementation. Do not interpret this branch as passing that suite.

## Before installation

1. Confirm current HA/Python/OS versions and a recoverable backup.
2. Nine runtime dependencies are pinned in the manifest and resolved against HA 2026.10.2 constraints; see S90C_DEPENDENCIES.md. Confirm the actual installed HA version before installation. Do not install the development requirements.txt in HA OS.
3. Keep optional SmartThings/AI credentials unset for local use and disable remote logos if unwanted.
4. Keep GitHub Actions/release automation disabled unless its permissions and mutable action references have been reviewed. This branch does not change workflow configuration or claim those findings resolved.
5. Install only an explicitly reviewed revision of this fork after HA validation. Do not automatically sync upstream.

This profile is intended for a fresh installation on a non-Frame TV. It does not remove old dashboard resources already registered by a previous installation, remove every Art option/service definition, or migrate existing Frame dashboards. A HA restart is required to unload previously registered views. Do not re-enable Frame features without reviewing remaining Art and frontend paths.

No HA configuration, existing automations, network settings or TV settings were changed while preparing this branch. Game Mode reads were verified separately; changing its value remains untested and requires authorization.
