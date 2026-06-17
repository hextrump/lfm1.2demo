#!/usr/bin/env python3
"""Minimal SSE server for the Live Tail Console.

Listens on 127.0.0.1:8765 and serves Server-Sent Events streaming
`tail -F /tmp/demo1_live_tail.log` (a unified event log written by the
Streamlit app — see app.py::append_live_event).

Why stdlib only:
- The demo's venv is uv-managed and has no pip; aiohttp would need a
  separate install. Python 3.12's asyncio + selectors is enough for a
  long-lived single-purpose SSE relay that just `tail -F`s a file.

Endpoints:
- GET /sse      → text/event-stream of new log lines
- GET /health   → "ok"
- GET /         → tiny HTML page with a self-test
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

DEFAULT_LOG = "/tmp/demo1_live_tail.log"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def _format_sse(line: str) -> bytes:
    # SSE protocol: each event is "data: <line>\n\n"
    return f"data: {line.rstrip()}\n\n".encode("utf-8")


async def _stream_tail(send, log_path: Path, stop_event: asyncio.Event) -> None:
    """Spawn `tail -F` on `log_path` and forward each line as an SSE event.

    `send` is an asyncio StreamWriter fed by the HTTP handler.
    """
    proc = await asyncio.create_subprocess_exec(
        "tail", "-F", "-n", "0", str(log_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        while not stop_event.is_set():
            line = await proc.stdout.readline()
            if not line:
                # tail exited (file was deleted/rotated). Exit and let the
                # client reconnect.
                break
            try:
                await send(_format_sse(line.decode("utf-8", errors="replace")))
            except (ConnectionResetError, BrokenPipeError):
                break
    finally:
        try:
            proc.terminate()
            await proc.wait()
        except ProcessLookupError:
            pass


async def _handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Minimal HTTP/1.1 handler that supports GET /sse and GET /health."""
    try:
        request_line = await asyncio.wait_for(reader.readline(), timeout=10)
    except asyncio.TimeoutError:
        writer.close()
        return
    if not request_line:
        writer.close()
        return
    try:
        method, path, _ = request_line.decode("latin-1").split(" ", 2)
    except ValueError:
        writer.close()
        return

    # Drain headers (we don't need them)
    while True:
        line = await reader.readline()
        if line in (b"\r\n", b"", b"\n"):
            break

    if method != "GET":
        writer.write(b"HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n")
        await writer.drain()
        writer.close()
        return

    if path.startswith("/health"):
        body = b"ok"
        writer.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"Access-Control-Allow-Origin: *\r\n\r\n" + body
        )
        await writer.drain()
        writer.close()
        return

    if path.startswith("/sse"):
        log_path_str = request_line.decode("latin-1").split()
        # Parse "log=<path>" from query string if present
        log_path = Path(DEFAULT_LOG)
        if "?" in path:
            from urllib.parse import parse_qs
            qs = parse_qs(path.split("?", 1)[1])
            if qs.get("log"):
                log_path = Path(qs["log"][0])

        writer.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/event-stream\r\n"
            b"Cache-Control: no-cache\r\n"
            b"Connection: keep-alive\r\n"
            b"X-Accel-Buffering: no\r\n"
            b"Access-Control-Allow-Origin: *\r\n\r\n"
        )
        await writer.drain()

        async def send(data: bytes) -> None:
            writer.write(data)
            await writer.drain()

        stop_event = asyncio.Event()
        try:
            # Send a hello so the client knows we're alive
            await send(b": connected\n\n")
            # Heartbeat every 15s to keep the connection alive
            async def heartbeat():
                while not stop_event.is_set():
                    await asyncio.sleep(15)
                    try:
                        await send(b": hb\n\n")
                    except (ConnectionResetError, BrokenPipeError):
                        stop_event.set()
                        return
            hb_task = asyncio.create_task(heartbeat())
            try:
                await _stream_tail(send, log_path, stop_event)
            finally:
                hb_task.cancel()
        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass
        return

    # Fallback
    body = b"Live Tail SSE server. Endpoints: /sse, /health"
    writer.write(
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/plain\r\n"
        b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
    )
    await writer.drain()
    writer.close()


async def main_async(host: str, port: int, log_path: Path) -> None:
    # Touch the file so `tail -F` doesn't error on first start
    log_path.touch(exist_ok=True)
    print(f"[live-tail] log: {log_path}")
    print(f"[live-tail] listening on http://{host}:{port}/sse")
    print(f"[live-tail] health: http://{host}:{port}/health")
    server = await asyncio.start_server(_handle_client, host, port)
    async with server:
        await server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--log", default=DEFAULT_LOG)
    args = parser.parse_args()
    try:
        asyncio.run(main_async(args.host, args.port, Path(args.log)))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
