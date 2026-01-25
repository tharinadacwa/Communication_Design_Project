import pmt
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self,file_path=r"C:\Users\Subodha\Desktop\CDP\original our\output.txt", append=False):
        gr.basic_block.__init__(
            self,
            name="pdu_file_writer",
            in_sig=[],
            out_sig=[]
        )

        self.file_path = file_path
        self.append = append  # If True, append to file; else overwrite

        self.message_port_register_in(pmt.intern("pdus"))
        self.set_msg_handler(pmt.intern("pdus"), self.handle_pdu)

        # If overwrite mode, clear the file at the start

        open(self.file_path, "wb").close()

    def handle_pdu(self, msg):
        meta = pmt.car(msg)
        data = pmt.cdr(msg)

        if pmt.is_u8vector(data):
            byte_data = bytes(pmt.u8vector_elements(data))

            # Determine file mode: append ("ab") or write ("wb")
            mode = "ab" if self.append else "ab"  # still append for multiple PDUs in same run

            with open(self.file_path, mode) as f:
                f.write(byte_data)
