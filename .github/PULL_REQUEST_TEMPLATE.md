<!--
  Thanks for contributing to Strato DynDNS!
  Please, DO NOT DELETE ANY TEXT from this template (unless instructed).
-->

## Breaking change

<!--
  If your PR contains a breaking change for existing users, tell them what breaks,
  how to make it work again and why it was done this way. This text is published
  with the release notes, so write it towards users, not maintainers.
  Note: Remove this section if this PR is NOT a breaking change.
-->

## Proposed change

<!--
  Describe the big picture of your changes here. If it fixes a bug or resolves a
  feature request, link that issue in the additional information section below.
-->

## Type of change

<!-- Check only 1 box. If multiple apply, consider splitting the PR. -->

- [ ] Dependency upgrade
- [ ] Bugfix (non-breaking change which fixes an issue)
- [ ] New feature (adds functionality to the integration)
- [ ] Deprecation (breaking change to happen in the future)
- [ ] Breaking change (fix/feature causing existing functionality to break)
- [ ] Code quality improvements or addition of tests
- [ ] Documentation only

## Additional information

- This PR fixes or closes issue: fixes #
- This PR is related to issue:

## Checklist

<!-- Put an `x` in the boxes that apply. -->

- [ ] I understand the code I am submitting and can explain how it works.
- [ ] The change was tested against a real Home Assistant instance and a real Strato account.
- [ ] Local tests pass (`pytest`). **Your PR cannot be merged unless tests pass.**
- [ ] Tests have been added or updated to cover the new code.
- [ ] There is no commented out or dead code in this PR.
- [ ] The GitHub Actions checks (hassfest, HACS validation, CodeQL) pass.
- [ ] No credentials, domains or IP addresses of real accounts are contained in the diff.

If user-facing behaviour or configuration options are added or changed:

- [ ] `custom_components/strato_dyndns/strings.json` and both translation files
      (`translations/en.json`, `translations/de.json`) are updated and in sync.
- [ ] `README.md` is updated.
- [ ] `CHANGELOG.md` has an entry for this change.
- [ ] The `version` field in `custom_components/strato_dyndns/manifest.json` is bumped.

If the change touches the update logic or outgoing requests:

- [ ] Strato is still only called when an update is actually necessary (no unnecessary requests).
- [ ] Error backoff per domain still works, so `abuse` blocks cannot be triggered.
- [ ] Credentials are never written to logs or diagnostics.

If dependencies changed:

- [ ] `requirements` in `manifest.json` are pinned to an exact version.
- [ ] A link to the dependency's changelog or release notes is included in this PR description.
