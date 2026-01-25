import pmt
from gnuradio import gr
from PyQt5 import QtWidgets, QtCore
import sys
import datetime

class MessageBubble(QtWidgets.QWidget):
    def __init__(self, text, time_str, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)

        frame = QtWidgets.QFrame()
        frame_layout = QtWidgets.QVBoxLayout(frame)

        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #CCCCCC;
            }
        """)

        lbl_text = QtWidgets.QLabel(text)
        lbl_text.setWordWrap(True)
        lbl_text.setStyleSheet("font-size: 14px; color: black;")
        frame_layout.addWidget(lbl_text)

        meta = QtWidgets.QHBoxLayout()
        lbl_time = QtWidgets.QLabel(time_str)
        lbl_time.setStyleSheet("font-size: 10px; color: #555;")
        meta.addStretch()
        meta.addWidget(lbl_time)
        frame_layout.addLayout(meta)

        layout.addWidget(frame)
        layout.addStretch()
        self.setLayout(layout)


class ChatReceiverWindow(QtWidgets.QWidget):
    new_message_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Received Messages")
        self.resize(400, 600)
        self.setStyleSheet("background-color: #E6EBEF;")

        layout = QtWidgets.QVBoxLayout()
        self.chat_area = QtWidgets.QListWidget()
        self.chat_area.setStyleSheet("border: none; background-color: transparent;")
        layout.addWidget(self.chat_area)
        self.setLayout(layout)

        self.new_message_signal.connect(self.display)

    def display(self, text):
        time_str = datetime.datetime.now().strftime("%H:%M")
        bubble = MessageBubble(text, time_str)
        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(bubble.sizeHint())
        self.chat_area.addItem(item)
        self.chat_area.setItemWidget(item, bubble)
        self.chat_area.scrollToBottom()


class ChatReceiverInterface(gr.basic_block):

    def __init__(self, max_packet_size=32):
        gr.basic_block.__init__(
            self,
            name="Chat Receiver Interface GUI",
            in_sig=None,
            out_sig=None)

        self.max_packet_size = int(max_packet_size)

        self.message_port_register_in(pmt.intern("pdus_in"))
        self.set_msg_handler(pmt.intern("pdus_in"), self.handle_pdu)

        self.qapp = QtWidgets.QApplication.instance()
        if not self.qapp:
            self.qapp = QtWidgets.QApplication(sys.argv)

        self.gui = ChatReceiverWindow()
        self.gui.show()

        self.buffer = {}   # pkt_num → pdu

    def handle_pdu(self, pdu):
        meta = pmt.car(pdu)
        vec = pmt.cdr(pdu)

        if not pmt.is_u8vector(vec):
            return

        data = list(pmt.u8vector_elements(vec))
        pkt_len = len(data)
        pkt_num = data[0]

        print(f"[RX] Received PDU (len={pkt_len}) pkt={pkt_num}")

        # ------------------------------------------------------
        # TERMINATION PACKET
        # ------------------------------------------------------
        if pkt_len == self.max_packet_size - 1:
            print("[RX] Termination packet detected.")

            full_bytes = b""

            for k in sorted(self.buffer.keys()):
                p = self.buffer[k]
                raw = list(pmt.u8vector_elements(pmt.cdr(p)))
                full_bytes += bytes(raw[1:])  # skip pkt_num

            try:
                decoded = full_bytes.decode("utf-8")
            except:
                decoded = "<Decode Error>"

            # ----------- ADDED CONDITION HERE --------------
            if decoded.strip() == "":
                print("[RX] Empty message. Not displaying.")
            else:
                self.gui.new_message_signal.emit(decoded)
                print("[RX] Assembled message:", decoded)
            # ------------------------------------------------

            self.buffer.clear()
            return

        # ------------------------------------------
        # NORMAL PACKET
        # ------------------------------------------
        self.buffer[pkt_num] = pdu
        print(f"[RX] Stored packet {pkt_num}")

    def stop(self):
        self.gui.close()
        return super().stop()

