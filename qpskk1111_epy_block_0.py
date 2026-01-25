import pmt
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(
            self,
            name="pdu_file_writer",
            in_sig=[],
            out_sig=[]
        )

        self.message_port_register_in(pmt.intern("pdus"))
        self.set_msg_handler(pmt.intern("pdus"), self.handle_pdu)

    def handle_pdu(self, msg):
        meta = pmt.car(msg)
        data = pmt.cdr(msg)

        if pmt.is_u8vector(data):
            byte_data = bytes(pmt.u8vector_elements(data))
            with open("C:/Users/Subodha/Desktop/3rd Semester/CDP/output.txt", "wb") as f:
                f.write(byte_data)
                f.write(b"\n")  # optional: newline between messages
