import asyncio
import pathlib
import ssl
import typing
from dataclasses import dataclass
from tempfile import TemporaryDirectory

import pytest
import pytest_asyncio
import urllib3
from aiohttp import ClientSession, web

import truststore



MKCERT_CA_NOT_INSTALLED = b"local CA is not installed in the system trust store"
MKCERT_CA_ALREADY_INSTALLED = b"local CA is now installed in the system trust store"
SUBPROCESS_TIMEOUT = 5


@pytest_asyncio.fixture(scope="function")
async def mkcert() -> typing.AsyncIterator[None]:
    async def is_mkcert_available() -> bool:
        try:
            p = await asyncio.create_subprocess_exec(
                "mkcert",
                "-help",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except FileNotFoundError:
            return False
        await asyncio.wait_for(p.wait(), timeout=SUBPROCESS_TIMEOUT)
        return p.returncode == 0

    # Checks to see if mkcert is available at all.
    if not await is_mkcert_available():
        pytest.skip("Install mkcert to run custom CA tests")

    # Now we attempt to install the root certificate
    # to the system trust store. Keep track if we should
    # call mkcert -uninstall at the end.
    should_mkcert_uninstall = False
    try:
        p = await asyncio.create_subprocess_exec(
            "mkcert",
            "-install",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        await p.wait()
        assert p.returncode == 0

        # See if the root cert was installed for the first
        # time, if so we want to leave no trace.
        stdout, _ = await p.communicate()
        should_mkcert_uninstall = MKCERT_CA_ALREADY_INSTALLED in stdout

        yield

    finally:
        # Only uninstall mkcert root cert if it wasn't
        # installed before our attempt to install.
        if should_mkcert_uninstall:
            p = await asyncio.create_subprocess_exec(
                "mkcert",
                "-uninstall",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await p.wait()


@dataclass
class CertFiles:
    key_file: pathlib.Path
    cert_file: pathlib.Path


@pytest_asyncio.fixture(scope="function")
async def mkcert_certs(mkcert) -> typing.AsyncIterator[CertFiles]:
    with TemporaryDirectory() as tmp_dir:

        # Create the structure we'll eventually return
        # as long as mkcert succeeds in creating the certs.
        tmpdir_path = pathlib.Path(tmp_dir)
        certs = CertFiles(
            cert_file=tmpdir_path / "localhost.pem",
            key_file=tmpdir_path / "localhost-key.pem",
        )

        cmd = (
            "mkcert"
            f" -cert-file {certs.cert_file}"
            f" -key-file {certs.key_file}"
            " localhost"
        )
        p = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        await asyncio.wait_for(p.wait(), timeout=SUBPROCESS_TIMEOUT)

        # Check for any signs that mkcert wasn't able to issue certs
        # or that the CA isn't installed
        stdout, _ = await p.communicate()
        if MKCERT_CA_NOT_INSTALLED in stdout or p.returncode != 0:
            raise RuntimeError(
                f"mkcert couldn't issue certificates "
                f"(exited with {p.returncode}): {stdout.decode()}"
            )

        yield certs


@dataclass
class Server:
    host: str
    port: int

    @property
    def base_url(self) -> str:
        return f"https://{self.host}:{self.port}"


@pytest_asyncio.fixture(scope="function")
async def server(mkcert_certs: CertFiles) -> typing.AsyncIterator[Server]:
    async def handler(request: web.Request) -> web.Response:
        # Check the request was served over HTTPS.
        assert request.scheme == "https"

        return web.Response(status=200)

    app = web.Application()
    app.add_routes([web.get("/", handler)])

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(
        certfile=mkcert_certs.cert_file,
        keyfile=mkcert_certs.key_file,
    )

    # we need keepalive_timeout=0
    # see https://github.com/aio-libs/aiohttp/issues/5426
    runner = web.AppRunner(app, keepalive_timeout=0)
    await runner.setup()
    port = 9999  # Arbitrary choice.
    site = web.TCPSite(runner, ssl_context=ctx, port=port)
    await site.start()
    try:
        yield Server(host="localhost", port=port)
    finally:
        await site.stop()
        await runner.cleanup()


async def test_urllib3_custom_ca(server: Server) -> None:
    def test_urllib3():
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with urllib3.PoolManager(ssl_context=ctx) as client:
            resp = client.request("GET", server.base_url)
        assert resp.status == 200

    thread = asyncio.to_thread(test_urllib3)
    await thread


@pytest.mark.asyncio
async def test_aiohttp_custom_ca(server: Server) -> None:
    ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    async with ClientSession() as client:
        resp = await client.get(server.base_url, ssl=ctx)
        assert resp.status == 200
