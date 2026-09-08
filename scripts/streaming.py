"""Explicit local video pilot commands. No inference, recordings or network exposure."""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import platform
import subprocess  # noqa: S404 - fixed executables and argument arrays, never a shell
import tarfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.20.1"
DESTINATION = ROOT / "tools" / "streaming" / VERSION
CONFIG = ROOT / "config" / "streaming" / "mediamtx.local.yml"
PUBLISH_URL = "rtsp://127.0.0.1:8554/camera1"
ASSETS = {
    "Windows": (
        "windows_amd64.zip",
        "mediamtx.exe",
        "dc970f8e1f3ad58edafcf536bcd1ffe0adcb4390e7ace9377694a9ea2c1ebe53",
    ),
    "Linux": (
        "linux_amd64.tar.gz",
        "mediamtx",
        "81b143f55a5d23d4a8c028d52869c14ea4a59919900528698fcc97a747fd69c6",
    ),
}


def asset() -> tuple[str, str, str]:
    if platform.machine().lower() not in {"amd64", "x86_64"} or platform.system() not in ASSETS:
        raise ValueError("Este instalador suporta somente Windows/Linux x86-64.")
    return ASSETS[platform.system()]


def unpack_verified(data: bytes, suffix: str, executable: str, expected: str) -> bytes:
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("SHA-256 do MediaMTX divergente; instalação recusada.")
    # Select exactly one member, never extract paths provided by the archive.
    if suffix.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            return archive.read(executable)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        member = archive.getmember(executable)
        if not member.isfile():
            raise ValueError("Executável inválido no pacote MediaMTX.")
        content = archive.extractfile(member)
        if content is None:
            raise ValueError("Executável ausente no pacote MediaMTX.")
        return content.read()


def setup() -> None:
    suffix, executable, expected = asset()
    url = f"https://github.com/bluenviron/mediamtx/releases/download/v{VERSION}/mediamtx_v{VERSION}_{suffix}"
    with urlopen(url, timeout=60) as response:  # noqa: S310 - fixed HTTPS release URL
        data = response.read(100_000_001)
    if len(data) > 100_000_000:
        raise ValueError("Pacote excede o limite de download.")
    binary = unpack_verified(data, suffix, executable, expected)
    DESTINATION.mkdir(parents=True, exist_ok=True)
    target = DESTINATION / executable
    if target.exists():
        if target.read_bytes() != binary:
            raise ValueError("Já existe outro executável nesse caminho; não será sobrescrito.")
    else:
        target.write_bytes(binary)
        target.chmod(0o755)
    print(f"MediaMTX {VERSION} verificado: {target}")


def ffmpeg() -> str:
    try:
        import imageio_ffmpeg  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ValueError(
            "Ative smart-environment e execute: python -m pip install -e .[stream]"
        ) from exc
    return str(imageio_ffmpeg.get_ffmpeg_exe())


def windows_device(device: str) -> str:
    # DirectShow has its own video=...:audio=... grammar even without a shell.
    if (
        not device.strip()
        or any(char in device for char in ":=")
        or any(ord(char) < 32 for char in device)
    ):
        raise ValueError(
            "Use apenas o nome da webcam, sem seletores extras ou caracteres de controle."
        )
    return f"video={device}"


def publish_args(device: str | None, seconds: int | None) -> list[str]:
    args = [ffmpeg(), "-hide_banner"]
    if device is None:
        args += ["-re", "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30"]
    elif platform.system() == "Windows":
        args += [
            "-f",
            "dshow",
            "-video_size",
            "1280x720",
            "-framerate",
            "30",
            "-i",
            windows_device(device),
        ]
    else:
        if not device.startswith("/dev/video") or not device[len("/dev/video") :].isdigit():
            raise ValueError("No Ubuntu, use um dispositivo como /dev/video0.")
        args += ["-f", "v4l2", "-video_size", "1280x720", "-framerate", "30", "-i", device]
    if seconds is not None:
        if seconds <= 0:
            raise ValueError("A duração deve ser positiva.")
        args += ["-t", str(seconds)]
    args += [
        "-map",
        "0:v:0",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-tune",
        "zerolatency",
        "-profile:v",
        "baseline",
        "-level:v",
        "3.1",
        "-pix_fmt",
        "yuv420p",
        "-b:v",
        "2500k",
        "-maxrate",
        "2500k",
        "-bufsize",
        "2500k",
        "-g",
        "30",
        "-keyint_min",
        "30",
        "-sc_threshold",
        "0",
        "-bf",
        "0",
        "-fps_mode",
        "passthrough",
        "-f",
        "rtsp",
        "-rtsp_transport",
        "tcp",
        PUBLISH_URL,
    ]
    return args


def run(command: list[str], *, local_server: bool = False) -> int:
    # Ctrl+C terminates our child; never stop unrelated server/camera processes.
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper() != "FFREPORT"
        and not (local_server and key.upper().startswith(("MTX_", "RTSP_")))
    }
    child = subprocess.Popen(command, cwd=ROOT, env=environment)  # noqa: S603
    try:
        return child.wait()
    except KeyboardInterrupt:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
        return 130


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("setup", help="baixar MediaMTX fixado e conferir SHA-256")
    commands.add_parser("server", help="iniciar servidor SOMENTE em loopback")
    commands.add_parser("devices", help="listar nomes de webcams no Windows")
    modes = commands.add_parser("modes", help="listar modos de uma webcam no Windows")
    modes.add_argument("--device", required=True)
    test = commands.add_parser("test-pattern", help="publicar padrão sem acessar câmera")
    test.add_argument("--seconds", type=int)
    camera = commands.add_parser("webcam", help="transmitir webcam explicitamente escolhida")
    camera.add_argument("--device", required=True)
    camera.add_argument("--seconds", type=int)
    args = parser.parse_args()
    try:
        if args.command == "setup":
            setup()
            return 0
        if args.command == "server":
            executable = DESTINATION / asset()[1]
            if not executable.is_file():
                raise ValueError("Execute primeiro: python scripts/streaming.py setup")
            return run([str(executable), str(CONFIG)], local_server=True)
        if args.command in {"devices", "modes"}:
            if platform.system() != "Windows":
                raise ValueError(
                    "No Ubuntu, consulte os dispositivos /dev/video* e seus modos V4L2."
                )
            option = "-list_devices" if args.command == "devices" else "-list_options"
            source = "dummy" if args.command == "devices" else windows_device(args.device)
            print("O FFmpeg pode encerrar com código 1 após listar os dispositivos/modos.")
            return run([ffmpeg(), "-hide_banner", option, "true", "-f", "dshow", "-i", source])
        return run(publish_args(args.device if args.command == "webcam" else None, args.seconds))
    except (OSError, ValueError) as exc:
        print(f"Erro: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
