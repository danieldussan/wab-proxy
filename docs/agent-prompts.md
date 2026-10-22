# Prompts para agentes de IA

Abre tu agente (Claude Code, Codex, OpenCode…) **dentro de la carpeta del repo**. Todos leen `AGENTS.md` (Claude Code vía `CLAUDE.md`).

> 🔒 **Las contraseñas se escriben en el panel, nunca en el chat.** Si pegas una en el chat, cámbiala después.

## Instalación guiada completa (recomendado)

```
Lee AGENTS.md. Abre el panel (start-dashboard.sh --no-open), dame el enlace y guíame
paso a paso para configurar mis proxies de WhatsApp en una VPS. Explica cada paso en
una frase, verifica cada fase y pídeme confirmación antes de tocar la VPS.
No leas mi .env ni me pidas contraseñas por el chat.
```

## Solo diagnosticar

```
Ejecuta ./scripts/doctor.sh y ./scripts/deploy.sh status, interpreta el resultado y dime
qué falla y cómo arreglarlo usando docs/04-troubleshooting.md. No leas mi .env.
```

## Añadir una cuenta

```
Quiero añadir una cuenta más. Abre el panel para que yo agregue el proxy ahí; luego
pruébalo, despliega y dime qué datos poner en el iPhone.
```

## Rotar credenciales de proxy

```
Voy a cambiar las credenciales de mis proxies en el panel. Cuando las guarde, prueba los
proxies, despliega y confirma con las sondas que cada cuenta mantiene su IP.
```

## English

```
Read AGENTS.md. Start the dashboard (start-dashboard.sh --no-open), give me the link and
walk me step by step through setting up per-account WhatsApp proxies on my VPS. Confirm
before touching the VPS. Never read my .env or ask me for passwords in chat.
```
