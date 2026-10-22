#!/usr/bin/env python3
"""SOCKS5 mínimo con usuario/clave, solo para PRUEBAS locales (no es un proxy real).
Uso: fake_socks5.py PUERTO USUARIO CLAVE [IP_DONDE_ESCUCHAR]
Acepta CONNECT por nombre de dominio (como un proxy real con socks5h://)."""
import socket, struct, sys, threading

port, user, pw = int(sys.argv[1]), sys.argv[2].encode(), sys.argv[3].encode()

def pipe(a, b):
    try:
        while (d := a.recv(65536)):
            b.sendall(d)
    except OSError:
        pass
    finally:
        for s in (a, b):
            try: s.shutdown(socket.SHUT_RDWR)
            except OSError: pass

def rd(c, n):
    b = b""
    while len(b) < n:
        x = c.recv(n - len(b))
        if not x: raise OSError("eof")
        b += x
    return b

def handle(c):
    try:
        ver, n = rd(c, 2); rd(c, n)
        c.sendall(b"\x05\x02")
        rd(c, 1); u = rd(c, rd(c, 1)[0]); p = rd(c, rd(c, 1)[0])
        if (u, p) != (user, pw):
            c.sendall(b"\x01\x01"); return
        c.sendall(b"\x01\x00")
        _, cmd, _, atyp = rd(c, 4)
        if atyp == 3: host = rd(c, rd(c, 1)[0]).decode()
        elif atyp == 1: host = socket.inet_ntoa(rd(c, 4))
        else: return
        dport = struct.unpack(">H", rd(c, 2))[0]
        try:
            r = socket.create_connection((host, dport), timeout=10)
        except OSError:
            c.sendall(b"\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00"); return
        c.sendall(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
        threading.Thread(target=pipe, args=(c, r), daemon=True).start()
        pipe(r, c)
    except OSError:
        pass
    finally:
        c.close()

s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((sys.argv[4] if len(sys.argv) > 4 else "127.0.0.1", port)); s.listen(50)
while True:
    conn, _ = s.accept()
    threading.Thread(target=handle, args=(conn,), daemon=True).start()
