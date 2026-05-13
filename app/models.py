import os
import subprocess
import time

import httpx

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GGUF_FILE = os.path.join(PROJECT_DIR, "lfm2-1.2b-tool-q4_k_m.gguf")
LLAMA_SERVER_BIN = os.path.join(PROJECT_DIR, "llama-server")

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080


class LlamaServer:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
    ):
        self.host = host
        self.port = port
        self._process: subprocess.Popen | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def model_name(self) -> str:
        return "lfm2-1.2b-tool-q4_k_m.gguf"

    def start(self) -> None:
        if self._process and self._process.poll() is None:
            return

        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = PROJECT_DIR

        cmd = [
            LLAMA_SERVER_BIN,
            "-m", GGUF_FILE,
            "--host", self.host,
            "--port", str(self.port),
            "--temp", "0",
        ]
        self._process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._wait_until_ready(timeout=120)

    def stop(self) -> None:
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def is_ready(self) -> bool:
        try:
            resp = httpx.get(f"{self.base_url}/health", timeout=2)
            return resp.status_code == 200
        except httpx.ConnectError:
            return False

    def _wait_until_ready(self, timeout: int = 120) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.is_ready():
                return
            if self._process and self._process.poll() is not None:
                raise RuntimeError(
                    f"llama-server exited: {self._process.stderr.read().decode()}"
                )
            time.sleep(2)
        raise TimeoutError("llama-server did not become ready within timeout")

    async def chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 512,
    ) -> dict:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0,
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()


_server: LlamaServer | None = None


def get_server() -> LlamaServer:
    global _server
    if _server is None:
        _server = LlamaServer()
    return _server