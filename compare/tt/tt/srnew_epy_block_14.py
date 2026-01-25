#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rewritten GUI + GNU Radio sync_block.

This preserves the exact algorithm, message ports, and flowgraph from your original
snippet:

  - Outgoing message port:  "msg_out"  (publishes text as a PMT symbol)
  - Incoming status port:   "status_in" (expects PMT symbol: "success", "fail", "pending")
  - GUI behavior: Telegram-style bubbles, "Sending..." state, ✓ Sent / Failed indications.
  - Thread-safe GUI updates via Qt signals.

The code below follows the structure and style of the sample you provided
(e.g. dedicated GuiSignaler QObject, clearer separation of responsibilities),
but implements the same message flow & logic you asked to keep unchanged.
"""

from gnuradio import gr
from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import pmt
import datetime


# ---------------------------
# Helper: Wallpaper / Scroll
# ---------------------------
class WallpaperScrollArea(QtWidgets.QScrollArea):
    """Optional background-capable scroll area (keeps UI style from sample)."""
    def __init__(self, bg_image: str = "", parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._pix = QtGui.QPixmap(bg_image) if bg_image else None

    def paintEvent(self, event):
        if self._pix and not self._pix.isNull():
            painter = QtGui.QPainter(self.viewport())
            scaled = self._pix.scaled(self.viewport().size(),
                                      QtCore.Qt.KeepAspectRatioByExpanding,
                                      QtCore.Qt.SmoothTransformation)
            x = (self.viewport().width() - scaled.width()) // 2
            y = (self.viewport().height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        super().paintEvent(event)


# ---------------------------
# GUI: Message bubble widget
# ---------------------------
class MessageBubble(QtWidgets.QWidget):
    """A compact, reusable message bubble widget with a status label."""
    def __init__(self, text: str, time_str: str, status: str = "Waiting", parent=None):
        super().__init__(parent)
        self._build_ui(text, time_str, status)

    def _build_ui(self, text, time_str, status):
        h = QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(0, 5, 0, 5)

        self.frame = QtWidgets.QFrame()
        v = QtWidgets.QVBoxLayout(self.frame)
        v.setContentsMargins(8, 6, 8, 6)

        self.frame.setStyleSheet("""
            QFrame { background-color: #EEFFDD; border-radius: 10px; border: 1px solid #CCDDCC; }
        """)

        self.lbl_text = QtWidgets.QLabel(text)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setStyleSheet("font-size:14px; color: #000; border: none;")
        v.addWidget(self.lbl_text)

        meta = QtWidgets.QHBoxLayout()
        meta.addStretch()

        self.lbl_time = QtWidgets.QLabel(time_str)
        self.lbl_time.setStyleSheet("font-size:10px; color:#555; border: none;")
        meta.addWidget(self.lbl_time)

        self.lbl_status = QtWidgets.QLabel(status)
        self.lbl_status.setStyleSheet("font-size:10px; color: gray; font-weight: bold; border:none;")
        meta.addWidget(self.lbl_status)

        v.addLayout(meta)

        h.addStretch()
        h.addWidget(self.frame)
        self.setLayout(h)

    def set_status(self, status_text: str, color: str):
        """Update status label and bubble color for failure/sent states."""
        self.lbl_status.setText(status_text)
        self.lbl_status.setStyleSheet(f"font-size:10px; font-weight:bold; color: {color}; border: none;")
        if status_text == "Failed":
            self.frame.setStyleSheet("QFrame { background-color: #FFDDDD; border-radius: 10px; border: 1px solid #DDAAAA; }")
        elif "Sent" in status_text or "✓" in status_text:
            self.frame.setStyleSheet("QFrame { background-color: #EEFFDD; border-radius: 10px; border: 1px solid #CCDDCC; }")


# ---------------------------
# GUI: Main chat window
# ---------------------------
class ChatWindow(QtWidgets.QWidget):
    """
    A simplified Telegram-style chat window.
    Emits:
      - send_signal(str) : when user hits send (payload text)
    Provides:
      - status_signal(str, str) : slot used internally for thread-safe status updates (text, color)
    """
    send_signal = QtCore.pyqtSignal(str)
    status_signal = QtCore.pyqtSignal(str, str)  # (status_text, color)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Secure Radio Chat")
        self.resize(420, 620)
        self.setStyleSheet("background-color: #E6EBEF;")
        self._current_bubble = None
        self._build_ui()

        # connect internal status update signal to slot
        self.status_signal.connect(self._update_last_status)

    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(6)

        self.chat_area = QtWidgets.QListWidget()
        self.chat_area.setStyleSheet("border: none; background-color: transparent;")
        self.chat_area.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.chat_area.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        main.addWidget(self.chat_area, stretch=1)

        input_container = QtWidgets.QWidget()
        input_container.setStyleSheet("background-color: white; border-top: 1px solid #DDD;")
        inlay = QtWidgets.QHBoxLayout(input_container)
        inlay.setContentsMargins(8, 8, 8, 8)

        self.text_input = QtWidgets.QLineEdit()
        self.text_input.setPlaceholderText("Write a message...")
        self.text_input.returnPressed.connect(self._on_send_clicked)
        inlay.addWidget(self.text_input)

        self.btn_send = QtWidgets.QPushButton("➤")
        self.btn_send.setFixedSize(40, 40)
        self.btn_send.setStyleSheet("background-color: #3390EC; color: white; border-radius: 20px; font-weight: bold;")
        self.btn_send.clicked.connect(self._on_send_clicked)
        inlay.addWidget(self.btn_send)

        main.addWidget(input_container)
        self.setLayout(main)

    def _on_send_clicked(self):
        text = self.text_input.text().strip()
        if not text:
            return
        self.text_input.clear()
        ts = datetime.datetime.now().strftime("%H:%M")
        bubble = MessageBubble(text, ts, status="Sending...")
        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(bubble.sizeHint())
        self.chat_area.addItem(item)
        self.chat_area.setItemWidget(item, bubble)
        self.chat_area.scrollToBottom()
        self._current_bubble = bubble

        # emit text to be published to GNU Radio block
        self.send_signal.emit(text)

    def _update_last_status(self, status_text: str, color: str):
        if self._current_bubble:
            self._current_bubble.set_status(status_text, color)


# ---------------------------
# Qt-to-GR Signaler
# ---------------------------
class GuiSignaler(QtCore.QObject):
    """
    Small QObject wrapper so the GNU Radio block can emit signals to the Qt GUI
    from within message handlers safely.
    """
    status_update = QtCore.pyqtSignal(str, str)   # (status_text, color)
    debug_log = QtCore.pyqtSignal(str)            # debug console log (optional)


# ---------------------------
# GNU Radio sync block
# ---------------------------
class ChatInterface(gr.sync_block):
    """
    GNU Radio sync_block that hosts the Qt GUI and bridges messages.

    Ports:
      - Registers OUT:  'msg_out'  (publishes outgoing payloads as PMT symbol)
      - Registers IN:   'status_in' (status updates from other GR blocks; expected PMT symbol)
    """
    def __init__(self):
        gr.sync_block.__init__(self,
                               name="Chat Interface (Telegram Style)",
                               in_sig=None,
                               out_sig=None)

        # Register message ports (exact names required by your flowgraph)
        self.message_port_register_out(pmt.intern("msg_out"))
        self.message_port_register_in(pmt.intern("status_in"))

        # Set handler for status messages coming into this block
        self.set_msg_handler(pmt.intern("status_in"), self._handle_status_msg)

        # Qt application
        self._qapp = QtWidgets.QApplication.instance()
        if not self._qapp:
            self._qapp = QtWidgets.QApplication(sys.argv)

        # GUI + signaler (bridge)
        self._signaler = GuiSignaler()
        self._gui = ChatWindow()
        # connect signals: from GR -> GUI via Qt signals
        self._signaler.status_update.connect(self._gui.status_signal)

        # connect GUI send -> GR publishing method
        self._gui.send_signal.connect(self._publish_outgoing)

        # show GUI
        self._gui.show()

    # ---------------------------
    # Message handlers (incoming)
    # ---------------------------
    def _handle_status_msg(self, pmt_msg):
        """
        Called when a status message arrives on 'status_in'.
        We expect a PMT symbol with one of: "success", "fail", "pending".
        Map them to GUI-friendly statuses identically to original behavior.
        """
        try:
            if pmt.is_symbol(pmt_msg):
                status_str = pmt.symbol_to_string(pmt_msg)
            else:
                # defensive: try converting other PMT types
                status_str = pmt.to_python(pmt_msg) if hasattr(pmt, "to_python") else str(pmt_msg)

            # Debug print to console for visibility (keeps same debug behavior)
            print(f"[GUI] Status received: '{status_str}'")

            if status_str == "success":
                # "✓ Sent" in blue
                self._signaler.status_update.emit("✓ Sent", "#3390EC")
            elif status_str == "fail":
                self._signaler.status_update.emit("Failed", "red")
            elif status_str == "pending":
                # original ignored 'pending' (no UI update)
                pass
            else:
                # Unknown status -> log/debug but do not crash
                print(f"[GUI] Unknown status symbol: {status_str}")

        except Exception as e:
            print(f"[GUI] Error handling status: {e}")

    # ---------------------------
    # Outgoing publish (from GUI)
    # ---------------------------
    def _publish_outgoing(self, text: str):
        """
        Publish the outgoing text as a PMT symbol on 'msg_out' (same as original).
        """
        try:
            self.message_port_pub(pmt.intern("msg_out"), pmt.string_to_symbol(text))
        except Exception as e:
            print(f"[GUI] Error publishing outgoing message: {e}")

    # ---------------------------
    # Clean shutdown
    # ---------------------------
    def stop(self):
        """
        Close the GUI on flowgraph stop (keeps behavior from original).
        """
        try:
            if self._gui:
                # Close the window (thread-safe via Qt)
                QtCore.QMetaObject.invokeMethod(self._gui, "close", QtCore.Qt.QueuedConnection)
        except Exception as e:
            print(f"[GUI] Error during stop: {e}")
        return super().stop()
