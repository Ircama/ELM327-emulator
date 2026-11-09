# ELM327-emulator in Docker

Runs ELM327-emulator as a TCP server on port `35000`, simulating a car behind an ELM327 adapter. The image is built from the local source tree, so it always contains the code of the current checkout.

## Files

| File | Purpose |
|---|---|
| `Dockerfile` | `python:3.14-slim` + `pip install .` of this repository, starts `python3 -m elm -n 35000 -i 0.0.0.0 -s car` |
| `docker-compose.yaml` | builds the image (context = repository root), publishes port `35000`, keeps an interactive console (`stdin_open`, `tty`), `restart: unless-stopped` |

The `-s car` option selects the emulator's **car** scenario (engine running, speed, RPM, temperatures, fuel trims, O2 sensors, catalyst temperatures, …).

## Start / stop

Run from the `docker` directory:

```bash
cd docker
docker compose up -d --build      # build and start in the background
docker compose ps                 # status
docker compose logs -f            # logs
docker compose down               # stop and remove
```

Without Compose, from the repository root:

```bash
docker build -f docker/Dockerfile -t elm327-emulator .
docker run -it --rm -p 35000:35000 elm327-emulator
```

## Quick check

ELM327 is a plain text protocol (commands end with `\r`, the prompt is `>`):

```bash
(printf 'ATZ\r'; sleep 1; printf 'ATE0\r'; sleep 0.5; printf '010D\r'; sleep 0.5; printf 'ATRV\r'; sleep 0.5) \
  | nc localhost 35000 | tr '\r' '\n'
```

```text
ATZ
ELM327 v1.5
>ATE0
OK
>41 0D 33        <- mode 01 PID 0D (speed) = 0x33 = 51 km/h
>13.6V           <- ATRV, battery voltage
```

(`ATZ` and `ATE0` are echoed because echo is still on until `ATE0` is processed.)

For a live view of the emulated values see the console dashboard in [`../dashboard`](../dashboard).

## Emulator console

The container keeps the emulator's interactive console:

```bash
docker attach elm327-emulator     # type `help` for the emulator commands
                                  # detach with Ctrl-P Ctrl-Q (Ctrl-C stops the container)
```
