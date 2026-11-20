#!/usr/bin/env bash
# Makes data/plumbline-scan.txt: a real plumbline scan of a STOCK Ubuntu container (never of your own machine), verified before it runs.
# Needs: docker, curl, sha256sum. The release is checked against its checksums and, if the cosign container can be pulled, its keyless signature.
set -euo pipefail
V=${PLUMBLINE_VERSION:-2.0.1}; IMG=${IMAGE:-ubuntu:24.04}; W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
BASE=https://github.com/antaryx/plumbline/releases/download/v$V
cd "$W"; for f in plumbline_${V}_linux_amd64.tar.gz checksums.txt checksums.txt.sig checksums.txt.pem; do curl -fsSLO "$BASE/$f"; done
sha256sum -c --ignore-missing checksums.txt
chmod a+rx "$W"; chmod a+r checksums.txt checksums.txt.sig checksums.txt.pem
docker run --rm --network host -v "$W":/w:ro -w /w ghcr.io/sigstore/cosign/cosign:v2.4.1 verify-blob checksums.txt --signature checksums.txt.sig --certificate checksums.txt.pem \
  --certificate-identity-regexp 'https://github.com/antaryx/plumbline/.*' --certificate-oidc-issuer https://token.actions.githubusercontent.com
tar -xzf plumbline_${V}_linux_amd64.tar.gz plumbline; chmod a+rx plumbline
DIGEST=$(docker image inspect "$IMG" --format '{{index .RepoDigests 0}}' 2>/dev/null || echo "$IMG")
out=$(docker run --rm --network host -v "$W/plumbline":/usr/local/bin/plumbline:ro "$IMG" bash -c '
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq >/dev/null 2>&1 && apt-get install -y -qq --no-install-recommends openssh-server sudo cron rsyslog libpam-pwquality >/dev/null 2>&1
  . /etc/os-release; echo "TARGET: $PRETTY_NAME (docker image '"$IMG"' + openssh-server sudo cron rsyslog libpam-pwquality, default configuration)"
  plumbline scan --no-color --redact 2>/dev/null')
{ echo "# plumbline v$V (linux/amd64): sha256 checked against checksums.txt and the keyless cosign signature verified"; echo "# image: $DIGEST"
  echo "# command: plumbline scan --no-color --redact   (run as root inside the container; nothing of this host is scanned)"; echo "$out"; } > "$(dirname "$0")/../data/plumbline-scan.txt"
echo "written data/plumbline-scan.txt"
