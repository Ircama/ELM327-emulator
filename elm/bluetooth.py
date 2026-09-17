#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

"""
Native cross-platform Bluetooth RFCOMM / SPP transport for ELM327-emulator.

Unlike the serial COM-port interfaces (which need a pseudo-tty on UNIX/Linux
and a virtual serial driver such as com0com on Windows), this module exposes a
native Bluetooth Serial Port Profile (SPP) *server* implemented in pure Python:
the emulator registers itself as a discoverable Bluetooth SPP service and a
Bluetooth client (a phone/tablet OBD app, a laptop, ...) connects to it
directly, with no virtual serial port driver involved.

Design notes
------------
The technique is derived from the sibling project
`Ircama/PT-P300BT <https://github.com/Ircama/PT-P300BT>`_, which implements the
*client* side of the same problem (see ``native/btcommon.py`` and
``native/btnative.py``).  Since ELM327-emulator plays the opposite role (it
emulates the adapter, i.e. the SPP *server*), the same platform strategies are
reused but inverted:

- **Windows**: the Winsock Bluetooth stack is used directly through the standard
  :mod:`socket` module (``AF_BLUETOOTH``/``BTHPROTO_RFCOMM``).  A listening
  RFCOMM socket with no kernel-mode driver is all that is needed, so *com0com
  is not required* when a Bluetooth link is used.
- **Linux**: the same stdlib RFCOMM socket is used; additionally the SDP record
  is published with the BlueZ ``sdptool`` utility (best effort) and, when a
  specific channel cannot be bound, the ``rfcomm`` utility is used as fallback.
- **macOS**: unlike Linux and Windows, Darwin does not provide
  ``AF_BLUETOOTH`` sockets.  The IOBluetooth framework is used through PyObjC
  (the very same technique adopted by PT-P300BT): ``IOBluetooth`` publishes the
  SDP service record and delivers incoming RFCOMM channels, and the macOS run
  loop is pumped while waiting for data.  This is what makes macOS Ventura and
  later usable, where Apple no longer offers a Bluetooth serial tty port.

``BluetoothSerial`` exposes a :class:`serial.Serial`-compatible interface
(``read``/``write``/``reset_input_buffer``/``reset_output_buffer``/``flush``/
``close``) so that the emulator can use it exactly like a pyserial port.
"""

import atexit
import logging
import os
import socket
import subprocess
import sys
import time

__all__ = [
    "BTError",
    "BluetoothSerial",
    "platform_backend",
    "list_devices",
    "SERVICE_NAME",
    "SPP_UUID",
    "SPP_UUID16",
    "DEFAULT_CHANNEL",
    "RFCOMM_PROTOCOL",
]

# The name advertised in the SDP service record and matched by clients.
SERVICE_NAME = "ELM327"
# Serial Port Profile (SPP) UUID: 00001101-0000-1000-8000-00805f9b34fb
SPP_UUID16 = 0x1101
SPP_UUID = "00001101-0000-1000-8000-00805f9b34fb"
# RFCOMM channel normally used by Serial Port Profile services.
DEFAULT_CHANNEL = 1
# BTPROTO_RFCOMM (BlueZ) == BTHPROTO_RFCOMM (Winsock) == 3
RFCOMM_PROTOCOL = 3
# BDADDR_ANY: wildcard local Bluetooth adapter address.
BDADDR_ANY = "00:00:00:00:00:00"
# Unknown local Bluetooth adapter address.
MD_UNKNOWN_ADAPTER = "?"
# Winsock/BlueZ errors meaning "the requested channel is taken".
_CHANNEL_BUSY_ERRNOS = (10013, 10048, 98)  # WSAEACCES, WSAEADDRINUSE, EADDRINUSE

IS_WINDOWS = os.name == "nt"
IS_MACOS = sys.platform == "darwin"
IS_LINUX = not IS_WINDOWS and not IS_MACOS


class BTError(Exception):
    """Bluetooth transport error (configuration or link failure)."""


def platform_backend():
    """Return the Bluetooth backend name for the running platform."""
    if IS_MACOS:
        return "macos"
    if IS_WINDOWS:
        return "windows"
    return "linux"


def _normalize_mac(value):
    """Return a MAC address as 12 lowercase hex digits (or None)."""
    if not value or not isinstance(value, str):
        return None
    digits = value.replace(":", "").replace("-", "").strip().lower()
    if len(digits) == 12 and all(c in "0123456789abcdef" for c in digits):
        return digits
    return None


# =========================================================================
# Socket based backend (Windows / Linux) -- no kernel-mode driver required
# =========================================================================

class _SocketRFCOMMBackend:
    """RFCOMM SPP server built on the stdlib Bluetooth socket API.

    Used on Windows (Winsock ``AF_BLUETOOTH``) and on Linux (BlueZ
    ``AF_BLUETOOTH``).  The listening socket advertises the SPP service on the
    requested RFCOMM channel; if that channel is unavailable (for instance
    because the OS Bluetooth stack already reserved channel 1), the next free
    channel is selected automatically.
    """

    def __init__(self, name, channel, backlog=1):
        if not hasattr(socket, "AF_BLUETOOTH"):
            raise BTError(
                "This Python build has no AF_BLUETOOTH socket support; "
                "native Bluetooth SPP is unavailable on this platform.")
        proto = getattr(socket, "BTPROTO_RFCOMM", RFCOMM_PROTOCOL)
        try:
            self._listen = socket.socket(
                socket.AF_BLUETOOTH, socket.SOCK_STREAM, proto)
        except OSError as e:
            raise BTError("Cannot create Bluetooth RFCOMM socket: %s" % (e,))
        try:
            self._listen.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except OSError:
            pass  # not supported by every Bluetooth stack

        channels = self._channel_candidates(channel)
        last_err = None
        bound = False
        for ch in channels:
            try:
                self._listen.bind((BDADDR_ANY, ch))
                bound = True
                break
            except OSError as e:
                last_err = e
                if getattr(e, "errno", None) not in _CHANNEL_BUSY_ERRNOS and \
                        getattr(e, "winerror", None) not in _CHANNEL_BUSY_ERRNOS:
                    break  # a different problem: no point in trying more
        if not bound:
            try:
                self._listen.close()
            except OSError:
                pass
            raise BTError(
                "Cannot bind a Bluetooth RFCOMM server socket on channel %s "
                "(%s). On Windows, the well-known SPP channels (1-4) are "
                "usually reserved by the OS Bluetooth stack; try another "
                "channel or let the emulator choose one automatically." %
                (channel, last_err))

        try:
            address, self._channel = self._listen.getsockname()
        except OSError:
            address, self._channel = MD_UNKNOWN_ADAPTER, channel
        self._address = address or MD_UNKNOWN_ADAPTER
        self._listen.listen(backlog)
        self._client = None
        self._name = name
        # Read timeout applied to the accepted client, so that reads return
        # periodically (the emulator loop stays responsive to termination).
        self.timeout = 0.2
        self._publish_sdp()

    @staticmethod
    def _channel_candidates(channel):
        """Ordered list of channels to try: requested first, then any free one.

        Concrete channels are preferred over the ``0`` wildcard because the
        Windows Bluetooth stack does not report the channel it assigns when
        the wildcard is used, and the client must be told which channel to
        connect to.
        """
        try:
            channel = int(channel)
        except (TypeError, ValueError):
            channel = DEFAULT_CHANNEL
        result = [channel] if 1 <= channel <= 30 else [DEFAULT_CHANNEL]
        for ch in range(1, 31):
            if ch not in result:
                result.append(ch)
        result.append(0)  # last resort: let the Bluetooth stack choose
        return result

    def _publish_sdp(self):
        """Publish the SPP SDP record (Linux/BlueZ only, best effort).

        Windows publishes no SDP record from user mode (that would require
        ``WSASetService``, which is not exposed by the stdlib), therefore the
        chosen channel must be communicated to the client out of band.
        """
        if not IS_LINUX:
            return
        for tool in ("/usr/bin/sdptool", "/usr/local/bin/sdptool",
                     "/bin/sdptool"):
            if not os.path.exists(tool):
                continue
            try:
                subprocess.run(
                    [tool, "add", "--channel=%d" % self._channel,
                     "--name=%s" % self._name, "SP"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=10)
                logging.debug(
                    "Bluetooth SDP record published on channel %d "
                    "via %s.", self._channel, tool)
            except (OSError, subprocess.SubprocessError) as e:
                logging.debug("Cannot publish SDP record with %s: %s", tool, e)
            return

    def accept(self, timeout):
        if self._client is not None:
            return True
        try:
            readable, _, _ = _select_readable(self._listen, timeout)
        except OSError as e:
            logging.debug("Bluetooth accept poll failed: %s", e)
            return False
        if not readable:
            return False
        try:
            self._client, peer = self._listen.accept()
        except OSError as e:
            logging.debug("Bluetooth accept failed: %s", e)
            return False
        try:
            self._client.settimeout(self.timeout)
        except OSError:
            pass
        logging.info(
            "Bluetooth client connected to SPP service '%s' from %s.",
            self._name, peer[0] if peer else "?")
        return True

    def recv(self, n):
        try:
            return self._client.recv(n)
        except socket.timeout:
            return b""
        except OSError as e:
            logging.debug("Bluetooth client disconnected: %s", e)
            self._drop_client()
            return b""

    def send(self, data):
        if self._client is None:
            return 0
        try:
            self._client.sendall(bytes(data))
        except OSError as e:
            logging.debug("Bluetooth write failed: %s", e)
            self._drop_client()
            return 0
        return len(data)

    def _drop_client(self):
        if self._client is not None:
            try:
                self._client.close()
            except OSError:
                pass
            self._client = None

    @property
    def connected(self):
        return self._client is not None

    @property
    def address(self):
        return self._address

    @property
    def channel(self):
        return self._channel

    @property
    def description(self):
        return ("Bluetooth RFCOMM/SPP server '%s' on channel %s "
                "(adapter %s)" % (self._name, self._channel, self._address))

    def close(self):
        self._drop_client()
        try:
            self._listen.close()
        except OSError:
            pass


MD_UNKNOWN_ADAPTER = "?"


def _select_readable(sock, timeout):
    """``select`` wrapper returning ``([sock], [], [])`` when readable."""
    import select
    return select.select([sock], [], [], timeout)


# =========================================================================
# macOS backend (IOBluetooth via PyObjC)
# =========================================================================

# PyObjC and the IOBluetooth framework are available on macOS only.  The
# guarded module level imports let the class definitions below reach the
# framework names as module globals (methods defined in a nested class cannot
# access the enclosing function locals).  A missing dependency is recorded
# rather than raised, so the rest of ELM327-emulator keeps working when
# Bluetooth is not used.
_macos_import_error = None
if IS_MACOS:
    try:
        import objc
        from Foundation import (NSObject, NSDefaultRunLoopMode, NSRunLoop,
                                NSDate, NSNumber)
        import IOBluetooth
    except ImportError as e:  # pragma: no cover - depends on host setup
        _macos_import_error = e


def _load_macos_backend_class():
    """Return the PyObjC based macOS backend class (or raise BTError)."""
    if _macos_import_error is not None:
        raise BTError(
            "Native macOS Bluetooth support requires PyObjC.\n"
            "Install it with:  python3 -m pip install "
            "pyobjc-framework-IOBluetooth\n(%s)" % (_macos_import_error,))
    return _MacOSBackend


if IS_MACOS and _macos_import_error is None:  # pragma: no cover - macOS only

    def _spin(cond, deadline):
        """Pump the run loop (delivering IOBluetooth callbacks) until cond().

        This is the crux of the macOS support, ported from PT-P300BT: the
        macOS run loop must be drained for IOBluetooth to deliver data and to
        tear the channel down cleanly.
        """
        run_loop = NSRunLoop.currentRunLoop()
        while not cond() and time.time() < deadline:
            run_loop.runMode_beforeDate_(
                NSDefaultRunLoopMode,
                NSDate.dateWithTimeIntervalSinceNow_(0.05))

    def _number(value):
        """Wrap an SDP attribute ID in an NSNumber (used as dictionary key)."""
        return NSNumber.numberWithInt_(value)

    class _Delegate(NSObject):
        """Receives incoming RFCOMM channels and their data."""

        def init(self):
            self = objc.super(_Delegate, self).init()
            if self is None:
                return None
            self.pending = None
            self.channel = None
            self.rx = bytearray()
            self.closed = False
            self.open_status = -1
            self.open_done = False
            return self

        # Incoming channel notification (registered with the selector below).
        def newRFCOMMChannelOpened_(self, channel):
            self.pending = channel

        def rfcommChannelOpenComplete_status_(self, channel, status):
            self.open_status = status
            self.open_done = True

        def rfcommChannelData_data_length_(self, channel, data, length):
            # PyObjC bridges (void *data, size_t length) to a buffer object.
            try:
                self.rx += bytes(data[:length])
            except Exception:  # pragma: no cover - defensive
                pass

        def rfcommChannelClosed_(self, channel):
            self.closed = True
            self.channel = None

    class _MacOSBackend:
        """IOBluetooth SPP server: publishes SDP and accepts RFCOMM channels."""

        def __init__(self, name, channel, backlog=1):
            self._name = name
            self._address = MD_UNKNOWN_ADAPTER
            self._channel = channel
            self._client = None
            self._delegate = _Delegate.alloc().init()
            self._notification = None
            self._record = None

            cid = self._publish_sdp_record(name, channel)
            self._channel = cid
            self._register_for_incoming(cid)

        # ----- SDP service publication ---------------------------------
        def _publish_sdp_record(self, name, channel):
            try:
                channel = int(channel)
            except (TypeError, ValueError):
                channel = DEFAULT_CHANNEL
            number = _number
            spp_uuid = IOBluetooth.IOBluetoothSDPUUID.uuid16_(SPP_UUID16)
            l2cap_uuid = IOBluetooth.IOBluetoothSDPUUID.uuid16_(0x0100)
            rfcomm_uuid = IOBluetooth.IOBluetoothSDPUUID.uuid16_(0x0003)
            browse_uuid = IOBluetooth.IOBluetoothSDPUUID.uuid16_(0x1002)
            # Keys are SDP attribute IDs represented as NSNumber (see the
            # IOBluetoothSDPServiceRecord documentation).
            service = {
                number(0x0001): [spp_uuid],                    # ServiceClassIDList
                number(0x0004): [                              # ProtocolDescriptorList
                    [l2cap_uuid],
                    [rfcomm_uuid, number(channel)],
                ],
                number(0x0005): [browse_uuid],                 # BrowseGroupList
                number(0x0100): name,                          # ServiceName
            }
            try:
                record = IOBluetooth.IOBluetoothSDPServiceRecord.\
                    publishedServiceRecordWithDictionary_(service)
            except Exception as e:  # pragma: no cover - platform specific
                raise BTError(
                    "Cannot publish the macOS Bluetooth SDP service record: %s"
                    % (e,))
            if record is None:
                raise BTError(
                    "Cannot publish the macOS Bluetooth SDP service record.")
            self._record = record
            try:
                res, cid = record.getRFCOMMChannelID_(None)
            except Exception:  # pragma: no cover - platform specific
                res, cid = 1, channel
            if res == 0 and cid:
                return cid
            return channel

        # ----- incoming channel registration ---------------------------
        def _register_for_incoming(self, cid):
            direction = getattr(
                IOBluetooth,
                "kIOBluetoothUserNotificationChannelDirectionIncoming", 1)
            try:
                self._notification = IOBluetooth.IOBluetoothRFCOMMChannel.\
                    registerForChannelOpenNotifications_selector_withChannelID_direction_(
                        self._delegate, b"newRFCOMMChannelOpened:", cid,
                        direction)
            except Exception as e:  # pragma: no cover - platform specific
                raise BTError(
                    "Cannot register for incoming macOS RFCOMM channels "
                    "on channel %s: %s" % (cid, e))
            if self._notification is None:
                raise BTError(
                    "Cannot register for incoming macOS RFCOMM channels "
                    "on channel %s." % (cid,))

        # ----- backend interface ---------------------------------------
        def accept(self, timeout):
            if self._client is not None:
                return True
            # Pump the run loop so IOBluetooth delivers the open notification.
            _spin(lambda: self._delegate.pending is not None,
                  time.time() + max(timeout, 0.0))
            channel = self._delegate.pending
            if channel is None:
                return False
            self._delegate.pending = None
            try:
                channel.setDelegate_(self._delegate)
            except Exception as e:  # pragma: no cover - platform specific
                logging.debug("Cannot set macOS RFCOMM channel delegate: %s", e)
                return False
            self._delegate.channel = channel
            self._delegate.closed = False
            self._client = channel
            logging.info(
                "Bluetooth client connected to SPP service '%s' "
                "(macOS, channel %s).", self._name, self._channel)
            return True

        def recv(self, n):
            if self._client is None:
                return b""
            _spin(lambda: len(self._delegate.rx) >= n or self._delegate.closed,
                  time.time() + 0.2)
            if self._delegate.closed:
                self._drop_client()
                return b""
            take = min(len(self._delegate.rx), n)
            if not take:
                return b""
            data = bytes(self._delegate.rx[:take])
            del self._delegate.rx[:take]
            return data

        def send(self, data):
            if self._client is None:
                return 0
            data = bytes(data)
            try:
                mtu = int(self._client.getMTU()) or 320
                for i in range(0, len(data), mtu):
                    seg = data[i:i + mtu]
                    self._client.writeSync_length_(seg, len(seg))
            except Exception as e:  # pragma: no cover - platform specific
                logging.debug("Bluetooth write failed: %s", e)
                self._drop_client()
                return 0
            return len(data)

        def _drop_client(self):
            channel = self._client
            self._client = None
            if channel is not None:
                try:
                    channel.closeChannel()
                except Exception:
                    pass
                # Drain the run loop so bluetoothd tears the channel down.
                _spin(lambda: self._delegate.closed, time.time() + 1.0)

        @property
        def connected(self):
            return self._client is not None

        @property
        def address(self):
            return self._address

        @property
        def channel(self):
            return self._channel

        @property
        def description(self):
            return ("Bluetooth RFCOMM/SPP server '%s' on channel %s "
                    "(macOS IOBluetooth)" % (self._name, self._channel))

        def close(self):
            self._drop_client()
            if self._notification is not None:
                try:
                    self._notification.unregister()
                except Exception:
                    pass
                self._notification = None
            if self._record is not None:
                # The ObjC selector is exposed under different names depending
                # on the PyObjC version; both are tried (best effort).
                for method in ("remove", "removeServiceRecord"):
                    try:
                        getattr(self._record, method)()
                        break
                    except Exception:
                        continue
                self._record = None


# =========================================================================
# Public, serial.Serial-compatible facade
# =========================================================================

class BluetoothSerial:
    """``serial.Serial``-compatible native Bluetooth SPP *server* port.

    The socket is opened when the object is created and a Bluetooth client can
    connect at any time.  ``read()`` returns ``b""`` while no client is
    connected (after a short poll), so the emulator main loop is never blocked
    forever and can be terminated cleanly.

    :param name: SDP service name advertised to clients.
    :param channel: preferred RFCOMM channel (``None``/``0`` to auto-select).
    :param poll_interval: seconds to wait before polling again when no client
        is connected.
    """

    def __init__(self, name=None, channel=None, poll_interval=0.05):
        self.name = str(name) if name else SERVICE_NAME
        self.poll_interval = poll_interval
        self.timeout = 0.2
        self.is_open = False
        self.backend = None
        self.address = MD_UNKNOWN_ADAPTER
        self.channel = channel
        try:
            channel = int(channel) if channel is not None else DEFAULT_CHANNEL
        except (TypeError, ValueError):
            channel = DEFAULT_CHANNEL
        backend_name = platform_backend()
        if backend_name == "macos":
            cls = _load_macos_backend_class()
        else:
            cls = _SocketRFCOMMBackend
        self.backend = cls(self.name, channel)
        self.address = self.backend.address
        self.channel = self.backend.channel
        self.is_open = True
        atexit.register(self.close)
        logging.info("Bluetooth SPP server started: %s.", self.port_name)

    @property
    def port_name(self):
        """Human readable description of the Bluetooth port."""
        if self.backend is None:
            return "Bluetooth SPP server '%s' (closed)" % self.name
        return self.backend.description

    @property
    def client_connected(self):
        return bool(self.backend and self.backend.connected)

    # ----- pyserial compatible I/O -------------------------------------
    def read(self, n=1):
        """Return up to ``n`` bytes (``b""`` on timeout or no client)."""
        if not self.is_open or self.backend is None:
            return b""
        if not self.backend.connected:
            if not self.backend.accept(self.timeout):
                # No client yet: do not busy-spin the emulator main loop.
                time.sleep(self.poll_interval)
                return b""
        return self.backend.recv(n)

    def write(self, data):
        """Write ``data`` to the connected client (no-op if not connected)."""
        if not self.is_open or self.backend is None:
            return 0
        return self.backend.send(data)

    def reset_input_buffer(self):
        pass

    def reset_output_buffer(self):
        pass

    def flush(self):
        pass

    def close(self):
        if self.backend is not None:
            self.backend.close()
            self.backend = None
        self.is_open = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False

    def __str__(self):
        return self.port_name


# =========================================================================
# Optional paired-device discovery helpers (adapted from PT-P300BT)
# =========================================================================

def list_devices():
    """Return ``[(name, address, channel_or_port), ...]`` for known devices.

    This is a diagnostic helper mirroring the discovery logic of PT-P300BT:
    it is not needed to run the emulator, but it helps understanding which
    Bluetooth devices are already paired with the host.

    - macOS: paired devices and their SPP RFCOMM channel (IOBluetooth).
    - Windows: paired SPP devices and the COM port the stack exposes.
    - Linux: paired devices reported by ``bluetoothctl``.
    """
    backend = platform_backend()
    if backend == "macos":
        return _list_devices_macos()
    if backend == "windows":
        return _list_devices_windows()
    return _list_devices_linux()


def _list_devices_macos():
    try:
        import IOBluetooth
    except ImportError:
        raise BTError(
            "Listing Bluetooth devices on macOS requires PyObjC "
            "(pip install pyobjc-framework-IOBluetooth).")
    devices = []
    for device in IOBluetooth.IOBluetoothDevice.pairedDevices() or []:
        name = device.name() or "?"
        address = device.addressString() or "?"
        channel = DEFAULT_CHANNEL
        spp = IOBluetooth.IOBluetoothSDPUUID.uuid16_(SPP_UUID16)
        record = device.getServiceRecordForUUID_(spp)
        if record is not None:
            res, cid = record.getRFCOMMChannelID_(None)
            if res == 0 and cid:
                channel = cid
        devices.append((name, address, channel))
    return devices


def _list_devices_windows():
    """Paired SPP devices and the COM port Windows exposes for them.

    Names are read from the ``BTHPORT`` registry key (stored as
    null-terminated byte strings); the COM port comes from the ``BTHENUM``
    ``{00001101-...}`` (SPP) service keys.  Placeholder ports carrying the null
    MAC are skipped, exactly as in PT-P300BT.
    """
    import re
    import winreg
    from serial.tools import list_ports

    def _read_name(sub):
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters"
                r"\Devices" + "\\" + sub
            ) as key:
                raw = winreg.QueryValueEx(key, "Name")[0]
            if isinstance(raw, (bytes, bytearray)):
                return raw.split(b"\x00", 1)[0].decode("utf-8", "replace")
            return raw
        except OSError:
            return None

    names = {}
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
        ) as root:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(root, i)
                except OSError:
                    break
                i += 1
                name = _read_name(sub)
                if name:
                    names[sub.lower()] = name
    except OSError:
        pass

    devices = []
    try:
        base = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Enum\BTHENUM")
        with base:
            i = 0
            while True:
                try:
                    dev_key = winreg.EnumKey(base, i)
                except OSError:
                    break
                i += 1
                if not dev_key.lower().startswith(
                        "{00001101-0000-1000-8000-00805f9b34fb}"):
                    continue  # only Serial Port Profile service keys
                try:
                    dk = winreg.OpenKey(base, dev_key)
                except OSError:
                    continue
                with dk:
                    j = 0
                    while True:
                        try:
                            inst = winreg.EnumKey(dk, j)
                        except OSError:
                            break
                        j += 1
                        mac = _normalize_mac(
                            (re.search(r"([0-9a-fA-F]{12})_", inst) or
                             [None, None])[1])
                        if mac is None or mac.strip("0") == "":
                            continue  # skip null-MAC placeholder ports
                        try:
                            with winreg.OpenKey(dk, inst) as ik:
                                friendly = winreg.QueryValueEx(
                                    ik, "FriendlyName")[0]
                        except OSError:
                            continue
                        match = re.search(r"\((COM\d+)\)$", friendly)
                        if not match:
                            continue
                        address = ":".join(
                            mac[x:x + 2] for x in range(0, 12, 2))
                        devices.append((
                            names.get(mac, address), address,
                            match.group(1)))
    except OSError:
        pass

    if not devices:
        for port in list_ports.comports():
            desc = port.description or ""
            if "standard serial over bluetooth" in desc.lower():
                devices.append((desc, port.hwid, port.device))
    return devices


def _list_devices_linux():
    devices = []
    try:
        out = subprocess.run(
            ["bluetoothctl", "devices"],
            capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return devices
    for line in out.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) >= 3 and parts[0] == "Device":
            devices.append((parts[2], parts[1], DEFAULT_CHANNEL))
    return devices
