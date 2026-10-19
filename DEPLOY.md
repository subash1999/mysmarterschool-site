# Deploy Smart School to Himalayan Host

## Approved destination and domain audit

The owner explicitly approved `/home/subashnc/public_html` on 2026-10-19. cPanel also maps its primary domain, `subashn.com.np`, to that directory; public DNS serves the portfolio from GitHub Pages. Its portfolio repository and deployment stay separate.

The complete cPanel **Domains** table was expanded and reviewed on 2026-10-19, including the absolute paths in its File Manager links. Only the approved primary alias shares the product root. Every other listed document root is outside it. No tenant application was opened. Keep detailed audit evidence private; customer domain names do not belong in this public repository.

**Repeat that complete UI audit after changing any domain mapping, before the next deployment.** The publisher does not automatically recheck cPanel mappings. The host’s jailed shell cannot execute its UAPI wrapper, so this site has no runtime UAPI dependency and needs no extra API credential or relaxed server permissions.

`deployment.json` pins the approved root and lists every deployable file explicitly. Both the build and publisher reject any missing or unlisted file. The publisher rejects symlinks, path escapes and destination directory collisions, prints the complete write plan, and preserves existing server configuration, including `.htaccess`. It changes no DNS, domain configuration or tenant scripts.

## Backups and write plan

The original main-domain blank index was downloaded before deployment: HTTP 200, 161 bytes, retained locally outside document roots. The first server deployment also backs up the current server file.

Every deployment backs up all files it will overwrite under `/home/subashnc/backups/mysmarterschool-site/<UTC timestamp>/` before changing any destination file. A backup failure stops publication. Assets are copied before HTML, with atomic replacement per file. Unrelated files and directories are preserved; no deletion or directory wipe is used.

After cloning the approved commit to the server, this command builds inside the checkout and validates/prints the complete write plan without changing published files:

```sh
/usr/bin/python3 /home/subashnc/repositories/mysmarterschool-site/tools/deploy.py --check
```

Review the plan against `deployment.json`. It must contain only the product site’s static files below the approved root. Existing host defaults control caching, compression and error routing.

## GitHub Actions CI/CD

The workflow reuses the existing app pipeline’s four secret **names**: `SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_PRIVATE_KEY`. The application repository remains read-only. GitHub does not reveal stored secret values for copying.

Checks run on PRs and pushes. After checks pass, an enabled push to `main` or manual run on `main` fetches that exact commit into `/home/subashnc/repositories/mysmarterschool-site` and runs the guarded publisher. It never invokes the app’s tenant deployment scripts. Actions are pinned to reviewed commits, deployments are serialized, and dirty or symlinked server checkouts are refused.

Production CI/CD was enabled on 2026-10-19. Every push to `main` runs checks and automatically publishes that exact checked commit. The [first Actions deployment succeeded](https://github.com/subash1999/mysmarterschool-site/actions/runs/39187043541/attempts/2); this route requires no cPanel deployment clicks.

One-time configuration (completed for this repository):

1. Store the four matching Actions secrets under **Settings → Secrets and variables → Actions**. The owner approved reusing the app pipeline’s existing server key. It was transferred directly into the encrypted secret without displaying its contents; the temporary local copy was deleted after the successful Actions deployment. The application repository and original server key remain unchanged.
2. Set Actions variable `SSH_HOST_FINGERPRINT` to `SHA256:13RkNDZvbg//aHif6V4sXBapE1Rz6OdgF/sebfulvAA`. This is the host’s ECDSA key, negotiated by the pinned action. On 2026-10-19 it was read from the loopback SSH service through an authenticated connection pinned to the independently verified ED25519 key, and matched a separate public-endpoint scan. The ED25519 fingerprint is `SHA256:zqrA1L0RCRtEq0o/mWL8Wr7FFRTxIPOp9TiK+sglzKA`; substituting it for the action’s negotiated ECDSA key causes a fingerprint mismatch. Reverify through a trusted channel after any host-key change.
3. Confirm the complete domain audit remains current and review the exact file list and write plan. Python 3.9.25, SSH authentication and the 48-file check-mode plan were verified before publication. The successful Actions log records the checked commit, completed backup and publication.
4. `DEPLOY_ENABLED` is set to the exact value `true`. Set it to `false` to pause publication while retaining CI checks. Re-enable only after required root audits and write-plan checks are current.

A changed domain mapping requires disabling deployment and repeating the UI audit. Changes to the public file set require a reviewed manifest update. The file guards establish filesystem boundaries; the UI audit establishes which domains serve those paths.

## Owner’s cPanel clicks (manual alternative)

After the public repository exists and its first push is approved:

1. Open **cPanel → Files → Git™ Version Control → Create**.
2. Enable **Clone a Repository**.
3. Clone URL: `https://github.com/subash1999/mysmarterschool-site`.
4. Repository path: `/home/subashnc/repositories/mysmarterschool-site`, outside every document root.
5. Repository name: `mysmarterschool-site`. Select **Create**.
6. Open **Manage → Pull or Deploy**, select the intended `main` branch, and choose **Update from Remote**.
7. Check the displayed commit against the approved commit. Run the write-plan command above and confirm the domain audit is current.
8. Select **Deploy HEAD Commit**. It should report the write plan, backup directory and successful publication.

The checked-in `.cpanel.yml` runs the same publisher. The website itself needs only static file hosting. PHP, tooling, Git data, reports, design previews and server configuration are excluded from deployed files.

Official references: [cPanel deployment guide](https://docs.cpanel.net/knowledge-base/web-services/guide-to-git-deployment/), [Git Version Control](https://docs.cpanel.net/cpanel/files/git-version-control/).

## After deployment

Check the Actions result, then verify HTTP 200 and title `Smart School — School management for Nepal` at `https://mysmarterschool.com/`. Check the guide, images and About page on desktop/mobile, and rerun public Lighthouse.

Only for the expressly requested post-deployment health check, make an unauthenticated status request to the production app and compare with its pre-deployment status. Do not log in, load school records or take tenant screenshots. No tenant app was contacted while making demo assets or auditing cPanel. The pre-deployment status was recorded separately without saving response content. After the first Actions deployment, this network received cPGuard’s human-verification page on both domains; that response is not proof of either site’s health. Live title, hosted Lighthouse and the tenant-status comparison remain pending until the verification is cleared.

If publication fails, inspect the reported backup and restore only affected product-site files. Never restore over a tenant directory. New files are preserved rather than deleted automatically.
