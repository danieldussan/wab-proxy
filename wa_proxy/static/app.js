"use strict";
// ---------------------------------------------------------------- textos (ES / EN)
const I18N = {
es: {
  title: "WhatsApp Proxy", quit: "Cerrar panel", lang: "Idioma", theme: "Cambiar tema",
  tab_sum: "Resumen", tab_prx: "Proxies", tab_vps: "VPS", tab_acc: "Cuentas", tab_ios: "iPhone",
  ag_none: "Sin agente conectado", ag_on: "Agente conectado", ag_idle: "esperando", ag_hint: "Un agente de IA puede conectarse a este panel con «wa agent».",
  al_title: "El agente necesita algo de ti:", al_btn: "Responder", al_more: "solicitudes pendientes",
  w_tools: "Faltan herramientas en este equipo: ", w_conn: "Se perdió la conexión con el panel. ¿Lo cerraste? Ábrelo de nuevo con «wa dashboard».",
  k_prx: "Proxies verificados", k_vps: "VPS preparadas", k_run: "Cuentas encendidas", k_last: "Última verificación",
  k_allok: "Todos OK", k_bad: "Hay problemas", k_untested: "Sin probar", k_none: "Sin datos", k_dep: "{n} desplegando", k_dis: "IPs distintas",
  ago_now: "ahora", ago_min: "hace {n} min", ago_h: "hace {n} h", ago_d: "hace {n} d",
  st_steps: "Pasos", st_stepsd: "Tu avance de principio a fin.", s_prx: "Proxies", s_vps: "VPS", s_dep: "Desplegar", s_ios: "iPhone",
  s_prx_d: "Verificadas: {n}", s_prx_t: "Pendiente de probar", s_vps_d: "Preparada", s_vps_t: "Sin preparar", s_dep_d: "En marcha: {n}", s_dep_t: "Pendiente", s_run: "En curso…", s_ios_t: "Pendiente",
  nx_acc: "Siguiente: añade tu primer proxy", nx_acc_d: "Pega los datos que te dio tu proveedor de proxies (pestaña Proxies).",
  nx_test: "Siguiente: prueba tus proxies", nx_test_d: "Pulsa «Probar proxies» para comprobar que funcionan.",
  nx_fix: "Hay que corregir tus proxies", nx_fix_d: "Mira el resultado de la prueba en la pestaña Proxies.",
  nx_vps: "Siguiente: registra tu VPS", nx_vps_d: "Escribe la IP de tu servidor (pestaña VPS).",
  nx_prep: "Siguiente: prepara la VPS", nx_prep_d: "Pulsa «Preparar» en la pestaña VPS.",
  nx_dep: "Siguiente: despliega los proxies", nx_dep_d: "Pulsa «Desplegar proxies» en la pestaña VPS.",
  nx_done: "¡Todo en marcha!", nx_done_d: "Configura el iPhone con los datos de la pestaña iPhone.",
  nx_wait: "Consultando el estado de la VPS…", nx_wait_d: "",
  nx_req: "El agente espera tu respuesta", nx_req_d: "Responde a su solicitud para que pueda continuar.",
  nx_job: "Hay una operación en curso", nx_job_d: "Mira el avance en la consola de la derecha.",
  go: "Ir", view: "Ver",
  accounts: "Tus cuentas", accounts_d: "Estado real en la VPS.", acc: "Cuenta", state: "Estado", exit_ip: "IP de salida", ports: "Puertos",
  st_up: "Encendida", st_down: "Apagada", st_other: "Revisar", st_none: "Sin desplegar",
  start: "Encender", stop: "Apagar", restart: "Reiniciar",
  p_title: "Tus proxies", p_d: "Una fila por cada cuenta de WhatsApp. Cada cuenta necesita su propio proxy SOCKS5 con IP fija. Los datos los entrega tu proveedor.",
  name: "Nombre (opcional)", name_ph: "Ej. Ventas", server: "Servidor", port: "Puerto", user: "Usuario", pass: "Contraseña", pass_keep: "•••••• (sin cambios)",
  remove: "Quitar", add: "Añadir cuenta", paste: "Pegar URL socks5://…", paste_ph: "socks5://usuario:clave@servidor:puerto", paste_btn: "Rellenar", paste_bad: "No pude leer esa URL.",
  save: "Guardar", saved: "Guardado.", test: "Probar proxies", testing: "Probando…", test_note: "No gasta datos de WhatsApp: solo comprueba IP de salida y alcance.",
  no_accounts: "Aún no hay cuentas. Pulsa «Añadir cuenta».",
  res_ip: "IP de salida", dup: "Dos cuentas salen por la MISMA IP. Cada cuenta debe tener una IP distinta.",
  partial: "Funciona solo por {ok} de {n} IPs de la pasarela del proveedor. Como el DNS rota entre ellas, fallará de forma intermitente. Pide a tu proveedor que lo corrija.",
  inconsistent: "Cada pasarela devuelve una IP de salida distinta: la IP de la cuenta cambiaría. Consulta a tu proveedor.",
  test_all_ok: "Todos los proxies funcionan.", test_some_bad: "Algún proxy falla. Revisa usuario, contraseña, puerto o contacta a tu proveedor.",
  v_title: "Tu VPS", v_d: "El servidor donde correrán los proxies (lo compras aparte, Ubuntu o Debian). Aquí lo registras y lo preparas.",
  vps_ip: "IP de la VPS", vps_name: "Nombre (opcional)", vps_add: "Añadir VPS", vps_none: "Aún no hay VPS.", vps_del: "Quitar de la lista",
  prep: "Preparar VPS (solo la primera vez)", prep_help: "Instala Docker, Tailscale y el firewall. Tarda unos minutos.",
  prep_user: "Usuario inicial", prep_pass: "Contraseña de root del proveedor", prep_pass_h: "Se usa una sola vez para instalar una clave SSH. No se guarda. Déjala vacía si ya añadiste la clave del panel en tu proveedor.",
  prep_go: "Preparar", deploy: "Desplegar proxies", deploy_help: "Sube tus proxies a la VPS y los enciende.",
  key_title: "Clave SSH del panel", key_help: "Si tu proveedor te deja añadir una clave SSH al crear la VPS, pega esta.", key_show: "Crear / mostrar clave", copy: "Copiar", copied: "¡Copiado!",
  loading: "Consultando…", no_conn: "Sin conexión", no_prep: "Sin preparar", not_deployed: "Sin desplegar", prepared: "Preparada", refresh: "Actualizar estado", ts_ip: "IP de Tailscale",
  m_nothing: "La VPS está accesible pero aún no hay nada desplegado.", m_denied: "La VPS rechazó la clave SSH: hay que prepararla.",
  m_unreach: "No se puede conectar a la VPS: revisa la IP y que esté encendida.", m_ssh: "No se pudo conectar por SSH.", m_no_ssh: "No se encontró el cliente SSH en este equipo.",
  m_notdeployed: "La VPS está preparada pero aún no se ha desplegado.",
  i_title: "Configurar el iPhone", i_d: "En cada iPhone: instala Tailscale e inicia sesión con la MISMA cuenta de la VPS. Luego en WhatsApp: Ajustes → Almacenamiento y datos → Proxy.",
  f_addr: "Dirección", f_chat: "Puerto de chat", f_media: "Puerto de medios", f_tls: "TLS del chat", tls_off: "APAGADO",
  i_none: "Cuando tu VPS esté desplegada, aquí verás los datos para cada cuenta.", i_warn: "Las llamadas de WhatsApp NO pasan por el proxy. No uses llamadas en estas cuentas.",
  act: "Actividad", live: "En vivo", ev_none: "Aquí verás lo que haga el agente y lo que hagas tú.", console: "Consola", cons_none: "Sin operaciones todavía.",
  ts_auth: "Autoriza la VPS en Tailscale", ts_help: "Abre este enlace, inicia sesión en Tailscale y acepta. Luego vuelve aquí.", ts_open: "Abrir Tailscale",
  who_agent: "El agente", who_user: "Tú",
  k_verify: "Probar proxies", k_prepare: "Preparar VPS", k_deploy: "Desplegar proxies", k_power: "Encender/apagar cuenta",
  e_job_start: "Iniciado: {kind}{alias}", e_job_ok: "Terminó bien: {kind}{alias}", e_job_fail: "Falló: {kind}{alias}",
  e_req_proxy: "El agente pide las credenciales de un proxy", e_req_vps: "El agente pide que registres la VPS", e_req_confirm: "El agente pide tu confirmación", e_req_approve: "El agente pide permiso: {desc}",
  e_req_denied: "Rechazaste una solicitud del agente", e_req_confirmed: "Aceptaste la solicitud del agente", e_proxy_saved: "Guardaste las credenciales del proxy {n}", e_vps_saved: "Registraste la VPS {alias} ({ip})",
  e_approved: "Aprobaste: {desc}", e_accounts_saved: "Guardaste tus proxies", e_vps_added: "Registraste la VPS {ip}",
  ap_prepare: "preparar la VPS {alias}", ap_deploy: "desplegar los proxies en {alias}", ap_power_start: "encender la cuenta {n} en {alias}", ap_power_stop: "apagar la cuenta {n} en {alias}", ap_power_restart: "reiniciar la cuenta {n} en {alias}",
  rq_proxy: "Credenciales del proxy «{name}»", rq_proxy_new: "Credenciales de un proxy nuevo", rq_vps: "Registra tu VPS", rq_confirm: "El agente pide confirmación",
  rq_say: "El agente dice:", rq_later: "Más tarde", rq_cancel: "Cancelar", rq_deny: "Rechazar", rq_accept: "Aceptar", rq_allow: "Permitir", rq_save: "Guardar de forma segura", rq_fields: "Escribir datos", rq_url: "Pegar URL socks5://…",
  rq_secure: "Solo se guardan en tu equipo, en el archivo .env. El agente nunca ve la contraseña: llega directo al panel.",
  rq_pass_secure: "La contraseña se usa una sola vez y no se guarda. El agente no la ve.",
  rq_vps_secure: "Se guarda en tu equipo (hosts.conf). Usa la IP que te dio tu proveedor.",
  ap_q_prepare: "¿Permitir que el agente prepare la VPS?", ap_q_deploy: "¿Permitir que el agente despliegue los proxies?", ap_q_power: "¿Permitir que el agente cambie una cuenta?",
  ap_mod: "Esto modifica el servidor {ip}.", ap_will: "Se hará lo siguiente:",
  ap_p1: "Instalar Docker y Tailscale", ap_p2: "Activar el firewall (solo SSH abierto) y fail2ban", ap_p3: "Crear el usuario «wa» con la clave SSH del panel", ap_p_info: "Tarda unos minutos. Al final tendrás que autorizar la VPS en Tailscale con un botón.",
  ap_d1: "Subir tus proxies y la configuración a la VPS", ap_d2: "Encender una pasarela por cada cuenta", ap_d3: "Comprobar la IP de salida de cada una",
  ap_w1: "{do_} la cuenta {n} en {alias}. Los puertos de las demás no cambian.",
  confirm_quit: "¿Cerrar el panel? Tus proxies y VPS siguen funcionando.", confirm_del: "¿Quitar esta VPS de la lista? (No apaga nada en el servidor.)",
  confirm_rm: "¿Quitar esta cuenta? Los puertos de las demás NO cambian.", closed: "Panel cerrado. Ya puedes cerrar esta pestaña.", err: "Error"
},
en: {
  title: "WhatsApp Proxy", quit: "Close dashboard", lang: "Language", theme: "Toggle theme",
  tab_sum: "Overview", tab_prx: "Proxies", tab_vps: "VPS", tab_acc: "Accounts", tab_ios: "iPhone",
  ag_none: "No agent connected", ag_on: "Agent connected", ag_idle: "waiting", ag_hint: "An AI agent can connect to this dashboard with “wa agent”.",
  al_title: "The agent needs something from you:", al_btn: "Respond", al_more: "pending requests",
  w_tools: "Missing tools on this computer: ", w_conn: "Lost connection to the dashboard. Did you close it? Reopen it with “wa dashboard”.",
  k_prx: "Verified proxies", k_vps: "Prepared VPS", k_run: "Accounts running", k_last: "Last verification",
  k_allok: "All OK", k_bad: "Problems found", k_untested: "Not tested", k_none: "No data", k_dep: "{n} deploying", k_dis: "Distinct IPs",
  ago_now: "just now", ago_min: "{n} min ago", ago_h: "{n} h ago", ago_d: "{n} d ago",
  st_steps: "Steps", st_stepsd: "Your progress from start to finish.", s_prx: "Proxies", s_vps: "VPS", s_dep: "Deploy", s_ios: "iPhone",
  s_prx_d: "Verified: {n}", s_prx_t: "Not tested yet", s_vps_d: "Prepared", s_vps_t: "Not prepared", s_dep_d: "Running: {n}", s_dep_t: "Pending", s_run: "In progress…", s_ios_t: "Pending",
  nx_acc: "Next: add your first proxy", nx_acc_d: "Paste the details from your proxy provider (Proxies tab).",
  nx_test: "Next: test your proxies", nx_test_d: "Press “Test proxies” to check they work.",
  nx_fix: "Your proxies need fixing", nx_fix_d: "See the test result in the Proxies tab.",
  nx_vps: "Next: register your VPS", nx_vps_d: "Enter your server's IP (VPS tab).",
  nx_prep: "Next: prepare the VPS", nx_prep_d: "Press “Prepare” in the VPS tab.",
  nx_dep: "Next: deploy the proxies", nx_dep_d: "Press “Deploy proxies” in the VPS tab.",
  nx_done: "All up and running!", nx_done_d: "Set up the iPhone with the details in the iPhone tab.",
  nx_wait: "Checking the VPS status…", nx_wait_d: "",
  nx_req: "The agent is waiting for your answer", nx_req_d: "Answer its request so it can continue.",
  nx_job: "An operation is in progress", nx_job_d: "Follow it in the console on the right.",
  go: "Go", view: "View",
  accounts: "Your accounts", accounts_d: "Real state on the VPS.", acc: "Account", state: "State", exit_ip: "Exit IP", ports: "Ports",
  st_up: "Running", st_down: "Stopped", st_other: "Check", st_none: "Not deployed",
  start: "Start", stop: "Stop", restart: "Restart",
  p_title: "Your proxies", p_d: "One row per WhatsApp account. Each account needs its own fixed-IP SOCKS5 proxy. Your provider gives you these details.",
  name: "Name (optional)", name_ph: "e.g. Sales", server: "Server", port: "Port", user: "Username", pass: "Password", pass_keep: "•••••• (unchanged)",
  remove: "Remove", add: "Add account", paste: "Paste socks5://… URL", paste_ph: "socks5://user:pass@server:port", paste_btn: "Fill in", paste_bad: "Couldn't read that URL.",
  save: "Save", saved: "Saved.", test: "Test proxies", testing: "Testing…", test_note: "Uses no WhatsApp data: it only checks exit IP and reachability.",
  no_accounts: "No accounts yet. Press “Add account”.",
  res_ip: "Exit IP", dup: "Two accounts exit through the SAME IP. Each account needs a different IP.",
  partial: "Works through only {ok} of {n} IPs of the provider's gateway. Since DNS rotates between them, it will fail intermittently. Ask your provider to fix it.",
  inconsistent: "Each gateway returns a different exit IP: the account's IP would change. Ask your provider.",
  test_all_ok: "All proxies work.", test_some_bad: "A proxy is failing. Check username, password, port, or contact your provider.",
  v_title: "Your VPS", v_d: "The server that will run the proxies (bought separately, Ubuntu or Debian). Register and prepare it here.",
  vps_ip: "VPS IP", vps_name: "Name (optional)", vps_add: "Add VPS", vps_none: "No VPS yet.", vps_del: "Remove from list",
  prep: "Prepare VPS (first time only)", prep_help: "Installs Docker, Tailscale and the firewall. Takes a few minutes.",
  prep_user: "Initial user", prep_pass: "Provider's root password", prep_pass_h: "Used once to install an SSH key. Not stored. Leave empty if you already added the dashboard key at your provider.",
  prep_go: "Prepare", deploy: "Deploy proxies", deploy_help: "Uploads your proxies to the VPS and starts them.",
  key_title: "Dashboard SSH key", key_help: "If your provider lets you add an SSH key when creating the VPS, paste this one.", key_show: "Create / show key", copy: "Copy", copied: "Copied!",
  loading: "Checking…", no_conn: "No connection", no_prep: "Not prepared", not_deployed: "Not deployed", prepared: "Prepared", refresh: "Refresh status", ts_ip: "Tailscale IP",
  m_nothing: "The VPS is reachable but nothing is deployed yet.", m_denied: "The VPS rejected the SSH key: it needs to be prepared.",
  m_unreach: "Can't reach the VPS: check the IP and that it's powered on.", m_ssh: "Couldn't connect over SSH.", m_no_ssh: "The SSH client was not found on this computer.",
  m_notdeployed: "The VPS is prepared but not deployed yet.",
  i_title: "Set up the iPhone", i_d: "On each iPhone: install Tailscale and sign in with the SAME account as the VPS. Then in WhatsApp: Settings → Storage and data → Proxy.",
  f_addr: "Address", f_chat: "Chat port", f_media: "Media port", f_tls: "Chat TLS", tls_off: "OFF",
  i_none: "Once your VPS is deployed, the details for each account will appear here.", i_warn: "WhatsApp calls do NOT go through the proxy. Don't make calls on these accounts.",
  act: "Activity", live: "Live", ev_none: "Here you'll see what the agent does and what you do.", console: "Console", cons_none: "No operations yet.",
  ts_auth: "Authorize the VPS in Tailscale", ts_help: "Open this link, sign in to Tailscale and accept. Then come back here.", ts_open: "Open Tailscale",
  who_agent: "The agent", who_user: "You",
  k_verify: "Test proxies", k_prepare: "Prepare VPS", k_deploy: "Deploy proxies", k_power: "Start/stop account",
  e_job_start: "Started: {kind}{alias}", e_job_ok: "Finished OK: {kind}{alias}", e_job_fail: "Failed: {kind}{alias}",
  e_req_proxy: "The agent asks for a proxy's credentials", e_req_vps: "The agent asks you to register the VPS", e_req_confirm: "The agent asks for your confirmation", e_req_approve: "The agent asks permission: {desc}",
  e_req_denied: "You rejected an agent request", e_req_confirmed: "You accepted the agent's request", e_proxy_saved: "You saved the credentials of proxy {n}", e_vps_saved: "You registered VPS {alias} ({ip})",
  e_approved: "You approved: {desc}", e_accounts_saved: "You saved your proxies", e_vps_added: "You registered VPS {ip}",
  ap_prepare: "prepare VPS {alias}", ap_deploy: "deploy the proxies on {alias}", ap_power_start: "start account {n} on {alias}", ap_power_stop: "stop account {n} on {alias}", ap_power_restart: "restart account {n} on {alias}",
  rq_proxy: "Credentials for proxy “{name}”", rq_proxy_new: "Credentials for a new proxy", rq_vps: "Register your VPS", rq_confirm: "The agent asks for confirmation",
  rq_say: "The agent says:", rq_later: "Later", rq_cancel: "Cancel", rq_deny: "Reject", rq_accept: "Accept", rq_allow: "Allow", rq_save: "Save securely", rq_fields: "Type details", rq_url: "Paste socks5://… URL",
  rq_secure: "They are stored only on your computer, in the .env file. The agent never sees the password: it goes straight to the dashboard.",
  rq_pass_secure: "The password is used once and not stored. The agent doesn't see it.",
  rq_vps_secure: "Stored on your computer (hosts.conf). Use the IP your provider gave you.",
  ap_q_prepare: "Allow the agent to prepare the VPS?", ap_q_deploy: "Allow the agent to deploy the proxies?", ap_q_power: "Allow the agent to change an account?",
  ap_mod: "This modifies server {ip}.", ap_will: "This will happen:",
  ap_p1: "Install Docker and Tailscale", ap_p2: "Enable the firewall (only SSH open) and fail2ban", ap_p3: "Create user “wa” with the dashboard's SSH key", ap_p_info: "Takes a few minutes. At the end you'll authorize the VPS in Tailscale with a button.",
  ap_d1: "Upload your proxies and configuration to the VPS", ap_d2: "Start one gateway per account", ap_d3: "Check each account's exit IP",
  ap_w1: "{do_} account {n} on {alias}. Other accounts' ports don't change.",
  confirm_quit: "Close the dashboard? Your proxies and VPS keep running.", confirm_del: "Remove this VPS from the list? (Does not stop anything on the server.)",
  confirm_rm: "Remove this account? Other accounts' ports do NOT change.", closed: "Dashboard closed. You can close this tab.", err: "Error"
}};
let lang = localStorage.getItem("lang") || ((navigator.language || "es").slice(0, 2) === "en" ? "en" : "es");
const t = (k, p) => {
  let s = I18N[lang] && I18N[lang][k] != null ? I18N[lang][k] : I18N.es[k] != null ? I18N.es[k] : k;
  for (const [a, b] of Object.entries(p || {})) s = s.split("{" + a + "}").join(b == null ? "" : String(b));
  return s;
};

const q = new URLSearchParams(location.search);
if (q.get("t")) { sessionStorage.setItem("tok", q.get("t")); history.replaceState(null, "", location.pathname); }
const TOK = sessionStorage.getItem("tok") || "";

// ---------------------------------------------------------------- estado
let S = {accounts: [], vps: [], tools: {}, ssh_key: false, last_verify: null, version: 0};
let tab = localStorage.getItem("tab") || "sum";
let draft = [], dirty = false;
let status = {}, statusLoading = {};
let feed = {since: 0, events: [], reqs: [], agent: {ago: null, working: ""}, job: null};
let cons = {job: null, lines: [], status: "", kind: "", alias: ""};
let dismissed = new Set(), modalReq = null, connLost = false;
const NS = "http://www.w3.org/2000/svg";

// ---------------------------------------------------------------- utilidades DOM
function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v === true) e.setAttribute(k, "");
    else if (v !== false && v != null) e.setAttribute(k, v);
  }
  for (const c of kids.flat(Infinity)) if (c != null && c !== false && c !== "") e.append(c.nodeType ? c : document.createTextNode(String(c)));
  return e;
}
function ic(name, cls) {
  const s = document.createElementNS(NS, "svg");
  s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("fill", "none"); s.setAttribute("stroke", "currentColor");
  s.setAttribute("stroke-width", "2"); s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round");
  s.setAttribute("aria-hidden", "true"); s.setAttribute("class", "svg-i" + (cls ? " " + cls : ""));
  const src = (window.ICONS || {})[name];
  if (src) {
    const d = new DOMParser().parseFromString('<svg xmlns="' + NS + '">' + src + "</svg>", "image/svg+xml");
    for (const k of Array.from(d.documentElement.childNodes)) s.append(document.importNode(k, true));
  }
  return s;
}
const $ = id => document.getElementById(id);
const put = (el, ...kids) => el.replaceChildren(...kids.flat(Infinity).filter(k => k != null && k !== false && k !== ""));
const chip = (kind, ...kids) => h("span", {class: "chip c-" + kind}, ...kids);
const dotc = (kind, text) => chip(kind, h("i", {class: "d"}), text);
function toast(text) { const e = $("toast"); e.textContent = text; e.classList.add("on"); clearTimeout(toast.t); toast.t = setTimeout(() => e.classList.remove("on"), 2200); }
function msg(box, text, kind) { put(box, text ? h("div", {class: "msg " + kind}, text) : ""); }
async function copy(text, btn) {
  try { await navigator.clipboard.writeText(text); } catch (e) {
    const ta = h("textarea"); ta.value = text; document.body.append(ta); ta.select(); document.execCommand("copy"); ta.remove();
  }
  const old = btn.textContent; btn.textContent = t("copied"); setTimeout(() => btn.textContent = old, 1200);
}
function ago(ts) {
  if (!ts) return "—";
  const m = Math.floor((Date.now() / 1000 - ts) / 60);
  return m < 1 ? t("ago_now") : m < 60 ? t("ago_min", {n: m}) : m < 1440 ? t("ago_h", {n: Math.floor(m / 60)}) : t("ago_d", {n: Math.floor(m / 1440)});
}
const hhmm = ts => new Date(ts * 1000).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit", second: "2-digit"});

async function api(path, body) {
  let r;
  try {
    r = await fetch(path, {method: body === undefined ? "GET" : "POST", headers: {"X-Token": TOK, "Content-Type": "application/json"}, body: body === undefined ? undefined : JSON.stringify(body)});
  } catch (e) { if (!connLost) { connLost = true; renderTop(); } throw e; }
  if (connLost) { connLost = false; renderTop(); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || (t("err") + " " + r.status));
  return j;
}
async function waitJob(id) {
  for (;;) {
    await new Promise(r => setTimeout(r, 1000));
    const j = await api("/api/jobs/" + id);
    if (j.status !== "running") return j;
  }
}

// ---------------------------------------------------------------- datos derivados
const accOk = a => a.exit_ip && a.targets.every(x => x.ok) && !a.partial && !a.inconsistent_ip;
const verified = () => S.last_verify ? S.last_verify.result : null;
const verifiedOk = r => !!r && r.accounts.every(accOk) && !r.duplicate_ips;
const jobRunning = kind => feed.job && feed.job.status === "running" && (!kind || feed.job.kind === kind);
const stList = () => S.vps.map(v => status[v.alias]).filter(Boolean);
const runningCount = () => stList().reduce((n, s) => n + s.accounts.filter(a => a.state === "running").length, 0);
const accLabel = n => { const a = S.accounts.find(x => x.n === n); return a && a.label ? a.label : ""; };
const kindName = k => t("k_" + k);
function describe(p) {
  if (p.action === "prepare") return t("ap_prepare", p);
  if (p.action === "deploy") return t("ap_deploy", p);
  return t("ap_power_" + p.do, p);
}

// ---------------------------------------------------------------- barra superior, aviso, pestañas
function renderTop() {
  const a = feed.agent, on = a.ago != null && a.ago < 600;
  document.documentElement.lang = lang; document.title = t("title");
  put($("top"),
    h("div", {class: "brand"}, h("span", {class: "logo"}, ic("diamond")), t("title")),
    h("span", {class: "sp"}),
    connLost ? h("span", {class: "pill"}, ic("triangle-alert"), t("w_conn")) :
    h("span", {class: "pill" + (on ? " on" : ""), title: on ? "" : t("ag_hint")}, h("span", {class: "dot"}), on ? [t("ag_on"), " · ", h("i", {}, a.working || t("ag_idle"))] : t("ag_none")),
    h("button", {class: "btn sm", title: t("lang"), onclick: () => { lang = lang === "es" ? "en" : "es"; localStorage.setItem("lang", lang); renderAll(); }}, ic("languages"), lang.toUpperCase()),
    h("button", {class: "btn sm", title: t("theme"), onclick: () => { document.documentElement.classList.toggle("dark"); localStorage.setItem("theme", document.documentElement.classList.contains("dark") ? "dark" : "light"); renderTop(); }}, ic(document.documentElement.classList.contains("dark") ? "sun" : "moon")),
    h("button", {class: "btn sm dan", onclick: quit}, ic("power"), h("span", {class: "lbl"}, t("quit"))));
}
async function quit() {
  if (!confirm(t("confirm_quit"))) return;
  try { await api("/api/quit", {}); } catch (e) {}
  document.body.replaceChildren(h("p", {class: "card"}, t("closed")));
}
function reqTitle(r) {
  const p = r.params;
  if (r.kind === "proxy") { const nm = p.label || (p.n ? accLabel(p.n) || ("#" + p.n) : ""); return nm ? t("rq_proxy", {name: nm}) : t("rq_proxy_new"); }
  if (r.kind === "vps") return t("rq_vps");
  if (r.kind === "confirm") return t("rq_confirm");
  return t("ap_q_" + p.action);
}
function renderAlert() {
  const rs = feed.reqs;
  put($("alert"), rs.length ? h("div", {class: "alert"}, ic("bell"), h("span", {class: "t"}, h("b", {}, t("al_title")), " ", reqTitle(rs[0]), rs.length > 1 ? " (+" + (rs.length - 1) + ")" : ""),
    h("button", {class: "btn sm pri", onclick: () => { dismissed.delete(rs[0].id); renderModal(true); }}, t("al_btn"))) : "");
}
function renderTabs() {
  const names = [["sum", "tab_sum"], ["prx", "tab_prx"], ["vps", "tab_vps"], ["acc", "tab_acc"], ["ios", "tab_ios"]];
  put($("tabs"), names.map(([k, l]) => h("button", {class: "tab" + (tab === k ? " act" : ""), role: "tab", "aria-selected": tab === k ? "true" : "false", onclick: () => setTab(k)}, t(l))));
}
function setTab(k) { tab = k; localStorage.setItem("tab", k); renderTabs(); renderMain(); }

// ---------------------------------------------------------------- pestaña Resumen
function nextStep() {
  if (feed.reqs.length) return {k: "nx_req", ic: "bell", act: () => { dismissed.delete(feed.reqs[0].id); renderModal(true); }, lbl: t("al_btn")};
  if (!S.accounts.length) return {k: "nx_acc", ic: "key-round", tab: "prx"};
  const v = verified();
  if (!v) return {k: "nx_test", ic: "shield-check", tab: "prx"};
  if (!verifiedOk(v)) return {k: "nx_fix", ic: "triangle-alert", tab: "prx", bad: true};
  if (!S.vps.length) return {k: "nx_vps", ic: "server", tab: "vps"};
  if (jobRunning()) return {k: "nx_job", ic: "terminal"};
  const sts = S.vps.map(x => status[x.alias]);
  if (sts.some(s => !s)) return {k: "nx_wait", ic: "refresh-cw"};
  if (sts.every(s => !s.prepared)) return {k: "nx_prep", ic: "package", tab: "vps"};
  if (sts.some(s => s.prepared && !s.accounts.length)) return {k: "nx_dep", ic: "rocket", tab: "vps"};
  return {k: "nx_done", ic: "smartphone", tab: "ios"};
}
function renderSummary(box) {
  const v = verified(), nOk = v ? v.accounts.filter(accOk).length : 0, sts = stList();
  const prepared = sts.filter(s => s.prepared).length, run = runningCount(), total = S.accounts.length;
  const deploying = jobRunning("deploy");
  const kpi = (l, val, small, chipEl) => h("div", {class: "kpi"}, h("div", {class: "l"}, l), h("div", {class: "v"}, val, small ? h("small", {}, " / " + small) : ""), chipEl || "");
  const ns = nextStep();
  const steps = [
    {n: 1, name: t("s_prx"), done: verifiedOk(v), desc: verifiedOk(v) ? t("s_prx_d", {n: nOk}) : t("s_prx_t")},
    {n: 2, name: t("s_vps"), done: S.vps.length > 0 && prepared === S.vps.length, desc: prepared ? t("s_vps_d") : t("s_vps_t")},
    {n: 3, name: t("s_dep"), done: total > 0 && run >= total, desc: run ? t("s_dep_d", {n: run}) : t("s_dep_t"), running: deploying},
    {n: 4, name: t("s_ios"), done: false, desc: t("s_ios_t")}];
  const cur = steps.findIndex(s => !s.done);
  put(box,
    h("div", {class: "kpis"},
      kpi(t("k_prx"), v ? nOk : "—", v ? v.accounts.length : "", !v ? chip("mu", t("k_untested")) : verifiedOk(v) ? chip("ok", ic("check"), t("k_allok")) : chip("er", t("k_bad"))),
      kpi(t("k_vps"), S.vps.length ? prepared : "—", S.vps.length || "", S.vps.length ? chip(prepared === S.vps.length ? "ok" : "wa", prepared === S.vps.length ? t("prepared") : t("no_prep")) : chip("mu", t("k_none"))),
      kpi(t("k_run"), sts.length ? run : "—", total || "", deploying ? chip("wa", t("s_run")) : sts.length ? chip(run >= total && total ? "ok" : "mu", run >= total && total ? t("k_allok") : t("st_none")) : chip("mu", t("k_none"))),
      h("div", {class: "kpi"}, h("div", {class: "l"}, t("k_last")), h("div", {class: "v s"}, v ? ago(S.last_verify.ts) : "—"), v && !v.duplicate_ips ? chip("mu", t("k_dis"), " ", ic("check")) : "")),
    h("div", {class: "next" + (ns.bad ? " bad" : "")}, h("span", {class: "nic"}, ic(ns.ic)),
      h("div", {class: "t"}, h("b", {}, t(ns.k)), t(ns.k + "_d") ? h("span", {class: "sub t0"}, t(ns.k + "_d")) : ""),
      ns.tab || ns.act ? h("button", {class: "btn pri", onclick: ns.act || (() => setTab(ns.tab))}, ns.lbl || t("go")) : ""),
    h("div", {class: "card"}, h("h2", {}, t("st_steps")), h("p", {class: "sub"}, t("st_stepsd")),
      h("div", {class: "steps"}, steps.map((s, i) => {
        const bar = s.running ? h("div", {class: "pbar run"}, h("i")) : null;
        return h("div", {class: "step" + (s.done ? " done" : i === cur ? " cur" : "")}, h("div", {class: "n"}, s.done ? ic("check") : String(s.n)), h("b", {}, s.name), h("small", {}, s.running ? t("s_run") : s.desc), bar);
      }))),
    accountsCard(false));
}

function accountsCard(withPower) {
  const rows = [];
  S.accounts.forEach(a => {
    let found = false;
    S.vps.forEach(v => {
      const st = status[v.alias]; const x = st && st.accounts.find(c => c.n === a.n);
      if (x) { found = true; rows.push(accRow(a, v, x, withPower)); }
    });
    if (!found) rows.push(accRow(a, null, null, withPower));
  });
  return h("div", {class: "card"}, h("h2", {}, t("accounts")), h("p", {class: "sub"}, t("accounts_d")),
    rows.length ? h("div", {class: "tablewrap"}, h("table", {}, h("tr", {}, h("th", {}, t("acc")), h("th", {}, t("state")), h("th", {}, t("exit_ip")), h("th", {}, t("ports")), withPower ? h("th") : ""), rows)) : h("p", {class: "sub"}, t("no_accounts")));
}
function accRow(a, v, x, withPower) {
  const up = x && x.state === "running";
  const stc = !x ? chip("mu", t("st_none")) : up ? dotc("ok", t("st_up")) : x.state === "exited" ? dotc("mu", t("st_down")) : dotc("wa", t("st_other") + ": " + x.state);
  const pw = act => h("button", {class: "btn sm", onclick: async e => {
    if (act !== "start" && !confirm(t("ap_w1", {do_: t(act), n: a.n, alias: v.alias}))) return;
    e.target.disabled = true;
    try { const {job} = await api("/api/power", {alias: v.alias, n: a.n, do: act}); await waitJob(job); } catch (er) { alert(er.message); }
    refresh(v.alias);
  }}, t(act));
  return h("tr", {}, h("td", {}, h("b", {}, a.label || (t("acc") + " " + a.n)), h("span", {class: "tag"}, a.n), S.vps.length > 1 && v ? h("span", {class: "tag"}, v.alias) : ""),
    h("td", {}, stc), h("td", {class: "mono"}, (x && x.exit_ip) || "—"), h("td", {class: "mono"}, (5100 + a.n) + " · " + (5200 + a.n)),
    withPower ? h("td", {}, v && x ? (up ? [pw("restart"), " ", pw("stop")] : pw("start")) : "") : "");
}

// ---------------------------------------------------------------- pestaña Proxies
function renderProxies(box) {
  const out = h("div"), note = h("div");
  const list = h("div");
  if (!draft.length) list.append(h("p", {class: "sub"}, t("no_accounts")));
  draft.forEach((a, i) => {
    const inp = (key, label, type, ph, extra) => h("div", {}, h("label", {}, label),
      h("input", Object.assign({type: type || "text", value: a[key] ?? "", placeholder: ph || "", autocomplete: "off", spellcheck: "false", oninput: e => { a[key] = e.target.value; dirty = true; }}, extra || {})));
    list.append(h("div", {class: "acc"}, h("b", {}, t("acc") + " " + (a.n || "")),
      h("div", {class: "row"}, inp("label", t("name"), "text", t("name_ph")), inp("host", t("server"), "text", "isp.ejemplo.com"), inp("port", t("port"), "number", "10001", {min: 1, max: 65535})),
      h("div", {class: "row"}, inp("user", t("user")), inp("password", t("pass"), "password", a.has_password ? t("pass_keep") : "", {autocomplete: "new-password"})),
      h("button", {class: "btn sm dan", onclick: () => { if (confirm(t("confirm_rm"))) { draft.splice(i, 1); dirty = true; renderMain(); } }}, ic("trash"), t("remove"))));
  });
  const pasteIn = h("input", {type: "text", placeholder: t("paste_ph"), autocomplete: "off", spellcheck: "false"}), pasteMsg = h("div");
  const fill = () => {
    try {
      const u = new URL(pasteIn.value.trim());
      if (!/^socks5h?:$/.test(u.protocol) || !u.hostname) throw 0;
      draft.push({n: null, label: "", host: u.hostname, port: u.port, user: decodeURIComponent(u.username), password: decodeURIComponent(u.password), has_password: false});
      dirty = true; renderMain();
    } catch (e) { msg(pasteMsg, t("paste_bad"), "er"); }
  };
  const saveBtn = h("button", {class: "btn pri", onclick: async () => { try { await save(); toast(t("saved")); } catch (e) { msg(note, e.message, "er"); } }}, t("save"));
  const testing = jobRunning("verify");
  const testBtn = h("button", {class: "btn", disabled: testing, onclick: async () => {
    try {
      if (dirty) await save();
      msg(note, "", ""); const {job} = await api("/api/verify", {}); await waitJob(job); await refreshState();
    } catch (e) { msg(note, e.message, "er"); }
  }}, ic("shield-check"), testing ? t("testing") : t("test"));
  put(box, h("div", {class: "card"}, h("h2", {}, t("p_title")), h("p", {class: "sub"}, t("p_d")), list,
    h("div", {class: "btns"}, h("button", {class: "btn", onclick: () => { draft.push({n: null, label: "", host: "", port: "", user: "", password: "", has_password: false}); dirty = true; renderMain(); }}, ic("plus"), t("add")),
      h("details", {}, h("summary", {}, t("paste")), h("div", {class: "btns"}, pasteIn, h("button", {class: "btn", onclick: fill}, t("paste_btn"))), pasteMsg)),
    h("div", {class: "btns"}, saveBtn, testBtn, h("span", {class: "sub t0"}, t("test_note"))), note, out));
  renderResults(out, verified());
}
function renderResults(box, r) {
  if (!r) return put(box);
  const rows = r.accounts.map(a => {
    const okAll = accOk(a), nOk = (a.gateways || []).filter(g => g.ok).length;
    const gw = a.gateways && a.gateways.length ? h("div", {class: "msg " + (a.partial ? "er" : "wa")}, a.partial ? t("partial", {ok: nOk, n: a.gateways.length}) : (a.inconsistent_ip ? t("inconsistent") : ""),
      h("div", {class: "mono gw"}, a.gateways.map(g => h("div", {}, ic(g.ok ? "circle-check" : "circle-x"), " " + g.gateway + (g.exit_ip ? " → " + g.exit_ip : ""))))) : "";
    return h("tr", {}, h("td", {}, t("acc") + " " + a.n + (a.label ? " · " + a.label : "")), h("td", {class: "mono"}, a.exit_ip || "—"),
      h("td", {}, a.targets.map(x => h("span", {}, ic(x.ok ? "circle-check" : "circle-x"), " ", h("small", {}, x.target + "  "))), a.error && !okAll && !a.partial ? h("div", {class: "sub t0"}, a.error) : "", gw),
      h("td", {}, okAll ? chip("ok", "OK") : chip("er", "✗")));
  });
  const allOk = verifiedOk(r);
  put(box, h("div", {class: "tablewrap"}, h("table", {}, h("tr", {}, h("th", {}, t("acc")), h("th", {}, t("res_ip")), h("th", {}, "WhatsApp"), h("th")), rows)),
    r.duplicate_ips ? h("div", {class: "msg er"}, t("dup")) : "", h("div", {class: "msg " + (allOk ? "ok" : "er")}, allOk ? t("test_all_ok") : t("test_some_bad")));
}
async function save() {
  const r = await api("/api/accounts", {accounts: draft.map(a => ({n: a.n, label: a.label, host: a.host, port: a.port, user: a.user, password: a.password || ""}))});
  S.accounts = r.accounts; draft = S.accounts.map(a => ({...a, password: ""})); dirty = false; await refreshState(true);
}

// ---------------------------------------------------------------- pestaña VPS
function renderVps(box) {
  const ipIn = h("input", {type: "text", placeholder: "203.0.113.10", autocomplete: "off"}), nmIn = h("input", {type: "text", placeholder: "vps1", autocomplete: "off"}), note = h("div");
  const add = h("button", {class: "btn pri", onclick: async () => {
    try { const r = await api("/api/vps", {ip: ipIn.value.trim(), alias: nmIn.value.trim()}); S.vps = r.vps; renderAll(); refreshAll(); } catch (e) { msg(note, e.message, "er"); }
  }}, ic("plus"), t("vps_add"));
  const keyOut = h("div");
  const keyBtn = h("button", {class: "btn sm", onclick: async () => {
    const r = await api("/api/ssh-key", {}); const ta = h("textarea", {readonly: true, rows: 3, class: "mono"}); ta.value = r.public_key;
    put(keyOut, ta, h("button", {class: "btn sm", onclick: e => copy(r.public_key, e.currentTarget)}, ic("copy"), t("copy")));
  }}, ic("key-round"), t("key_show"));
  put(box, h("div", {class: "card"}, h("h2", {}, t("v_title")), h("p", {class: "sub"}, t("v_d")),
    S.vps.length ? S.vps.map(vpsCard) : h("p", {class: "sub"}, t("vps_none")),
    h("div", {class: "row"}, h("div", {}, h("label", {}, t("vps_ip")), ipIn), h("div", {}, h("label", {}, t("vps_name")), nmIn), add), note,
    h("details", {}, h("summary", {}, t("key_title")), h("p", {class: "sub"}, t("key_help")), keyBtn, keyOut)));
}
function vpsCard(v) {
  const st = status[v.alias];
  const userIn = h("input", {type: "text", value: "root", autocomplete: "off"}), passIn = h("input", {type: "password", autocomplete: "new-password", placeholder: "••••••"});
  const note = h("div");
  const prepBtn = h("button", {class: "btn pri", disabled: jobRunning("prepare")}, ic("package"), t("prep_go"));
  const depBtn = h("button", {class: "btn pri", disabled: jobRunning("deploy")}, ic("rocket"), t("deploy"));
  const guard = async (btn, path, body) => {
    btn.disabled = true; msg(note, "", "");
    try { const {job} = await api(path, body); await waitJob(job); await refresh(v.alias); } catch (e) { msg(note, e.message, "er"); }
    btn.disabled = false;
  };
  prepBtn.onclick = () => guard(prepBtn, "/api/prepare", {alias: v.alias, initial_user: userIn.value.trim(), password: passIn.value}).then(() => { passIn.value = ""; });
  depBtn.onclick = async () => { if (dirty) { try { await save(); } catch (e) { return msg(note, e.message, "er"); } } guard(depBtn, "/api/deploy", {alias: v.alias}); };
  const state = !st ? chip("mu", t("loading")) : !st.reachable ? dotc("er", t("no_conn")) : !st.prepared ? dotc("wa", t("no_prep")) : st.accounts.length ? dotc("ok", t("st_up")) : dotc("wa", t("not_deployed"));
  return h("div", {class: "vps"},
    h("div", {class: "kv"}, h("span", {}, h("b", {}, v.alias), " · ", h("span", {class: "mono"}, v.ip), st && st.tailscale_ip ? [" · Tailscale ", h("span", {class: "mono"}, st.tailscale_ip)] : ""),
      h("span", {}, state, " ", h("button", {class: "btn sm", title: t("refresh"), onclick: () => refresh(v.alias)}, ic("refresh-cw")), " ",
        h("button", {class: "btn sm dan", title: t("vps_del"), onclick: async () => { if (confirm(t("confirm_del"))) { S.vps = (await api("/api/vps/delete", {alias: v.alias})).vps; delete status[v.alias]; renderAll(); } }}, ic("trash")))),
    st && st.msg_key ? h("div", {class: "msg wa"}, t("m_" + st.msg_key)) : st && st.message ? h("div", {class: "msg wa"}, st.message) : "",
    h("details", {open: !!st && (!st.reachable || !st.prepared)}, h("summary", {}, t("prep")), h("p", {class: "sub"}, t("prep_help")),
      h("div", {class: "row"}, h("div", {}, h("label", {}, t("prep_user")), userIn), h("div", {}, h("label", {}, t("prep_pass")), passIn), prepBtn), h("p", {class: "sub"}, t("prep_pass_h"))),
    h("div", {class: "btns"}, depBtn, h("span", {class: "sub t0"}, t("deploy_help"))), note);
}

// ---------------------------------------------------------------- pestaña iPhone
function renderIos(box) {
  const cards = [];
  S.vps.forEach(v => {
    const st = status[v.alias];
    if (!st || !st.tailscale_ip || !st.accounts.length) return;
    st.accounts.forEach(a => {
      const kv = (k, val, cp) => h("div", {class: "kv"}, h("span", {}, k), h("span", {class: "v"}, val), cp ? h("button", {class: "btn sm", onclick: e => copy(String(val), e.currentTarget)}, ic("copy"), t("copy")) : h("span"));
      cards.push(h("div", {class: "vps"}, h("b", {}, t("acc") + " " + a.n + (accLabel(a.n) ? " · " + accLabel(a.n) : "") + (S.vps.length > 1 ? "  (" + v.alias + ")" : "")),
        kv(t("f_addr"), st.tailscale_ip, true), kv(t("f_chat"), 5100 + a.n, true), kv(t("f_media"), 5200 + a.n, true), kv(t("f_tls"), t("tls_off"), false)));
    });
  });
  put(box, h("div", {class: "card"}, h("h2", {}, t("i_title")), h("p", {class: "sub"}, t("i_d")), cards.length ? cards : h("p", {class: "sub"}, t("i_none")),
    h("div", {class: "msg wa"}, t("i_warn"))));
}

function renderMain() {
  const box = $("main");
  const miss = Object.entries(S.tools || {}).filter(([, v]) => !v).map(([k]) => k);
  const body = h("div");
  if (tab === "sum") renderSummary(body);
  else if (tab === "prx") renderProxies(body);
  else if (tab === "vps") renderVps(body);
  else if (tab === "acc") put(body, accountsCard(true), S.vps.length ? "" : h("p", {class: "sub"}, t("vps_none")));
  else renderIos(body);
  put(box, miss.length ? h("div", {class: "msg er"}, t("w_tools") + miss.join(", ")) : "", body);
}

// ---------------------------------------------------------------- columna de actividad
function evText(e) {
  if (e.text) return e.text;
  const p = e.params || {};
  const kind = p.kind ? kindName(p.kind) : "", alias = p.alias ? " · " + p.alias : "";
  if (e.key === "e_approved" || e.key === "approved") return t("e_approved", {desc: describe(p)});
  if (e.key === "req_approve") return t("e_req_approve", {desc: describe(p)});
  const key = "e_" + e.key.replace(/^req_(proxy|vps|confirm)$/, "req_$1");
  return t(key, {kind, alias, n: p.n, ip: p.ip});
}
function evIcon(e) {
  if (e.level === "req") return "bell";
  if (e.level === "ok") return "circle-check";
  if (e.level === "er") return "circle-x";
  return e.who === "agent" ? "bot" : e.who === "user" ? "user" : "settings";
}
function renderFeed() {
  const evs = feed.events.slice(-60).reverse();
  const tailscale = (cons.lines.join("\n").match(/https:\/\/login\.tailscale\.com\/a\/\w+/) || [])[0];
  const pre = h("pre", {class: "cons", id: "consolebox"}, cons.lines.length ? cons.lines.join("\n") : t("cons_none"));
  put($("feed"),
    h("div", {class: "card"}, h("div", {class: "fh"}, h("b", {}, t("act")), h("span", {class: "pill on"}, h("span", {class: "dot"}), t("live"))),
      h("div", {class: "evs"}, evs.length ? evs.map(e => h("div", {class: "ev " + (e.level === "req" || e.level === "ok" || e.level === "er" ? e.level : "")},
        h("div", {class: "i"}, ic(evIcon(e))), h("div", {class: "tx"}, h("div", {}, evText(e)), h("div", {class: "tm"}, hhmm(e.ts))))) : h("div", {class: "ev-empty"}, t("ev_none")))),
    h("div", {class: "card"}, h("div", {class: "fh"}, h("b", {}, t("console")), cons.kind ? chip(cons.status === "ok" ? "ok" : cons.status === "fail" ? "er" : "mu", kindName(cons.kind) + (cons.alias ? " · " + cons.alias : "")) : ""),
      tailscale && cons.status === "running" ? h("div", {class: "tsbox"}, h("div", {class: "msg wa"}, h("b", {}, t("ts_auth")), h("div", {}, t("ts_help")),
        h("div", {class: "btns"}, h("a", {class: "btn pri", href: tailscale, target: "_blank", rel: "noopener noreferrer"}, ic("external-link"), t("ts_open"))))) : "", pre));
  const c = $("consolebox"); if (c) c.scrollTop = c.scrollHeight;
}

// ---------------------------------------------------------------- ventana de solicitudes del agente
function renderModal(force) {
  const pend = feed.reqs.filter(r => !dismissed.has(r.id));
  const r = pend[0];
  if (!r) { if (modalReq) { modalReq = null; put($("modal")); } return; }
  if (modalReq === r.id && !force) return;
  modalReq = r.id;
  put($("modal"), modalFor(r));
  const f = $("modal").querySelector("input"); if (f) f.focus();
}
function modalFor(r) {
  const p = r.params, err = h("div");
  const later = () => { dismissed.add(r.id); modalReq = null; put($("modal")); renderAlert(); };
  const answer = async (decision, body) => {
    try { await api("/api/requests/" + r.id + "/answer", Object.assign({decision}, body || {})); modalReq = null; put($("modal")); await tickOnce(); } catch (e) { msg(err, e.message, "er"); }
  };
  const says = p.message ? h("div", {class: "sub t0"}, t("rq_say"), " ", h("span", {class: "say"}, p.message)) : "";
  const shell = (icon, wa, title, sub, body, foot) => h("div", {class: "ov"}, h("div", {class: "modal", role: "dialog", "aria-modal": "true"},
    h("div", {class: "mh"}, h("div", {class: "av" + (wa ? " wa" : "")}, ic(icon)), h("div", {}, h("b", {}, title), sub)),
    h("div", {class: "mb"}, body, err), h("div", {class: "mf"}, foot)));
  if (r.kind === "proxy") {
    const cur = p.n ? S.accounts.find(a => a.n === p.n) : null;
    const f = {label: p.label || (cur && cur.label) || "", host: cur ? cur.host : "", port: cur ? cur.port : "", user: cur ? cur.user : "", password: ""};
    let mode = "fields"; const body = h("div");
    const draw = () => {
      const inp = (k, lbl, type, ph) => h("div", {}, h("label", {}, lbl), h("input", {type: type || "text", value: f[k], placeholder: ph || "", autocomplete: "off", spellcheck: "false", oninput: e => { f[k] = e.target.value; }}));
      const urlIn = h("input", {type: "text", placeholder: t("paste_ph"), autocomplete: "off", spellcheck: "false", onchange: e => {
        try { const u = new URL(e.target.value.trim()); f.host = u.hostname; f.port = u.port; f.user = decodeURIComponent(u.username); f.password = decodeURIComponent(u.password); mode = "fields"; draw(); } catch (x) { msg(err, t("paste_bad"), "er"); }
      }});
      put(body, h("div", {class: "seg"}, h("button", {class: mode === "fields" ? "a" : "", onclick: () => { mode = "fields"; draw(); }}, t("rq_fields")), h("button", {class: mode === "url" ? "a" : "", onclick: () => { mode = "url"; draw(); }}, t("rq_url"))),
        mode === "url" ? h("div", {class: "g1"}, urlIn) : [
          h("div", {class: "g2"}, inp("host", t("server"), "text", "isp.ejemplo.com"), inp("port", t("port"), "number", "10001")),
          h("div", {class: "g2e"}, inp("user", t("user")), inp("password", t("pass"), "password", cur && cur.has_password ? t("pass_keep") : "")),
          h("div", {class: "g1"}, inp("label", t("name"), "text", t("name_ph")))],
        h("div", {class: "sec"}, ic("lock"), h("span", {}, t("rq_secure"))));
    };
    draw();
    return shell("key-round", false, reqTitle(r), says, body, [
      h("button", {class: "btn", onclick: later}, t("rq_later")), h("button", {class: "btn dan", onclick: () => answer("deny")}, t("rq_cancel")),
      h("button", {class: "btn pri", onclick: () => answer("submit", {n: p.n, label: f.label, host: f.host, port: f.port, user: f.user, password: f.password})}, t("rq_save"))]);
  }
  if (r.kind === "vps") {
    const f = {ip: "", alias: ""};
    const inp = (k, lbl, ph) => h("div", {}, h("label", {}, lbl), h("input", {type: "text", placeholder: ph, autocomplete: "off", oninput: e => { f[k] = e.target.value; }}));
    return shell("server", false, t("rq_vps"), says, [h("div", {class: "g2e"}, inp("ip", t("vps_ip"), "203.0.113.10"), inp("alias", t("vps_name"), "vps1")), h("div", {class: "sec"}, ic("lock"), h("span", {}, t("rq_vps_secure")))], [
      h("button", {class: "btn", onclick: later}, t("rq_later")), h("button", {class: "btn dan", onclick: () => answer("deny")}, t("rq_cancel")),
      h("button", {class: "btn pri", onclick: () => answer("submit", {ip: f.ip.trim(), alias: f.alias.trim()})}, t("vps_add"))]);
  }
  if (r.kind === "confirm") {
    return shell("info", true, t("rq_confirm"), "", h("div", {class: "say"}, p.message), [
      h("button", {class: "btn", onclick: later}, t("rq_later")), h("button", {class: "btn dan", onclick: () => answer("deny")}, t("rq_deny")),
      h("button", {class: "btn pri", onclick: () => answer("submit")}, t("rq_accept"))]);
  }
  // aprobación de una acción
  const f = {initial_user: "root", password: ""};
  let body;
  if (p.action === "prepare") {
    body = [h("div", {}, t("ap_will")), h("div", {class: "list"}, h("div", {}, ic("package"), t("ap_p1")), h("div", {}, ic("flame"), t("ap_p2")), h("div", {}, ic("user-plus"), t("ap_p3"))),
      h("div", {class: "g2e"}, h("div", {}, h("label", {}, t("prep_user")), h("input", {type: "text", value: "root", autocomplete: "off", oninput: e => { f.initial_user = e.target.value; }})),
        h("div", {}, h("label", {}, t("prep_pass")), h("input", {type: "password", autocomplete: "new-password", oninput: e => { f.password = e.target.value; }}))),
      h("div", {class: "sec"}, ic("info"), h("span", {}, t("ap_p_info") + " " + t("rq_pass_secure")))];
  } else if (p.action === "deploy") {
    body = [h("div", {}, t("ap_will")), h("div", {class: "list"}, h("div", {}, ic("package"), t("ap_d1")), h("div", {}, ic("rocket"), t("ap_d2")), h("div", {}, ic("shield-check"), t("ap_d3")))];
  } else {
    body = h("div", {}, t("ap_w1", {do_: t(p.do), n: p.n, alias: p.alias}));
  }
  return shell("triangle-alert", true, t("ap_q_" + p.action), h("div", {class: "sub t0"}, t("ap_mod", {ip: p.ip || p.alias})), [says, body], [
    h("button", {class: "btn", onclick: later}, t("rq_later")), h("button", {class: "btn dan", onclick: () => answer("deny")}, t("rq_deny")),
    h("button", {class: "btn pri", onclick: () => answer("submit", p.action === "prepare" ? {initial_user: f.initial_user.trim(), password: f.password} : {})}, t("rq_allow"))]);
}

// ---------------------------------------------------------------- bucle de actualización
async function refreshState(force) {
  const prevVer = S.version;
  const s = await api("/api/state");
  S = s;
  if (!dirty) draft = S.accounts.map(a => ({...a, password: ""}));
  if (S.version !== prevVer || force) renderMain();
}
async function refresh(alias) {
  statusLoading[alias] = true;
  try { status[alias] = await api("/api/status", {alias}); }
  catch (e) { status[alias] = {alias, reachable: false, prepared: false, accounts: [], message: e.message}; }
  statusLoading[alias] = false; renderMain();
}
function refreshAll() { S.vps.forEach(v => refresh(v.alias)); }

async function tickOnce() {
  const f = await api("/api/feed?since=" + feed.since);
  feed.agent = f.agent; feed.reqs = f.requests;
  const prevJob = feed.job; feed.job = f.job;
  for (const e of f.events) { feed.events.push(e); feed.since = Math.max(feed.since, e.id); }
  if (feed.events.length > 200) feed.events.splice(0, feed.events.length - 200);
  if (f.job && cons.job !== f.job.id) cons = {job: f.job.id, lines: [], status: "", kind: f.job.kind, alias: f.job.alias, since: 0};
  let consChanged = false, finished = false;
  if (cons.job && (cons.status === "running" || cons.status === "" || (f.job && f.job.id === cons.job && f.job.status !== cons.status))) {
    const j = await api("/api/jobs/" + cons.job + "?since=" + (cons.since || 0));
    if (j.lines.length) { cons.lines.push(...j.lines); cons.since = j.next; consChanged = true; }
    if (cons.status !== j.status) { consChanged = true; if (cons.status === "running" && j.status !== "running") finished = true; cons.status = j.status; }
  }
  if (f.version !== S.version) await refreshState();
  renderTop(); renderAlert(); renderFeed(); renderModal();
  if (finished || (prevJob && prevJob.status !== (f.job || {}).status)) { renderMain(); if (finished && cons.kind !== "verify") refreshAll(); }
}
async function loop() {
  try { await tickOnce(); } catch (e) { /* api() ya marca connLost */ }
  setTimeout(loop, 1500);
}

(async function init() {
  if (localStorage.getItem("theme") === "dark" || (!localStorage.getItem("theme") && matchMedia("(prefers-color-scheme: dark)").matches)) document.documentElement.classList.add("dark");
  try { await refreshState(true); } catch (e) { renderTop(); put($("main"), h("div", {class: "card"}, t("w_conn"))); return; }
  renderAll(); refreshAll(); loop();
})();
function renderAll() { renderTop(); renderAlert(); renderTabs(); renderMain(); renderFeed(); }
