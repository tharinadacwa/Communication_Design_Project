import pmt
from gnuradio import gr
import os

class blk(gr.basic_block):
    # USE r"" for Windows paths to handle backslashes correctly
    def __init__(self, file_path=r"C:\Users\Subodha\Desktop\CDP\output.txt", append=False):
        gr.basic_block.__init__(
            self,
            name="pdu_file_writer",
            in_sig=[],
            out_sig=[]
        )

        self.file_path = file_path
        self.append = append

        self.message_port_register_in(pmt.intern("pdus"))
        self.set_msg_handler(pmt.intern("pdus"), self.handle_pdu)

        # LOGIC FIX: Only wipe the file if we are NOT in append mode
        if not self.append:
            # "wb" opens for writing and deletes existing content
            try:
                open(self.file_path, "wb").close()
            except Exception as e:
                print(f"Error initializing file: {e}")

    def handle_pdu(self, msg):
        # Extract data from PDU (pair: meta . data)
        # meta = pmt.car(msg) # Metadata (not used here)
        data = pmt.cdr(msg)   # The actual bytes

        if pmt.is_u8vector(data):
            byte_data = bytes(pmt.u8vector_elements(data))

            # ALWAYS use "ab" (Append Binary) here.
            # Why? Because if you use "wb", packet #2 will delete packet #1.
            # We want to add to the file *during* this run.
            try:
                with open(self.file_path, "ab") as f:
                    f.write(byte_data)
                    f.flush() # Ensure data is written to disk immediately
            except Exception as e:
                print(f"Error writing to file: {e}")