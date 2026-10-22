# Per-account WhatsApp proxy (VPS + Tailscale + gost)

[🇪🇸 Español](README.md) · 🇬🇧 English

Each WhatsApp account (e.g. a cloned app on iPhone) reaches the internet through **its own fixed IP**, via your own VPS. Every account gets a dedicated [gost](https://github.com/ginuerzh/gost) container and can be switched on/off independently.

```
iPhone (WhatsApp → Settings → Proxy)
   │  over Tailscale (private VPN)
   ▼
Your VPS ── one gost container per account ──► ISP SOCKS5 proxy (fixed IP) ──► WhatsApp
```

> ⚠️ **Read first**
> - This is experimental. WhatsApp may block modified clients or proxy IPs. **Use test numbers, not important accounts.**
> - **Calls do not go through the proxy** and would use your real IP.
> - You must buy the fixed-IP SOCKS5 proxies and the VPS yourself.

## Quick start (dashboard, no terminal skills needed)

Requires **Python 3** and **ssh** on your computer (Linux, macOS, or Windows with WSL).

```bash
./start-dashboard.sh
```

A page opens in your browser (reachable only from your computer) and walks you through: **1)** your proxies (it URL-encodes special characters and can test them), **2)** your VPS (prepare + deploy), **3)** status & on/off control, **4)** the exact values to type into WhatsApp on the iPhone.

You can also ask an AI agent (Claude Code, Codex, OpenCode) to guide you — see [docs/agent-prompts.md](docs/agent-prompts.md). **Type passwords into the dashboard, not into the chat.** Detailed guides are currently in Spanish.

Manual / terminal alternative:

```bash
cp .env.example .env && chmod 600 .env     # paste PROXY_1, PROXY_2, ...
cp hosts.conf.example hosts.conf           # put wa@YOUR_VPS_IP
./scripts/doctor.sh && ./scripts/verify-proxies.sh
./scripts/prepare-vps.sh root@VPS_IP       # once per new VPS (Debian/Ubuntu)
./scripts/deploy.sh --env
```

In WhatsApp on the phone (Tailscale ON): Settings → Storage and data → Proxy → address = the VPS **Tailscale IP**, chat port `5100+n`, media port `5200+n`, and **turn the chat TLS toggle OFF** (gost tunnels raw TCP; see [how it works](docs/how-it-works.md)).

Account *n* ports: chat `5100+n`, media `5200+n`, probe `5300+n`.

## Security

`.env` and `hosts.conf` are git-ignored — never commit them. The dashboard listens only on 127.0.0.1 behind a random token and never shows passwords. Proxy ports listen only on the Tailscale IP; the firewall only allows public SSH (plus fail2ban).

## License

MIT. Independent project, not affiliated with WhatsApp/Meta, Tailscale or any proxy vendor.
