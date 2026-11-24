#!/usr/bin/env python3
"""Replay this historical batch's browser assertions against fresh local fixtures."""
from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
import json
from pathlib import Path
import select
import subprocess
import uuid


SCRIPTS = Path(__file__).resolve().parent


@contextmanager
def fixture():
    process = subprocess.Popen(
        ["node", str(SCRIPTS / "representative-server.cjs")],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout is not None
        if not select.select([process.stdout], [], [], 10)[0]:
            raise TimeoutError("Local fixture did not announce its URL")
        yield json.loads(process.stdout.readline())["baseUrl"]
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if process.stdout is not None:
            process.stdout.close()


def ego(script: str, destination: Path, timeout: int) -> str:
    result = subprocess.run(
        ["ego-browser", "nodejs"],
        input=script, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    with destination.open("x", encoding="utf-8") as output:
        output.write(result.stdout)
        output.write(f"\nexit={result.returncode}\n")
    print(result.stdout, end="", flush=True)
    result.check_returncode()
    return result.stdout


def replay(evidence: Path, mode: str) -> None:
    evidence.mkdir(mode=0o700)
    space_name = json.dumps("Agentflow fixture replay " + uuid.uuid4().hex[:10])
    opening = ego(
        f'const task=await taskSpace({space_name});'
        'console.log("AGENTFLOW_SPACE="+task.spaceId);',
        evidence / "space.txt", 30,
    )
    space_id = int(next(line.removeprefix("AGENTFLOW_SPACE=") for line in opening.splitlines()
                        if line.startswith("AGENTFLOW_SPACE=")))
    config = {"spaceId": space_id, "pageLabel": "p1", "evidence": str(evidence)}

    def run_script(name: str, inputs: dict) -> None:
        preamble = "globalThis.agentflowReplay=" + json.dumps({**config, **inputs}) + ";\n"
        source = (SCRIPTS / f"{name}.mjs").read_text(encoding="utf-8")
        ego(preamble + source, evidence / f"{name}.txt", 180)

    if mode in {"smoke", "all"}:
        with fixture() as base_url:
            run_script("representative-browser", {"baseUrl": base_url})
    if mode in {"extended", "all"}:
        with ExitStack() as stack:
            servers = {name: stack.enter_context(fixture())
                       for name in ("list-message", "action-browser", "action-api")}
            run_script("representative-browser-extended", {"servers": servers})
    ego(f"const task=await taskSpace({space_id}); await task.finish({{keep:[]}});",
        evidence / "finish.txt", 30)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("all", "smoke", "extended"), default="all")
    parser.add_argument("--output", type=Path, required=True, help="New evidence directory")
    args = parser.parse_args()
    try:
        replay(args.output.expanduser().absolute(), args.mode)
    except (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError) as exc:
        print(f"Replay stopped: {exc}. See evidence and space ID in {args.output}.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
