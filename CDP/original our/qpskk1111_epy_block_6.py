import numpy as np
from gnuradio import gr
from collections import deque

class IdlePacketInjectorExact(gr.sync_block):
    """
    IdlePacketInjectorExact
    - Idle byte (0xAA) is output continuously until a full packet is buffered.
    - Packet format expected in rx stream: 8-byte header (header[5] = payload_len) followed by payload_len bytes.
    - When full packet is available, transmit exactly:
         [header0..7][payload_len][payload_bytes]
      (i.e., transmit the packet exactly as received)
    - Transmission is continuous at the normal flow rate; packets may span multiple work() calls.
    - While transmitting a packet, rx_buf continues to accumulate the next incoming packet.
    """

    def __init__(self, idle_byte=0xAA):
        gr.sync_block.__init__(
            self,
            name="IdlePacketInjectorExact",
            in_sig=[np.uint8],
            out_sig=[np.uint8]
        )

        self.idle_byte = idle_byte & 0xFF

        # rx_buf: collects incoming raw bytes (deque for O(1) pops/appends)
        self.rx_buf = deque()
        # tx_buf: bytes of the packet currently being transmitted (deque)
        self.tx_buf = deque()

        # state helpers
        self.waiting_for_full_packet = True  # True when looking to form next tx_buf from rx_buf

    def _try_make_packet(self):
        """
        If rx_buf contains at least 8 bytes, read header[5] to get payload length,
        and if rx_buf contains the full packet (8 + payload_len), move those bytes
        to tx_buf (only if tx_buf is currently empty so we keep single active tx buffer).
        """
        # Only create a new tx packet if nothing is currently transmitting
        if self.tx_buf:
            return

        # Need at least 6 bytes to read header[5] safely (indexes 0..5)
        if len(self.rx_buf) < 6:
            return

        # Peek header[5] without popping
        # Convert deque to indexing by iterating - deque supports indexing but it's O(n).
        # Access small index directly via tuple() for efficiency when len small
        # but for clarity just use indexing (acceptable because index 5).
        payload_len = self.rx_buf[5]

        total_len = 8 + int(payload_len)  # 8-byte header + payload_len bytes

        # If we have full packet in rx_buf, move it to tx_buf
        if len(self.rx_buf) >= total_len:
            # move the first total_len bytes from rx_buf to tx_buf in order
            for _ in range(total_len):
                self.tx_buf.append(self.rx_buf.popleft())

            # Now tx_buf contains [header0..7, payload...], and will be transmitted
            # We don't set any special flag; presence of tx_buf indicates active transmission

# assume total_len = header_len + payload_len
            #header = [self.rx_buf.popleft() for _ in range(8)]  # first 8 bytes of header
            #payload = [self.rx_buf.popleft() for _ in range(total_len - 8)]  # rest of packet

# insert payload length byte right after header
            #payload_len_byte = total_len - 8
            #self.tx_buf.extend(header)         # header bytes
            #self.tx_buf.append(payload_len)  # length byte
            #self.tx_buf.extend(payload)        # payload bytes
            #print(self.tx_buf)


    def work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]
        n_out = len(out)
        out_index = 0

        # 1) append incoming bytes to rx_buf
        if len(inp) > 0:
            # inp is a numpy array of uint8
            self.rx_buf.extend(int(b) for b in inp.tolist())

        # 2) if no active tx_buf, try to assemble a packet from rx_buf
        # This also ensures back-to-back packets are handled: after finishing one,
        # next will be immediately prepared if rx_buf already contains it.
        self._try_make_packet()

        # 3) fill the output buffer at full rate.
        #    If tx_buf has data -> stream it continuously until empty,
        #    otherwise send idle bytes.
        while out_index < n_out:
            if self.tx_buf:
                # transmit next byte of current packet
                out[out_index] = self.tx_buf.popleft()
                out_index += 1

                # after popping a byte, if tx_buf becomes empty, attempt to prepare next packet
                if not self.tx_buf:
                    # attempt to build the next packet immediately (back-to-back)
                    self._try_make_packet()
                # continue loop
            else:
                # no packet currently being transmitted -> output idle
                out[out_index] = self.idle_byte
                out_index += 1

                # also after sending idle we can check if rx_buf now contains a full packet
                # (useful if rx_buf filled during this work() call)
                # But avoid calling _try_make_packet too often; it's cheap so ok:
                self._try_make_packet()

        return n_out
