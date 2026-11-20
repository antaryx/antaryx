# Security

This repository holds a GitHub profile page: a README, generated SVG images, a Python script that draws them, and one workflow that redraws them
daily. If you find a problem in any of it (for example a way the script could be made to draw something it should not), write to
**antaryx@proton.me**. Please do not open a public issue for anything security-related.

What the script reads: public GitHub data for this account, and the public CISA "Known Exploited Vulnerabilities" feed. Everything fetched is reduced to
printable ASCII and length-limited before it is drawn. The workflow runs with `contents: write` only and uses a single action pinned by commit SHA.
