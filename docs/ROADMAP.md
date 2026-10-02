# Roadmap

Key: ✅ from the original brief · ➕ added during planning · ⚠️ clashes with local-only or has a hard limit

## Feature map

### A. Network snapshot: "What's on my network?"

| # | Feature | Source | Notes |
|---|---|---|---|
| A1 | My connection: address, network range, router | ✅ | Reads settings only |
| A2 | Find all connected devices | ✅ | No admin (see D-004) |
| A3 | Identify devices: manufacturer, name, likely type | ✅ | Offline only. Bundled manufacturer list (D-016). Randomised "private" addresses are labelled, not "Unknown" |
| A4 | User names devices and marks them as trusted | ➕ | |
| A5 | Online/offline, first seen, last seen | ➕ | |
| A6 | Simple network map | ✅ ⚠️ | Mesh units and extenders are hard to detect |
| A7 | Public IP | ✅ ⚠️ | Router first; outside lookup only by consent |
| A8 | Wi-Fi details: name, band, signal, channel | ➕ | |
| A9 | IPv6 devices | ➕ | Later |

### B. Speed and traffic

| # | Feature | Source | Notes |
|---|---|---|---|
| B1 | This computer's live upload and download | ✅ | |
| B2 | Bandwidth per device | ✅ ⚠️ | Only if the router shares its counters |
| B3 | Internet speed test | ✅ ⚠️ | Opt-in only |
| B4 | Connection quality to the router | ➕ | |
| B5 | Which DNS server is used | ➕ | |

### C. Security audit: "Am I safe?"

| # | Feature | Source | Notes |
|---|---|---|---|
| C1 | Open ports on each device | ✅ | Short list of common ports |
| C2 | Risky services (Telnet, FTP, file sharing, remote desktop) | ✅ | |
| C3 | Wi-Fi encryption type | ✅ | |
| C4 | Default passwords | ✅ ⚠️ | See O-3. Never guess many passwords |
| C5 | Router checks: admin page without HTTPS, UPnP on | ➕ | |
| C6 | Alert when a new, unknown device joins | ➕ | Shown at the next scan until scheduled scans (H4) exist |
| C7 | Security score with "fix these first" | ➕ | |
| C8 | Guest network advice for smart devices | ➕ | |
| C9 | Outdated firmware with known vulnerabilities | ➕ | Later |
| C10 | Detect router impersonation (ARP spoofing) | ➕ | Later |

### D. Efficiency: "Why is my internet slow?"

| # | Feature | Source | Notes |
|---|---|---|---|
| D1 | Weak Wi-Fi signal warning | ➕ | |
| D2 | 2.4 GHz vs 5 GHz advice | ➕ | |
| D3 | Crowded Wi-Fi channel | ➕ | |
| D4 | Devices using the most bandwidth | ✅ ⚠️ | Depends on B2 |

### E. Recommendations: "What do I do?"

| # | Feature | Source | Notes |
|---|---|---|---|
| E1 | What it is, why it matters, how to fix it | ✅ | |
| E2 | Trusted tools list stored in the app | ✅ | |
| E3 | Mark as fixed, then re-check | ➕ | |
| E4 | Ignore with a reason | ➕ | |
| E5 | Router-brand-specific instructions | ➕ | Later |

### F. History and reports

| # | Feature | Source | Notes |
|---|---|---|---|
| F1 | Encrypted local history | ➕ | |
| F2 | What changed since last scan | ➕ | |
| F3 | Printable HTML report, with a share-safe version | ➕ | |
| F4 | Delete all my data | ➕ | |

### G. Trust and privacy

| # | Feature | Source | Notes |
|---|---|---|---|
| G1 | Hard rule: never scan outside the home network | ➕ | |
| G2 | Permission screen before the first scan | ➕ | |
| G3 | Privacy receipt after each scan | ➕ | |
| G4 | Automated no-internet test | ➕ | |
| G5 | Updates without phoning home | ➕ ⚠️ | See O-2 |
| G6 | No telemetry, no web assets, library audit | ➕ | |

### H. Usability

| # | Feature | Source | Notes |
|---|---|---|---|
| H1 | Plain-language interface | ✅ | |
| H2 | Explanations for unavoidable terms | ➕ | |
| H3 | First-run walkthrough | ➕ | |
| H4 | Scheduled background scans | ➕ | Later |

## Phases

| Phase | Theme | Features | Interface | How we prove it works |
|---|---|---|---|---|
| 0 | Setup | Repo, uv, tooling, GitHub security | None | Tests and security checks run on Windows and Ubuntu in GitHub Actions |
| 1 | See | A1, A2, A3, G1, G2 | Rich | Our device list matches the router's own list for at least 90% of devices, and every miss is explained. Read-only: nothing is saved to disk |
| 2 | Remember | F1, A4, A5, F2, C6, F4 | Rich | A phone leaving and rejoining is noticed. After "delete all", nothing is left on disk |
| 3 | Check | C1, C2, C3, C5, C7, E1, E2, E3, E4 | Rich | A deliberately unsafe test service is flagged. The warning clears once it's fixed. No false alarms on clean devices |
| 4 | Tune | A8, B1, B4, B5, D1, D2, D3 | Rich | Signal warning appears when far from the router. Readings match the OS's own Wi-Fi details |
| 5 | Show | H1, H2, H3, A6, F3, G3 | Textual + HTML report + launcher | A non-technical person uses it unaided and explains a finding back in their own words |
| 6 | Prove and ship | G4, G5, G6, packaging | | Full app runs with internet blocked by the firewall, with zero outbound attempts. Library audit is clean |
| Later | Stretch | A7, A9, B2, B3, C4, C8, C9, C10, D4, E5, H4 | | Each gets its own test |
