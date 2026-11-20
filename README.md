<!-- Every card below is an animated SVG drawn by scripts/render_cards.py (Python standard library, no third-party widget services, no trackers)
     and refreshed weekly by .github/workflows/update-cards.yml. The scorpion is Scorpius; the red star is Antares. Colours: the Antaryx desktop palette.
     Spacing is baked into the SVGs: keep the images of a row on one line with no spaces between them. -->
<div align="center">
<img src="./cards/hero.svg" width="100%" alt="ANTARYX. Security. Research. Adaptation. The Scorpius constellation with its red star, Antares." /><br>
<img src="./cards/whoami.svg" width="100%" alt="A terminal: whoami, the mission, the rules of engagement and a plumbline scan." /><br>
<img src="./cards/blue.svg" width="49.8%" alt="Defense vectors, blue team: anomaly detection, forensic architecture, system hardening." /><img src="./cards/red.svg" width="49.8%" alt="Offense vectors, red team: vulnerability research, payload engineering, stealth operations. Scope-gated, authorized targets only." /><br>
<img src="./cards/divider.svg" width="100%" alt="" />
</div>

<div align="center">

### `>_ git log --author=antaryx --stat`

</div>

<div align="center">
<a href="https://github.com/antaryx/plumbline"><img src="./cards/plumbline.svg" width="49.8%" alt="plumbline: a deterministic, offline, evidence-first host security auditor for Linux, written in Go." /></a><a href="https://github.com/antaryx/plumbline-action"><img src="./cards/plumbline-action.svg" width="49.8%" alt="plumbline-action: runs plumbline on a GitHub Actions runner and publishes SARIF findings." /></a><br>
<img src="./cards/activity.svg" width="100%" alt="Weekly commit activity of plumbline over the last 52 weeks." /><br>
<img src="./cards/stack.svg" width="100%" alt="Core stack: Python, Go, Docker, Bash, Django, Linux and WSLg, Git." />
</div>

<div align="center">

### `>_ cat /etc/method`

</div>

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#151b21","primaryTextColor":"#e6edf3","primaryBorderColor":"#6aa8ff","lineColor":"#5ccfe6","secondaryColor":"#151b21","tertiaryColor":"#0b0f12","fontFamily":"ui-monospace, Menlo, Consolas, monospace"}}}%%
flowchart LR
    A(["scope and<br/>authorization"]) --> B["recon"]
    B --> C["hypothesis"]
    C --> D["test, in scope"]
    D --> E[("evidence")]
    E --> F["report"]
    F --> G["harden and fix"]
    G -. "what the defence missed" .-> B
    style A stroke:#ff6b81,stroke-width:2px
```

<div align="center">
<img src="./cards/rules.svg" width="100%" alt="Rules of engagement: authorized targets only, scope before scan, evidence over opinion, report and never weaponise." />
</div>

<br>

<div align="center">

> *"The most dangerous vulnerabilities are the ones that cast no shadow."*

</div>

<details>
<summary><code>>_ cat /etc/operational_matrix.conf</code></summary>
<br>

**Operating in the void between defensive architecture and offensive exploitation.** **Antaryx** is a hybrid security research node dedicated to stealth automation, digital forensics and advanced payload engineering. I do not just monitor the perimeter; I become the noise to understand the threat.

| `[ DEFENSE_VECTORS // BLUE TEAM ]` | `[ OFFENSE_VECTORS // RED TEAM ]` |
|---|---|
| **Anomaly detection:** parsing the void for unauthorized telemetry and anomalous behaviours. | **Vulnerability research:** dissecting logic flaws, misconfigurations and system weaknesses. |
| **Forensic architecture:** reconstructing fragmented digital footprints and auditing access logs. | **Payload engineering:** crafting silent, adaptive execution chains. |
| **System hardening:** architecting impenetrable WSL / Linux environments and secure containerised infrastructure. | **Stealth operations:** bypassing static analysis through behavioural mutation and footprint reduction. |

> [!IMPORTANT]
> Offensive work happens only against targets I am authorized to test: HackTheBox, TryHackMe, CTF platforms and my own lab. Nothing here is a tool for anyone else's systems.

</details>

<div align="center">

### `>_ netstat -ano | grep ESTABLISHED`

*Establish a secure handshake via encrypted channels, or follow the training nodes:*

<a href="https://app.hackthebox.com/users/3514431"><img src="./cards/btn-htb.svg" width="286" alt="HackTheBox profile /users/3514431" /></a>&nbsp;&nbsp;<a href="https://tryhackme.com/p/antaryx"><img src="./cards/btn-thm.svg" width="286" alt="TryHackMe profile /p/antaryx" /></a>&nbsp;&nbsp;<a href="mailto:antaryx@proton.me"><img src="./cards/btn-mail.svg" width="286" alt="Secure comm: antaryx@proton.me" /></a>

<br>

<img src="./cards/footer.svg" width="100%" alt="exit. Identity verified. PGP fingerprint unavailable. Connection to 127.0.0.1 closed." />

<sub>cards drawn by <a href="./scripts/render_cards.py"><code>scripts/render_cards.py</code></a> and refreshed weekly: no third-party widgets, no trackers, no JavaScript</sub>

</div>
