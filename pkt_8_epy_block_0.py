import numpy as np
from gnuradio import gr
import pmt
import threading
import time


class blk(gr.sync_block):
    """Reads text from file and outputs as PDU vector periodically"""

    def __init__(self, file_path="", repeat_count=1, period=1.0):
        gr.sync_block.__init__(
            self,
            name='PDU File reader',
            in_sig=None,
            out_sig=None
        )

        # Parameters
        self.file_path = file_path
        self.repeat_count = int(repeat_count)
        self.period = float(period)

        # Register output message port
        self.portName = "out"
        self.message_port_register_out(pmt.intern(self.portName))

        # Load file content once
        self._load_file()

        # Thread control
        self._thread = None
        self._running = False

    def _load_file(self):
        try:
            with open(self.file_path, "r") as f:
                text = f.read().strip()
        except Exception as e:
            text = ""
            print(f"[PDU File reader] Error reading file: {e}")

        # Convert string into byte vector
        u8_vector = np.frombuffer(text.encode("utf-8"), dtype=np.uint8)
        self.pdu = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(u8_vector), u8_vector))

    def _send_loop(self):
        """Background thread to send PDUs periodically"""
        count = 0
        while self._running and (self.repeat_count <= 0 or count < self.repeat_count):
            self.message_port_pub(pmt.intern(self.portName), self.pdu)
            count += 1
            time.sleep(self.period)

    def start(self):
        """Called when flowgraph starts"""
        self._running = True
        self._thread = threading.Thread(target=self._send_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Called when flowgraph stops"""
        self._running = False
        if self._thread is not None:
            self._thread.join()
        return True

    def work(self, input_items, output_items):
        # No streaming work — PDUs only
        return 0
