import pmt
import threading
import time
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self, file_path="", interval=1.0, repeat_count=0):
        gr.basic_block.__init__(
            self,
            name="File to PDU (repeated N times)",
            in_sig=[],
            out_sig=[]
        )

        self.file_path = file_path
        self.interval = float(interval)
        self.repeat_count = int(repeat_count)
        self.message_port_register_out(pmt.intern("pdus"))

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._send_loop)
        self._thread.daemon = True

    def start(self):
        self._stop_event.clear()
        self._thread.start()
        return super().start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        return super().stop()

    def _send_loop(self):
        count = 0
        while not self._stop_event.is_set():
            # If repeat_count is positive, stop after sending that many times
            if self.repeat_count > 0 and count >= self.repeat_count:
                break

            try:
                with open(self.file_path, 'rb') as f:
                    data = f.read()

                if data:
                    payload = pmt.init_u8vector(len(data), bytearray(data))
                    meta = pmt.make_dict()
                    pdu = pmt.cons(meta, payload)
                    self.message_port_pub(pmt.intern("pdus"), pdu)
                    count += 1
            except Exception as e:
                print("[FileToPDU] Error reading file:", str(e))
                break  # Don't loop forever on failure

            time.sleep(self.interval)
