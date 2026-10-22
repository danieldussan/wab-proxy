# Prompts para agentes de IA

Abre tu agente (Claude Code, Codex, OpenCode…) **dentro de la carpeta del repo**. Todos leen `AGENTS.md` (Claude Code vía `CLAUDE.md`).

> 🔒 **Las contraseñas se escriben en el panel, nunca en el chat.** Si pegas una en el chat, cámbiala después.

## Instalación guiada completa (recomendado)

```
Lee AGENTS.md. Abre el panel con `wa agent open` y guíame paso a paso para configurar
mis proxies de WhatsApp en una VPS. Explica cada paso en una frase y verifica cada fase.
Pídeme las credenciales y los permisos por el panel (wa agent), no por el chat.
No leas mi .env.
```

## Solo diagnosticar

```
Ejecuta `wa doctor` y `wa agent status`, interpreta el resultado y dime
qué falla y cómo arreglarlo usando docs/04-troubleshooting.md. No leas mi .env.
```

## Añadir una cuenta

```
Quiero añadir una cuenta más. Pídeme el proxy con `wa agent ask-proxy`; luego pruébalo,
pide permiso para desplegar y dime qué datos poner en el iPhone.
```

## Rotar credenciales de proxy

```
Quiero cambiar las credenciales de un proxy. Pídemelas con `wa agent ask-proxy --n N`;
luego prueba los proxies, pide permiso para desplegar y confirma con las sondas que cada
cuenta mantiene su IP.
```

## English

```
Read AGENTS.md. Open the dashboard with `wa agent open` and walk me step by step through
setting up per-account WhatsApp proxies on my VPS. Ask me for credentials and permissions
through the dashboard (wa agent), never in chat. Never read my .env.
```
