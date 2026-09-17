# Release process

Only tags are used by now (not releases).

Do not remove '# Connecting' in README.md.

# Tagging a release

If a version needs to be changed, edit `elm/__version__.py`.

This file is read by *setup.py*.

If the version is not changed, the publishing procedure works using the same version with a different build number.

The GITHUB_RUN_NUMBER environment variable, when available, is read by *setup.py*.

Push all changes:

```shell
git commit -a
git push
```

_After pushing the last commit_, add a local tag (shall be added AFTER the commit that needs to be published):

```shell
git tag # list local tags
git tag v0.1.4
```

Notes:

- correspondence between tag and `__version__.py` is not automatic.
- the tag must start with "v" if a GitHub Action workflow needs to be run

Push this tag to the origin, which starts the PyPI publishing workflow (GitHub Action):

```shell
git push origin v0.1.4
git ls-remote --tags https://github.com/Ircama/ELM327-emulator # list remote tags
```

Check the published tag here: https://github.com/Ircama/ELM327-emulator/tags

It shall be even with the last commit.

Check the GitHub Action: https://github.com/Ircama/ELM327-emulator/actions

Check PyPI:

- https://test.pypi.org/manage/project/ELM327-emulator/releases/
- https://pypi.org/manage/project/ELM327-emulator/releases/

End user publishing page:

- https://test.pypi.org/project/ELM327-emulator
- https://pypi.org/project/ELM327-emulator/

Verify whether wrong builds need to be removed.

Test installation:

```shell
cd
python3 -m pip uninstall -y ELM327-emulator
python3 -m pip install ELM327-emulator
elm
python3 -m pip uninstall -y ELM327-emulator
```

# Updating the same tag (using a different build number for publishing)

```shell
git tag # list tags
git tag -d v0.1.5 # remove local tag
git push --delete origin v0.1.5 # remove remote tag
git ls-remote --tags https://github.com/Ircama/ELM327-emulator # list remote tags
```

Then follow the tagging procedure again to add the tag to the latest commit.

# Testing the build procedure locally

The build backend is declared in `pyproject.toml` (`setuptools`), so that the
build works on Python 3.14 too: since Python 3.14 the build backend is no longer
implicitly available in the isolated build environment and the `pkg_resources`
module removed from recent setuptools is no longer used by `setup.py`.

```shell
cd <repository directory>
```

## Local build (using build):

```shell
python3 -m build --sdist --wheel --outdir dist/ .
python3 -m twine upload --repository testpypi dist/*
```

## Local build (using setup):

```shell
python3 setup.py sdist bdist_wheel
python3 -m twine upload --repository testpypi dist/*
```

## Local build (using build versions):

```shell
GITHUB_RUN_NUMBER=31 python3 setup.py sdist bdist_wheel
python3 -m twine upload --repository testpypi dist/*
```

## Removing directories

```shell
ls -l dist
rm -r build dist ELM327_emulator.egg-info
```

# Security notes

The TCP/IP interface (`-n`) binds its socket to the `127.0.0.1` loopback address
by default, so that the emulator (which implements no authentication) is not
exposed to other hosts. The interface can be changed with the `-i`/`--interface`
option; `-i 0.0.0.0` (or `-i ::`) restores the previous behaviour of accepting
connections from any address and produces a warning at startup. Mention this in
the release notes, because it changes the default behaviour of the `-n` option.

# Behaviour notes

Other changes to be mentioned in the release notes:

- Windows: the `lockfile` and `python-daemon` packages are no longer imported
  (and no longer needed) on Windows and are now declared with environment
  markers in `install_requires`. Previously an installation could break on
  Windows because `lockfile` was imported unconditionally, while it was only
  available as a dependency of *python-daemon*.
- Windows: no virtual serial port driver is needed when the application can use
  Bluetooth SPP (`-w`, `-k`) or a WiFi/network adapter (`-n`). Only the serial
  port (`-p`) interface requires a driver like *com0com*.
- CAN scenarios (`default`, `car`): the initial `SEARCHING...` answer (and the
  related 1.5 s delay) is now emitted only when the client does not select the
  protocol with `ATTP`, like a real adapter, which searches the protocol only
  when it has to determine it. Strict clients (e.g., *HUD ECU Hacker*) receive
  the CAN answer at once; before this change they aborted with
  "Unexpected Rx data: SEARCHING..." and then timed out.
- `mt05` scenario: answers use K-Line/ISO 14230 framing (`<pos_answer>`) instead
  of CAN ISO 15765 framing, and the security access PIDs are named
  `UDS_REQ_SEED`/`UDS_SEND_KEY`. Scenario dictionaries are merged by key name,
  so the formerly used `UDS_SA_*` names did not override the generic `default`
  entries (a 3-byte seed was answered instead of the MT05 2-byte seed).
- [make_mmap_input.py](make_mmap_input.py) was added to create the
  `mmap-input.bin` memory map file required by the MT05 memory plugins, starting
  from a firmware image.
- `car` scenario: modes 03, 07 and 0A return the DTCs stored in the
  `DTC_STORED`, `DTC_PENDING` and `DTC_PERMANENT` variables of
  `elm/obd_message.py` (empty by default), framed with the ISO-TP single or
  multiple frame encoding; mode 04 clears them.
- `car` scenario: mode 01 requests including up to six PIDs (SAE J1979) are now
  answered with a single ISO-TP response.
- Requests sent to the functional address (`ATSH 7DF` or `18DB33F1`) are now
  answered by the entries related to a physical ECU address (they were skipped
  before, so most of the requests returned *NO DATA*) and the response uses the
  address of the answering ECU (a request using `<pos_answer>`/`<answer>` tags
  answered *7E7* instead of *7E8* before this change).
- `ATD0`/`ATD1` now control the display of the DLC byte when headers are off;
  they were ignored before.
- A new `-c`/`--slcan PORT` option makes the emulator expose a **CAN interface**
  running the SLCAN (Lawicel) firmware (like a CANable/CANtact adapter) instead
  of the ELM327 protocol: the connected CAN application exchanges CAN frames
  with the emulated ECUs (ISO-TP single/multiple frames, flow control included).
  It is a separate option from `-p`/`-n`/`-w` and does not require any driver
  when a virtual serial port pair is used; on Linux the interface can be
  attached to SocketCAN with `slcand` (`slcand -o -c -s6 /dev/pts/N can0`).
- The `car` scenario now also defines PIDs `2D` (EGR error), `2F` (fuel level)
  and `32` (evap system vapor pressure); the supported PIDs bitmaps are
  regenerated accordingly.
- A new `-K`/`--kline PORT` option makes the emulator emulate an **ECU connected
  to a K-Line interface** (a VAG KKL or similar serial K-Line adapter): the
  application drives the K-Line directly (ISO 9141-2 / ISO 14230) and the
  emulated ECUs answer the OBD-II requests. The emulation includes the echo of
  the transmitted bytes, the 5 baud wake-up answer (`55 08 08`), the *Start
  Communication* service and the ISO 14230 checksum. It was verified with HUD
  ECU Hacker 6.0.5 (`K-Line / VAG KKL` adapter type) over a com0com pair.
- The `mt05` UDS handshake entries (`81` *Start Communication* and `82` *Stop
  Communication*) belong to the `default` scenario, which is the base of every
  scenario: they no longer switch the emulated scenario when another scenario is
  selected. Previously a *Stop Communication* received while the `car` scenario
  was in use silently switched the emulator to `default`, so all the entries of
  the selected scenario (mode 03/07/0A, mode 02, and the scenario specific PIDs)
  were no longer recognized and answered with *NO DATA*.
- Mode 08 (`0800`) and mode 09 (`0900`) group requests are no longer removed by
  the dynamic mode 01 PID generator: the generator replaced the static grouped
  entries, but its removal filter also deleted the `PIDS_8` and `ELM_PIDS_9A`
  entries, which are not mode 01 PIDs.
- The mode 09 group answer (`0900`) now computes its supported PIDs bitmap on
  the scenario in use (`supported_pids_bitmap()` in `elm/obd_message.py`), so it
  advertises only the emulated mode 09 PIDs. A fixed bitmap claiming PIDs which
  are not defined (e.g. `FF FF FF FF`) makes strict clients request them and
  then fail (log lines like `Unknown request: '0920'` or `'090A'`).
