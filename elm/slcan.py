###########################################################################
# ELM327-emulator
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
#
# SLCAN (Lawicel) CAN interface emulation
###########################################################################

"""
Emulate a CAN interface running the SLCAN firmware (CANable, CANtact, or any
Serial Line CAN adapter), so that the emulator can be connected to the CAN bus
of a diagnostic application instead of using the ELM327 protocol.

The application opens the serial port of the emulated adapter (use a virtual
serial port pair like com0com on Windows, or a pseudo-tty) and exchanges CAN
frames with the SLCAN protocol:

* `t<id><dlc><data>` / `T<id><dlc><data>`: transmit an 11/29 bit CAN frame
  (answered with `z` when the transmission is accepted);
* `V`, `N`, `F`: firmware version, serial number, status flags;
* `S<n>`, `O`, `C`, ...: bitrate and channel configuration (answered with CR).

The frames received from the application are reassembled with the ISO-TP
protocol (ISO 15765-2) and used as OBD-II requests, which are answered with the
configured scenario dictionary; the answer is framed with the ISO-TP protocol
and sent back to the CAN bus as CAN frames (ref. issue #19).
"""

import logging
import re
import time

import serial

SLCAN_BAUDRATE = 115200  # default baud rate of CANable SLCAN devices
SLCAN_VERSION = "1013"  # reported firmware version
SLCAN_SERIAL_NUMBER = "12345"  # reported serial number
SLCAN_DEFAULT_BITRATE = "S6"  # 500 kbaud (byte 6 in the SLCAN mapping)
SLCAN_FC_TIMEOUT = 0.5  # seconds to wait for a flow control frame
SLCAN_MAX_DLC = 8  # bytes of a CAN frame
SLCAN_NO_FRAME = 0x07  # bell character: invalid frame

# ISO-TP (ISO 15765-2) protocol control information (first byte of the data)
ISO_TP_SINGLE_FRAME = 0x00
ISO_TP_FIRST_FRAME = 0x10
ISO_TP_CONSECUTIVE_FRAME = 0x20
ISO_TP_FLOW_CONTROL = 0x30

# <header>7E8</header><size>06</size><data>41 00 BE 3F A8 13</data>
FRAME_RE = re.compile(
    r'<header>\s*([0-9A-Fa-f ]+?)\s*</header>\s*'
    r'<size>\s*([0-9A-Fa-f]+)\s*</size>\s*'
    r'<data>\s*([0-9A-Fa-f ]*?)\s*</data>', re.IGNORECASE)


class SlcanError(Exception):
    """Error while processing the SLCAN protocol."""
    pass


class SlcanServer:
    """
    Emulate a CAN interface with the SLCAN firmware and the ECUs of the
    configured scenario on the related CAN bus.
    """

    def __init__(self, emulator, port, baudrate=SLCAN_BAUDRATE):
        """
        :param emulator: ELM327 emulator instance (ref. Elm.__init__)
        :param port: serial port of the emulated CAN interface
        :param baudrate: serial baud rate of the emulated CAN interface
        """
        self.emulator = emulator
        self.port = port
        self.baudrate = baudrate
        self.fd = None
        self.buffer = ""
        self.channel_open = False
        self.rx_data = []  # ISO-TP receive buffer
        self.rx_id = None  # CAN identifier of the assembled message
        self.rx_length = None  # ISO-TP expected length
        self.tx_queue = []  # pending CAN frames of the answer
        self.awaiting_fc = None  # answer waiting for a flow control frame
        self.fc_deadline = 0  # deadline of the flow control frame
        self.flow_control = None  # flow control frame received from the tester

    def open(self):
        """Open the serial port of the emulated CAN interface."""
        try:
            self.fd = serial.Serial(port=self.port, baudrate=self.baudrate,
                                    timeout=0.05)
        except Exception as e:
            logging.critical('Cannot open the SLCAN port %s: %s', self.port, e)
            return False
        return True

    def close(self):
        """Close the serial port of the emulated CAN interface."""
        if self.fd is not None:
            try:
                self.fd.close()
            except Exception:
                pass
            self.fd = None

    def write(self, data):
        """
        Write a response to the serial port.

        :param data: string to be written (without the trailing CR)
        """
        try:
            self.fd.write((data + "\r").encode())
        except Exception as e:
            logging.debug('SLCAN write error: %s', e)

    def read(self):
        """
        Read the serial port and return the received lines (CR terminated).

        :return: list of received lines
        """
        try:
            waiting = self.fd.in_waiting or 1
            chunk = self.fd.read(waiting)
        except Exception as e:
            logging.debug('SLCAN read error: %s', e)
            return []
        lines = []
        for char in chunk.decode(errors='ignore'):
            if char == '\r':
                if self.buffer.strip():
                    lines.append(self.buffer.strip())
                self.buffer = ""
            else:
                self.buffer += char
        return lines

    def run(self):
        """
        Main loop: process the SLCAN commands and frames received from the
        application until the emulator is terminated.

        :return: True if the CAN interface is closed. False in case of error.
        """
        if not self.open():
            return False
        logging.info('Emulated CAN interface (SLCAN) started on %s', self.port)
        while (self.emulator.threadState != self.emulator.THREAD.STOPPED and
                self.emulator.threadState != self.emulator.THREAD.TERMINATED):
            if self.emulator.threadState == self.emulator.THREAD.PAUSED:
                continue
            for line in self.read():
                self.handle_line(line)
            # A long answer is sent after the flow control frame of the tester
            if self.awaiting_fc is not None and (
                    self.flow_control == self.awaiting_fc or
                    time.time() > self.fc_deadline):
                if self.flow_control is None:
                    logging.debug(
                        'SLCAN: no flow control frame received for %s; '
                        'sending the answer anyway', self.awaiting_fc)
                self.awaiting_fc = None
                self.flow_control = None
                self.send_pending_frames()
        self.close()
        return True

    def handle_line(self, line):
        """
        Process a SLCAN command or frame.

        :param line: received line (without the trailing CR)
        """
        logging.debug('SLCAN received %s', repr(line))
        command = line[0]
        argument = line[1:]
        if command in ('t', 'T'):  # transmit a CAN frame
            self.transmit(argument, extended=command == 'T')
        elif command in ('r', 'R'):  # transmit a remote frame (not supported)
            self.write(chr(SLCAN_NO_FRAME))
        elif command == 'O':
            self.channel_open = True
            self.write('')
        elif command == 'C':
            self.channel_open = False
            self.write('')
        elif command == 'V' or command == 'v':
            self.write('V' + SLCAN_VERSION)
        elif command == 'N':
            self.write('N' + SLCAN_SERIAL_NUMBER)
        elif command == 'F':
            self.write('F00')
        else:
            # Bitrate (S), acceptance code/mask (M/m), UART options (U), auto
            # poll (A), listen only (L/l), timestamp (Z) and every other
            # configuration command are accepted with a plain CR (OK)
            self.write('')

    def transmit(self, argument, extended=False):
        """
        Process a SLCAN transmit (t/T) command.

        :param argument: frame (identifier, DLC and data) without the command
        :param extended: True for 29 bit (extended) CAN identifiers
        """
        identifier_length = 8 if extended else 3
        try:
            can_id = argument[:identifier_length].upper()
            dlc = int(argument[identifier_length:identifier_length + 1], 16)
            if (len(can_id) != identifier_length or dlc > SLCAN_MAX_DLC or
                    len(argument) < identifier_length + 1 + dlc * 2):
                raise SlcanError('invalid frame length')
            data = [int(argument[identifier_length + 1 + i * 2:
                                 identifier_length + 3 + i * 2], 16)
                    for i in range(dlc)]
        except (ValueError, SlcanError) as e:
            logging.warning('Invalid SLCAN frame %s: %s', repr(argument), e)
            self.write(chr(SLCAN_NO_FRAME))
            return
        self.write('z')  # acknowledge the transmitted frame
        try:
            self.process_frame(can_id, data)
        except Exception as e:
            logging.error('Error while processing CAN frame %s: %s',
                          repr(argument), e, exc_info=True)

    def process_frame(self, can_id, data):
        """
        Reassemble the ISO-TP message received from the CAN bus and answer it.

        :param can_id: CAN identifier of the received frame
        :param data: list of received bytes
        """
        if not data:
            return
        if data[0] & 0xF0 == ISO_TP_FLOW_CONTROL:  # 0x30: flow control frame
            logging.debug('SLCAN received flow control from %s', can_id)
            self.flow_control = can_id
            return
        if data[0] & 0xF0 == ISO_TP_CONSECUTIVE_FRAME:  # 0x2N: consecutive
            if self.rx_id is None or can_id != self.rx_id:
                logging.warning('Unexpected ISO-TP consecutive frame from %s',
                                can_id)
                return
            self.rx_data += data[1:]
            if self.rx_length is not None and len(self.rx_data) >= self.rx_length:
                self.answer(self.rx_id, self.rx_data[:self.rx_length])
                self.reset_rx()
            return
        if data[0] & 0xF0 == ISO_TP_FIRST_FRAME:  # 0x1NNN: first frame
            self.rx_id = can_id
            self.rx_length = ((data[0] & 0x0F) << 8) + data[1]
            self.rx_data = data[2:]
            if len(self.rx_data) >= self.rx_length:
                self.answer(self.rx_id, self.rx_data[:self.rx_length])
                self.reset_rx()
            else:
                # Ask the tester to send the following consecutive frames
                self.send_frame(self.rx_id, [0x30, 0x00, 0x00])
            return
        # Single frame: 0x0N
        length = data[0] & 0x0F
        self.answer(can_id, data[1:1 + length])

    def reset_rx(self):
        """Reset the ISO-TP receive buffer."""
        self.rx_data = []
        self.rx_id = None
        self.rx_length = None

    def answer(self, can_id, payload):
        """
        Answer an OBD-II request received from the CAN bus.

        :param can_id: CAN identifier of the request (e.g. 7DF or 7E0)
        :param payload: list of bytes of the request (e.g. [1, 0])
        """
        cmd = ''.join('%02X' % byte for byte in payload)
        logging.debug('SLCAN request %s from %s', repr(cmd), can_id)
        if not cmd:
            return
        self.rx_id = can_id
        try:
            self.emulator.counters['cmd_set_header'] = can_id
            # The communication protocol is fixed (CAN): do not simulate the
            # ELM327 protocol search ("SEARCHING...")
            self.emulator.counters['cmd_try_proto'] = 6
            _, _, response = self.emulator.handle_request(cmd, do_write=False)
        except Exception as e:
            logging.error('Error while processing request %s: %s',
                          repr(cmd), e, exc_info=True)
            return
        if not response:
            logging.debug('SLCAN no answer for request %s', repr(cmd))
            return
        self.tx_queue = []
        for header, size, data in FRAME_RE.findall(response):
            header = re.sub(r'\s+', '', header).upper()
            data = re.sub(r'[^0-9A-Fa-f]', '', data)
            frame = [int(size, 16)]
            frame += [int(data[i:i + 2], 16)
                      for i in range(0, len(data) - 1, 2)]
            self.tx_queue.append((header, frame))
        if not self.tx_queue:
            # The answer can be built with the <pos_answer>/<answer> tags (e.g.
            # modes 09 and UDS services): render it with the ELM327 formatter
            # (headers on, so that the CAN identifiers are included) and parse
            # the rendered CAN frames
            self.tx_queue = self.rendered_frames(response, cmd)
        if self.tx_queue:
            self.send_pending_frames()
        else:
            logging.debug('SLCAN answer without CAN frames: %s',
                          repr(response))

    def rendered_frames(self, response, cmd):
        """
        Frame an answer which is built at response time (by the
        <pos_answer>/<answer> tags) using the ELM327 formatter with headers on.

        :param response: response string returned by handle_request()
        :param cmd: request (hex string)
        :return: list of (can identifier, frame bytes) tuples
        """
        self.emulator.counters['cmd_use_header'] = True
        try:
            text = self.emulator.handle_response(
                response, do_write=False, request_header=self.rx_id or '',
                request_data=cmd) or ''
        except Exception as e:
            logging.error('Error while rendering the answer of %s: %s',
                          repr(cmd), e, exc_info=True)
            return []
        frames = []
        for line in text.replace('\r', '\n').split('\n'):
            fields = re.sub(r'[^0-9A-Fa-f ]', ' ', line.upper()).split()
            if len(fields) < 2 or len(fields[0]) not in (3, 8):
                continue
            try:
                frames.append((fields[0], [int(x, 16) for x in fields[1:]]))
            except ValueError:
                continue
        return frames

    def send_pending_frames(self):
        """
        Send the CAN frames of the pending answer. When the answer includes
        multiple frames, the consecutive frames are sent after the reception
        of the flow control frame of the tester.
        """
        while self.tx_queue:
            header, frame = self.tx_queue.pop(0)
            self.send_frame(header, frame)
            if frame[0] & 0xF0 == ISO_TP_FIRST_FRAME and self.tx_queue:
                # Long answer: wait for the flow control frame of the tester
                self.awaiting_fc = header
                self.fc_deadline = time.time() + SLCAN_FC_TIMEOUT
                return

    def send_frame(self, can_id, data):
        """
        Send a CAN frame to the CAN bus.

        :param can_id: CAN identifier of the frame (e.g. 7E8)
        :param data: list of bytes of the frame (first byte is the ISO-TP PCI)
        """
        data = list(data)
        if len(data) < SLCAN_MAX_DLC:
            data += [0x00] * (SLCAN_MAX_DLC - len(data))
        if len(can_id) <= 3:
            command = 't'
        else:
            command = 'T'
        frame = ''.join('%02X' % byte for byte in data)
        self.write('%s%s%1X%s' % (command, can_id, len(data), frame))
