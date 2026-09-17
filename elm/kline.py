###########################################################################
# ELM327-emulator
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
#
# K-Line (ISO 9141-2 / ISO 14230) ECU emulation
###########################################################################

"""
Emulate an ECU connected to a K-Line interface (a "VAG KKL" or similar serial
K-Line adapter), so that a diagnostic application which drives the K-Line
directly (without an ELM327) can talk to the emulated ECUs.

The application opens the serial port of the K-Line adapter (use a virtual
serial port pair like com0com on Windows, or a pseudo-tty) and exchanges
ISO 14230 / ISO 9141-2 messages:

* the K-Line is a single (half-duplex) wire, therefore every byte sent by the
  application is echoed back, exactly like a real interface does;
* the messages are reassembled with the ISO 14230 format (format byte with the
  length, target address, source address, data and checksum) and used as
  OBD-II requests, which are answered with the configured scenario dictionary;
* the answer is sent back as an ISO 14230 message with the addresses of the
  request (target and source swapped) and the related checksum.

The initialisation is acknowledged as well: a wake-up byte (the 5 baud address,
which normally appears as a 0x00 or 0x33 byte on the serial port) is answered
with the synchronization bytes expected by the tester, and the "Start
Communication" service (0x81) is answered with the related positive answer,
so that applications performing the bus initialization can connect.
"""

import logging
import re
import time

import serial

KLINE_BAUDRATE = 10400  # standard K-Line baud rate (ISO 9141-2 / ISO 14230)
KLINE_INIT_BYTES = (0x00, 0x33)  # 5 baud wake-up address (0x33)
KLINE_SYNC_RESPONSE = bytes([0x55, 0x08, 0x08])  # sync + KB1 + KB2
KLINE_IDLE_TIMEOUT = 0.02  # seconds of silence ending an ISO 9141-2 message
KLINE_TARGET_ANY = 0x33  # default ECU address (e.g. VAG functional address)
KLINE_TESTER = 0xF1  # default tester address
KLINE_RESPONSE_TIMEOUT = 1.0  # seconds: max wait for a complete request

# <header>7E8</header><size>06</size><data>41 00 BE 3F A8 13</data>
FRAME_RE = re.compile(
    r'<header>\s*([0-9A-Fa-f ]+?)\s*</header>\s*'
    r'<size>\s*([0-9A-Fa-f]+)\s*</size>\s*'
    r'<data>\s*([0-9A-Fa-f ]*?)\s*</data>', re.IGNORECASE)

# Positive answer of the Start Communication service (0xC1 + key bytes).
# The key bytes are the ones expected by the KWP2000 testers: the second key
# byte (0x8F) tells the tester the additional communication services which are
# supported by the ECU (a different value is reported as an unknown ECU by
# applications like HUD ECU Hacker, which also reports the expected value).
START_COMMUNICATION = 'C1 8F 8F'


class KLineServer:
    """
    Emulate a K-Line (ISO 9141-2 / ISO 14230) interface and the ECUs of the
    configured scenario on the related bus.
    """

    def __init__(self, emulator, port, baudrate=KLINE_BAUDRATE):
        """
        :param emulator: ELM327 emulator instance (ref. Elm.__init__)
        :param port: serial port of the K-Line interface
        :param baudrate: serial baud rate of the K-Line interface
        """
        self.emulator = emulator
        self.port = port
        self.baudrate = baudrate
        self.fd = None
        self.rx = []  # received bytes of the current message
        self.rx_length = None  # expected length (ISO 14230 only)
        self.last_byte_time = 0

    def open(self):
        """Open the serial port of the K-Line interface."""
        try:
            self.fd = serial.Serial(port=self.port, baudrate=self.baudrate,
                                    timeout=KLINE_IDLE_TIMEOUT)
        except Exception as e:
            logging.critical('Cannot open the K-Line port %s: %s',
                             self.port, e)
            return False
        return True

    def close(self):
        """Close the serial port of the K-Line interface."""
        if self.fd is not None:
            try:
                self.fd.close()
            except Exception:
                pass
            self.fd = None

    def write(self, data):
        """Write bytes to the K-Line interface."""
        try:
            self.fd.write(data)
        except Exception as e:
            logging.debug('K-Line write error: %s', e)

    def run(self):
        """
        Main loop: echo the received bytes, reassemble the messages and answer
        them until the emulator is terminated.

        :return: True if the K-Line interface is closed. False in case of error.
        """
        if not self.open():
            return False
        logging.info('Emulated K-Line interface started on %s', self.port)
        while (self.emulator.threadState != self.emulator.THREAD.STOPPED and
                self.emulator.threadState != self.emulator.THREAD.TERMINATED):
            if self.emulator.threadState == self.emulator.THREAD.PAUSED:
                continue
            try:
                waiting = self.fd.in_waiting or 1
                data = self.fd.read(waiting)
            except Exception as e:
                logging.debug('K-Line read error: %s', e)
                break
            if not data:
                # Silence: an ISO 9141-2 message (which has no length byte) is
                # terminated by the inter-message idle time
                if (self.rx and self.rx_length is None and
                        time.time() - self.last_byte_time > KLINE_IDLE_TIMEOUT):
                    self.handle_message()
                continue
            self.write(data)  # the K-Line is half duplex: echo the data
            for byte in data:
                self.last_byte_time = time.time()
                self.process_byte(byte)
        self.close()
        return True

    def process_byte(self, byte):
        """
        Process a byte received from the K-Line interface.

        :param byte: received byte
        """
        if not self.rx:
            if byte in KLINE_INIT_BYTES:
                # 5 baud wake-up address: answer with the sync bytes expected
                # by the tester (ref. ISO 9141-2 / ISO 14230 initialization)
                logging.debug('K-Line wake-up (0x%02X) received', byte)
                self.write(KLINE_SYNC_RESPONSE)
                return
            self.rx = [byte]
            if byte & 0x80:  # ISO 14230: the format byte includes the length
                self.rx_length = byte & 0x3F
            else:  # ISO 9141-2: the length is given by the message timing
                self.rx_length = None
            return
        self.rx.append(byte)
        if self.rx_length is not None:
            # format byte + target + source + data + checksum
            if len(self.rx) >= 4 + self.rx_length:
                self.handle_message()

    def handle_message(self):
        """Validate and process a complete K-Line message."""
        message = bytes(self.rx)
        self.rx = []
        self.rx_length = None
        logging.debug('K-Line received %s', message.hex().upper())
        if len(message) < 4:
            return
        checksum = sum(message[:-1]) & 0xFF
        if checksum != message[-1]:
            logging.debug('K-Line checksum error (expected %02X, got %02X)',
                          checksum, message[-1])
            return
        target, source = message[1], message[2]
        data = message[3:-1]
        if not data:
            return
        if target not in (KLINE_TARGET_ANY, 0x11, KLINE_TESTER):
            logging.debug('K-Line message not addressed to the ECU (target '
                          '0x%02X)', target)
            return
        self.answer(source, target, data)

    def answer(self, tester, ecu, data):
        """
        Answer an OBD-II request received from the K-Line.

        :param tester: tester address (source of the request)
        :param ecu: ECU address (target of the request)
        :param data: request bytes (e.g. b'\\x01\\x00')
        """
        cmd = data.hex().upper()
        logging.debug('K-Line request %s', repr(cmd))
        if cmd.startswith('81'):  # Start Communication
            payload = bytearray.fromhex(START_COMMUNICATION.replace(' ', ''))
        else:
            try:
                self.emulator.counters['cmd_set_header'] = '7E0'
                # The communication protocol is fixed (K-Line): do not
                # simulate the ELM327 protocol search ("SEARCHING...")
                self.emulator.counters['cmd_try_proto'] = 3
                _, _, response = self.emulator.handle_request(
                    cmd, do_write=False)
            except Exception as e:
                logging.error('Error while processing request %s: %s',
                              repr(cmd), e, exc_info=True)
                return
            if not response:
                logging.debug('K-Line no answer for request %s', repr(cmd))
                return
            payload = self.extract_payload(response, cmd)
        if not payload:
            return
        if len(payload) > 0x3F:
            logging.warning('K-Line answer too long (%d bytes); it is '
                            'truncated', len(payload))
            payload = payload[:0x3F]
        # The response addresses the tester (target) and comes from the ECU
        # (source), i.e. target and source of the request are swapped
        self.send_message(tester, ecu, payload)

    def extract_payload(self, response, cmd):
        """
        Extract the OBD-II payload (without the ISO-TP protocol byte) from the
        response string computed by handle_request().

        :param response: response string returned by handle_request()
        :param cmd: request (hex string)
        :return: payload as bytearray
        """
        frames = []
        for _header, size, data in FRAME_RE.findall(response):
            data = re.sub(r'[^0-9A-Fa-f]', '', data)
            frames.append([int(size, 16)] +
                          [int(data[i:i + 2], 16)
                           for i in range(0, len(data) - 1, 2)])
        if not frames:
            # The answer can be built with the <pos_answer>/<answer> tags:
            # render it with the ELM327 formatter (headers on) and parse the
            # resulting frames
            self.emulator.counters['cmd_use_header'] = True
            try:
                text = self.emulator.handle_response(
                    response, do_write=False, request_header='7E0',
                    request_data=cmd) or ''
            except Exception as e:
                logging.error('Error while rendering the answer of %s: %s',
                              repr(cmd), e, exc_info=True)
                return bytearray()
            for line in text.replace('\r', '\n').split('\n'):
                fields = re.sub(r'[^0-9A-Fa-f ]', ' ', line.upper()).split()
                if len(fields) < 2 or len(fields[0]) not in (3, 8):
                    continue
                try:
                    frames.append([int(x, 16) for x in fields[1:]])
                except ValueError:
                    continue
        if not frames:
            return bytearray()
        # ISO-TP: single frame (PCI = length) or first/consecutive frames
        payload = bytearray()
        for frame in frames:
            if not frame:
                continue
            if frame[0] & 0xF0 == 0x10:  # first frame: 10 <length> <data>
                payload += bytes(frame[2:])
            elif frame[0] & 0xF0 == 0x20:  # consecutive frame: 2N <data>
                payload += bytes(frame[1:])
            else:  # single frame: <length> <data>
                payload += bytes(frame[1:])
        return payload

    def send_message(self, target, source, data):
        """
        Send an ISO 14230 (KWP2000) message to the K-Line.

        :param target: target address (the tester)
        :param source: source address (the ECU)
        :param data: list of data bytes
        """
        message = bytearray([0x80 | (len(data) & 0x3F), target, source])
        message += bytes(data)
        message.append(sum(message) & 0xFF)
        logging.debug('K-Line send %s', message.hex().upper())
        self.write(bytes(message))
