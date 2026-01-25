import numpy as np
from gnuradio import gr
import pmt


class blk(gr.basic_block):
    """PDU to File (save first received text only)"""

    def __init__(self, file_path="output.txt"):
        gr.basic_block.__init__(
            self,
            name='PDU to File Writer',
            in_sig=None,
            out_sig=None
        )

        # Parameters
        self.file_path = file_path
        self.saved = False   # flag to only save the first PDU

        # Register input message port
        self.portName = "in"
        self.message_port_register_in(pmt.intern(self.portName))
        self.set_msg_handler(pmt.intern(self.portName), self.handle_msg)

    def handle_msg(self, msg):
        # Ignore if already saved
        if self.saved:
            return

        try:
            # Extract the u8vector from the PDU
            vector = pmt.u8vector_elements(pmt.cdr(msg))
            text = bytes(vector).decode("utf-8")

            # Save to file
            with open(self.file_path, "w") as f:
                f.write(text)

            print(f"[PDU to File Writer] Saved text to {self.file_path}")
            self.saved = True  # prevent further saves
        except Exception as e:
            print(f"[PDU to File Writer] Error: {e}")
