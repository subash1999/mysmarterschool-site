# Validation record — 2026-10-19

## Product site

- Plain HTML/CSS, eight public pages plus a custom 404 document; no runtime JavaScript, analytics, remote fonts or external subresources.
- Browser checks passed all 18 page/viewport combinations at 1440×900 and 390×844, plus 52 internal links/anchors. Images decoded, no horizontal overflow or JavaScript errors.
- Lighthouse 12.8.2: all eight public pages scored **100 performance / 100 accessibility / 100 SEO** on mobile; desktop home scored **100 / 100 / 100**. Home and teacher-guide audits were refreshed after the final marks screenshot update. See `lighthouse-summary.json` for measurement times.
- Static checker passed nine documents and the 32-image manifest. Static build contains 57 entries and excludes PHP, tooling, Git data, reports, design previews and server configuration.

## Demo evidence

- 16 distinct app screens, each captured as WebP at both requested viewport sizes. The manifest records role, caption, dimensions and app route.
- Fresh loopback-only MySQL database; app `DatabaseSeeder` followed by a synthetic supplement. School: Demo Academy. Generated demo identities and reserved `.test` contact addresses.
- Screens cover super admin, school admin, teacher, accountant and guardian workflows. A separate student login was not found, so no such login is advertised.
- The application checkout was read-only. No school environment file, SQL import, production connection or tenant screenshot was used. Source upload directories were excluded.
- The app’s existing mobile marks table fixes its first three columns and clips some entry fields at 390px. The mobile capture preserves that behavior; the public guide uses the desktop marks image. No application layout was changed.

## Tooling and deployment

- 19 Python tests passed: exact file boundaries, backups/preservation, backup failure before writes, recovery reporting after partial publication, symlinks and demo-copy regressions.
- Two Node safety tests passed. `actionlint`, including its shell checks, passed the GitHub workflow.
- Existing app pipeline inspected read-only: four SSH secret names matched; no Actions variables were listed. No secret value was retrieved from GitHub. The owner separately approved reusing the existing server SSH key; direct file transfer populated the new encrypted secret without displaying key contents, and the temporary local copy was deleted after deployment.
- Approved destination: `/home/subashnc/public_html`, shared with its exact `subashn.com.np` primary alias. A complete live Domains UI audit confirmed all other listed roots are separate. The publisher enforces an exact 48-file manifest and filesystem guards; domain mappings require a fresh UI audit after changes. Existing `.htaccess` and unrelated files are preserved.
- Main-site blank index backed up locally before deployment: HTTP 200, 161 bytes. The publisher also backs up every overwritten server file before any write.
- Independent OpenAI reviews found issues in input symlinks, overlapping roots and screenshot framing; confirmed fixes were re-reviewed. Review used OpenAI only because this workspace prohibits other vendors.

## Hosted deployment and remaining checks

- Public repository created and approved first push completed at `dd9999e`. CI passed; all four SSH secrets and the verified host fingerprint are configured. `DEPLOY_ENABLED=true` activates automatic publication on pushes to `main`.
- SSH authentication and the exact 48-file server write plan passed before publication. The [first real Actions deployment](https://github.com/subash1999/mysmarterschool-site/actions/runs/39187043541/attempts/2) passed checks and deployment, recorded the expected commit, and reported its completed backup before publication.
- The initial action attempt stopped before publication because its negotiated ECDSA key differed from the ED25519 pin used by local OpenSSH. All public host-key fingerprints were verified through the trusted ED25519 connection and matched an independent endpoint scan. The action now pins the verified ECDSA key; fingerprint checking remains required.
- Host Python 3.9.25 and the complete Domains UI were verified. The jailed shell's UAPI wrapper cannot run, so that runtime dependency was removed following architecture review. The exact file manifest, printed write plan and explicit activation gate replace it; this does not automatically detect later domain-mapping changes.
- Public verification is currently blocked by cPGuard's human-verification page for this network on both domains. Its HTTP 200 is not the marketing site or a successful tenant check. The pre-deployment tenant status was 302; the unchanged-status comparison, live title and hosted Lighthouse remain unverified until the challenge is cleared. Lighthouse results above are local-preview measurements only.

## Portfolio companion

- Added the owner-supplied Smart School case study to `index.template.html`, using the existing bilingual pattern and four demo WebPs.
- Ran the repository’s actual bake script in an isolated preview with its workflow environment. English/Japanese, desktop/mobile, image decoding, individual keyboard-link focus and dark-theme checks passed.
- Tracked `index.html` remains byte-for-byte unchanged. Only the template and four assets were committed locally as `c389aec`. Portfolio push to `main` requires separate owner approval.
