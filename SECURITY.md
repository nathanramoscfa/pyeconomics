# Security policy

## Supported versions

| Version                     | Supported                                                   |
|-----------------------------|-------------------------------------------------------------|
| Latest 1.0 pre-release      | Yes. Fixes ship in the next pre-release.                    |
| Older 1.0 pre-releases      | No. Upgrade to the latest pre-release.                      |
| 0.2.x (latest: 0.2.6)       | Security fixes only, on `legacy/0.2.x`, until 1.0.0 is released; then end of life. |
| 0.1.x, and 0.2.0 to 0.2.5   | No. Upgrade to 0.2.6.                                       |

After 1.0.0, the latest 1.x minor release is supported (ADR-0003).

## Reporting a vulnerability

Report a vulnerability privately through GitHub's private vulnerability
reporting: open the repository's
[Security tab and choose "Report a vulnerability"](https://github.com/pyeconomics-dev/pyeconomics/security/advisories/new).
Never open a public issue, discussion or pull request for a vulnerability.

Please include the affected version, a description of the issue and its impact,
and steps to reproduce it. Never include a real API key or other secret in the
report; describe where it leaks instead.

## What happens next

pyeconomics has one maintainer, so these are targets, not guarantees:

| Stage                     | Target                                                        |
|---------------------------|---------------------------------------------------------------|
| Acknowledge the report    | Within 3 business days                                        |
| Assess and rate severity  | Within 7 days, using CVSS                                     |
| Fix Critical or High      | Within 30 days, before any new feature work (ROADMAP §5 "Vulnerability handling") |
| Fix Medium or Low         | Tracked as an issue with an owner; fixed in a following release |

You are kept informed in the private advisory thread, and credited in the
advisory unless you prefer not to be.

## Advisories, yanks and key rotation

- **Advisory.** A vulnerability in a released version gets a GitHub security
  advisory naming the affected and fixed versions, a CVE where one is
  assigned, and a patched release. Example:
  [GHSA-j6rp-vwwv-jrr8](https://github.com/pyeconomics-dev/pyeconomics/security/advisories/GHSA-j6rp-vwwv-jrr8),
  the FRED API key logged by 0.2.0 to 0.2.5 and fixed in 0.2.6.
- **Yank.** A compromised or dangerously broken release is yanked from PyPI, so
  resolvers skip it unless it is pinned exactly. A published version number is
  never reused.
- **Key rotation.** When a version could have exposed a credential, such as a
  data provider's API key, the advisory tells users which keys to revoke and
  reissue at the provider. pyeconomics never needs to see a key to rotate it.
- **Releases.** Packages are published from GitHub Actions through PyPI
  Trusted Publishing with attestations; no PyPI API token exists. Verify a
  release's provenance on its PyPI page.
