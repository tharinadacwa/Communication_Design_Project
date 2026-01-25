#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# Author: User
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import blocks
from gnuradio import blocks, gr
from gnuradio import digital
from gnuradio import filter
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import gr, pdu
from gnuradio import soapy
from gnuradio import zeromq
import sip
import srnew_epy_block_12 as epy_block_12  # embedded python block
import srnew_epy_block_13 as epy_block_13  # embedded python block
import srnew_epy_block_14 as epy_block_14  # embedded python block
import srnew_epy_block_3_3 as epy_block_3_3  # embedded python block
import srnew_epy_block_7 as epy_block_7  # embedded python block
import threading



class srnew(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Not titled yet")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "srnew")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 4
        self.qpsk = qpsk = digital.constellation_rect([0.707+0.707j, -0.707+0.707j, -0.707-0.707j, 0.707-0.707j], [0, 1, 2, 3],
        4, 2, 2, 1, 1).base()
        self.nfilts = nfilts = 32
        self.access_key = access_key = '11100001010110101110100010010011'
        self.variable_header_format_default_0_0 = variable_header_format_default_0_0 = digital.header_format_default("010101010111000100",2, 2)
        self.variable_header_format_default_0 = variable_header_format_default_0 = digital.header_format_default("010101010111000100",2, 2)
        self.variable_adaptive_algorithm_0_0 = variable_adaptive_algorithm_0_0 = digital.adaptive_algorithm_cma( qpsk, .0001, 4).base()
        self.variable_adaptive_algorithm_0 = variable_adaptive_algorithm_0 = digital.adaptive_algorithm_cma( qpsk, .0001, 4).base()
        self.time_offset = time_offset = 1.0005
        self.thresh_1 = thresh_1 = 1
        self.thresh_0 = thresh_0 = 1
        self.thresh = thresh = 1
        self.samp_rate = samp_rate = 1e6
        self.rrc_taps_0 = rrc_taps_0 = firdes.root_raised_cosine(nfilts, nfilts, 1.0/float(sps), 0.35, 11*sps*nfilts)
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(nfilts, nfilts, 1.0/float(sps), 0.35, 11*sps*nfilts)
        self.phase_bw_0 = phase_bw_0 = 50e-3
        self.phase_bw = phase_bw = 0.0628
        self.noise_volt = noise_volt = 0.3
        self.nfilts_0 = nfilts_0 = 32
        self.hdr_format_0 = hdr_format_0 = digital.header_format_default(access_key, 0)
        self.hdr_format = hdr_format = digital.header_format_default(access_key, 0)
        self.freq_offset = freq_offset = 0.025
        self.freq2_0 = freq2_0 = 5e9
        self.freq2 = freq2 = 2.4e9
        self.freq1_0 = freq1_0 = 2.4e9
        self.freq1 = freq1 = 5e9
        self.excess_bw = excess_bw = 0.35
        self.equalizer = equalizer = 30
        self.delay = delay = 50
        self.access_key_0 = access_key_0 = '11100001010110101110100010010011'

        ##################################################
        # Blocks
        ##################################################

        self._equalizer_range = qtgui.Range(15, 100, 1, 30, 200)
        self._equalizer_win = qtgui.RangeWidget(self._equalizer_range, self.set_equalizer, "'equalizer'", "counter_slider", int, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._equalizer_win)
        self.zeromq_sub_source_0 = zeromq.sub_source(gr.sizeof_gr_complex, 1, 'tcp://127.0.0.1:5556', 100, False, (-1), '', False)
        self.zeromq_pub_sink_0_0 = zeromq.pub_sink(gr.sizeof_gr_complex, 1, 'tcp://127.0.0.1:5556', 100, False, (-1), '', True, True)
        self._time_offset_range = qtgui.Range(0.999, 1.001, 0.0001, 1.0005, 200)
        self._time_offset_win = qtgui.RangeWidget(self._time_offset_range, self.set_time_offset, "Channel: Timing Offset", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._time_offset_win, 0, 1, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.soapy_bladerf_source_0_0 = None
        dev = 'driver=bladerf'
        stream_args = ''
        tune_args = ['']
        settings = ['']

        self.soapy_bladerf_source_0_0 = soapy.source(dev, "fc32", 1, 'bladerf=0',
                                  stream_args, tune_args, settings)
        self.soapy_bladerf_source_0_0.set_sample_rate(0, samp_rate)
        self.soapy_bladerf_source_0_0.set_bandwidth(0, 1.5e6)
        self.soapy_bladerf_source_0_0.set_frequency(0, freq1_0)
        self.soapy_bladerf_source_0_0.set_frequency_correction(0, 0)
        self.soapy_bladerf_source_0_0.set_gain(0, min(max(30.0, -1.0), 60.0))
        self.soapy_bladerf_sink_0 = None
        dev = 'driver=bladerf'
        stream_args = ''
        tune_args = ['']
        settings = ['']

        self.soapy_bladerf_sink_0 = soapy.sink(dev, "fc32", 1, 'bladerf=0',
                                  stream_args, tune_args, settings)
        self.soapy_bladerf_sink_0.set_sample_rate(0, samp_rate)
        self.soapy_bladerf_sink_0.set_bandwidth(0, 1.5e6)
        self.soapy_bladerf_sink_0.set_frequency(0, freq1_0)
        self.soapy_bladerf_sink_0.set_frequency_correction(0, 0)
        self.soapy_bladerf_sink_0.set_gain(0, min(max(50, 17.0), 73.0))
        self.qtgui_time_sink_x_1 = qtgui.time_sink_f(
            20, #size
            samp_rate, #samp_rate
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_1.set_update_time(0.10)
        self.qtgui_time_sink_x_1.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_1.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_1.enable_tags(True)
        self.qtgui_time_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_1.enable_autoscale(False)
        self.qtgui_time_sink_x_1.enable_grid(False)
        self.qtgui_time_sink_x_1.enable_axis_labels(True)
        self.qtgui_time_sink_x_1.enable_control_panel(False)
        self.qtgui_time_sink_x_1.enable_stem_plot(False)


        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_1.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_1.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_1.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_1.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_1.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_1_win = sip.wrapinstance(self.qtgui_time_sink_x_1.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_1_win, 2, 0, 1, 2)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_const_sink_x_1 = qtgui.const_sink_c(
            1024, #size
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_1.set_update_time(0.10)
        self.qtgui_const_sink_x_1.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_1.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_1.enable_autoscale(False)
        self.qtgui_const_sink_x_1.enable_grid(False)
        self.qtgui_const_sink_x_1.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_1.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_1.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_1.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_1.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_1.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_1_win = sip.wrapinstance(self.qtgui_const_sink_x_1.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_const_sink_x_1_win)
        self.qtgui_const_sink_x_0_1 = qtgui.const_sink_c(
            1024, #size
            '', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0_1.set_update_time(0.10)
        self.qtgui_const_sink_x_0_1.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_0_1.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_0_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0_1.enable_autoscale(False)
        self.qtgui_const_sink_x_0_1.enable_grid(False)
        self.qtgui_const_sink_x_0_1.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
            "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0_1.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0_1.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0_1.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0_1.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0_1.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0_1.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_1_win = sip.wrapinstance(self.qtgui_const_sink_x_0_1.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_const_sink_x_0_1_win, 3, 0, 1, 2)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._phase_bw_0_range = qtgui.Range(10.8e-3, 100.8e-3, 0.5e-3, 50e-3, 200)
        self._phase_bw_0_win = qtgui.RangeWidget(self._phase_bw_0_range, self.set_phase_bw_0, "'phase_bw_0'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._phase_bw_0_win)
        self.pdu_tagged_stream_to_pdu_0_0_0 = pdu.tagged_stream_to_pdu(gr.types.byte_t, 'packet_len')
        self.pdu_tagged_stream_to_pdu_0_0 = pdu.tagged_stream_to_pdu(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0_1 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0_0_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self._noise_volt_range = qtgui.Range(0, 1, 0.01, 0.3, 200)
        self._noise_volt_win = qtgui.RangeWidget(self._noise_volt_range, self.set_noise_volt, "Channel: Noise Voltage", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._noise_volt_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._freq_offset_range = qtgui.Range(-0.1, 0.1, 0.001, 0.025, 200)
        self._freq_offset_win = qtgui.RangeWidget(self._freq_offset_range, self.set_freq_offset, "Channel: Frequency Offset", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._freq_offset_win, 0, 2, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.epy_block_7 = epy_block_7.ChatReceiverInterface(max_packet_size=32)
        self.epy_block_3_3 = epy_block_3_3.blk(address=2, max_packet_size=32)
        self.epy_block_14 = epy_block_14.ChatInterface()
        self.epy_block_13 = epy_block_13.ack_sync_prepender(sync_len_first=10000)
        self.epy_block_12 = epy_block_12.TextToPDU_ARQ(pkt_size=32, src_addr=1, dst_addr=2, sync_burst_bytes=10000, timeout=0.01, retry_limit=60)
        self.digital_symbol_sync_xx_0_0 = digital.symbol_sync_cc(
            digital.TED_SIGNAL_TIMES_SLOPE_ML,
            sps,
            (62.8e-3),
            1,
            1.0,
            1.5,
            2,
            digital.constellation_bpsk().base(),
            digital.IR_PFB_MF,
            32,
            rrc_taps)
        self.digital_symbol_sync_xx_0 = digital.symbol_sync_cc(
            digital.TED_SIGNAL_TIMES_SLOPE_ML,
            sps,
            (62.8e-3),
            1,
            1.0,
            1.5,
            4,
            digital.constellation_bpsk().base(),
            digital.IR_PFB_MF,
            32,
            rrc_taps)
        self.digital_protocol_formatter_async_0_0 = digital.protocol_formatter_async(hdr_format)
        self.digital_protocol_formatter_async_0 = digital.protocol_formatter_async(hdr_format)
        self.digital_map_bb_0_0 = digital.map_bb([0,1,2,3])
        self.digital_map_bb_0 = digital.map_bb([0,1,2,3])
        self.digital_linear_equalizer_0_0 = digital.linear_equalizer(equalizer, 4, variable_adaptive_algorithm_0, True, [ ], 'corr_est')
        self.digital_linear_equalizer_0 = digital.linear_equalizer(15, 2, variable_adaptive_algorithm_0, True, [ ], 'corr_est')
        self.digital_diff_decoder_bb_0_0 = digital.diff_decoder_bb(4, digital.DIFF_DIFFERENTIAL)
        self.digital_diff_decoder_bb_0 = digital.diff_decoder_bb(4, digital.DIFF_DIFFERENTIAL)
        self.digital_crc_check_0_0 = digital.crc_check(32, 0x4C11DB7, 0xFFFFFFFF, 0xFFFFFFFF, True, True, False, True, 0)
        self.digital_crc_check_0 = digital.crc_check(32, 0x4C11DB7, 0xFFFFFFFF, 0xFFFFFFFF, True, True, False, True, 0)
        self.digital_crc_append_0_0 = digital.crc_append(32, 0x4C11DB7, 0xFFFFFFFF, 0xFFFFFFFF, True, True, False, 0)
        self.digital_crc_append_0 = digital.crc_append(32, 0x4C11DB7, 0xFFFFFFFF, 0xFFFFFFFF, True, True, False, 0)
        self.digital_costas_loop_cc_0_0 = digital.costas_loop_cc(phase_bw, 4, False)
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc(phase_bw, 4, False)
        self.digital_correlate_access_code_xx_ts_0_0 = digital.correlate_access_code_bb_ts(access_key,
          2, 'packet_len')
        self.digital_correlate_access_code_xx_ts_0 = digital.correlate_access_code_bb_ts(access_key,
          thresh, 'packet_len')
        self.digital_constellation_modulator_0_0 = digital.generic_mod(
            constellation=qpsk,
            differential=True,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=excess_bw,
            verbose=False,
            log=False,
            truncate=False)
        self.digital_constellation_modulator_0 = digital.generic_mod(
            constellation=qpsk,
            differential=True,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=excess_bw,
            verbose=False,
            log=False,
            truncate=False)
        self.digital_constellation_decoder_cb_0_0 = digital.constellation_decoder_cb(qpsk)
        self.digital_constellation_decoder_cb_0 = digital.constellation_decoder_cb(qpsk)
        self._delay_range = qtgui.Range(0, 200, 1, 50, 200)
        self._delay_win = qtgui.RangeWidget(self._delay_range, self.set_delay, "Delay", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._delay_win, 0, 3, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.blocks_unpack_k_bits_bb_0_0 = blocks.unpack_k_bits_bb(2)
        self.blocks_unpack_k_bits_bb_0 = blocks.unpack_k_bits_bb(2)
        self.blocks_throttle2_0_0_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_tagged_stream_mux_0_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, "packet_len", 0)
        self.blocks_tagged_stream_mux_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, "packet_len", 0)
        self.blocks_repack_bits_bb_1_0_0_0 = blocks.repack_bits_bb(1, 8, "packet_len", False, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_1_0_0 = blocks.repack_bits_bb(1, 8, "packet_len", False, gr.GR_MSB_FIRST)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_cc(0.8)
        self.blocks_message_debug_2 = blocks.message_debug(True, gr.log_levels.info)
        self.blocks_char_to_float_0_0 = blocks.char_to_float(1, 1)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.digital_crc_append_0, 'out'), (self.digital_protocol_formatter_async_0, 'in'))
        self.msg_connect((self.digital_crc_append_0_0, 'out'), (self.digital_protocol_formatter_async_0_0, 'in'))
        self.msg_connect((self.digital_crc_check_0, 'ok'), (self.epy_block_12, 'ack_in'))
        self.msg_connect((self.digital_crc_check_0_0, 'ok'), (self.epy_block_3_3, 'pdus_in'))
        self.msg_connect((self.digital_protocol_formatter_async_0, 'header'), (self.pdu_pdu_to_tagged_stream_0, 'pdus'))
        self.msg_connect((self.digital_protocol_formatter_async_0, 'payload'), (self.pdu_pdu_to_tagged_stream_0_0, 'pdus'))
        self.msg_connect((self.digital_protocol_formatter_async_0_0, 'payload'), (self.pdu_pdu_to_tagged_stream_0_0_0, 'pdus'))
        self.msg_connect((self.digital_protocol_formatter_async_0_0, 'header'), (self.pdu_pdu_to_tagged_stream_0_1, 'pdus'))
        self.msg_connect((self.epy_block_12, 'pdus'), (self.digital_crc_append_0, 'in'))
        self.msg_connect((self.epy_block_12, 'status_out'), (self.epy_block_14, 'status_in'))
        self.msg_connect((self.epy_block_13, 'ack_out'), (self.digital_crc_append_0_0, 'in'))
        self.msg_connect((self.epy_block_14, 'msg_out'), (self.epy_block_12, 'msg_in'))
        self.msg_connect((self.epy_block_3_3, 'ack_packet_out'), (self.blocks_message_debug_2, 'log'))
        self.msg_connect((self.epy_block_3_3, 'ack_packet_out'), (self.epy_block_13, 'ack_in'))
        self.msg_connect((self.epy_block_3_3, 'pdus_out'), (self.epy_block_7, 'pdus_in'))
        self.msg_connect((self.pdu_tagged_stream_to_pdu_0_0, 'pdus'), (self.digital_crc_check_0, 'in'))
        self.msg_connect((self.pdu_tagged_stream_to_pdu_0_0_0, 'pdus'), (self.digital_crc_check_0_0, 'in'))
        self.connect((self.blocks_char_to_float_0_0, 0), (self.qtgui_time_sink_x_1, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.soapy_bladerf_sink_0, 0))
        self.connect((self.blocks_repack_bits_bb_1_0_0, 0), (self.pdu_tagged_stream_to_pdu_0_0, 0))
        self.connect((self.blocks_repack_bits_bb_1_0_0_0, 0), (self.pdu_tagged_stream_to_pdu_0_0_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0, 0), (self.digital_constellation_modulator_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0_0, 0), (self.digital_constellation_modulator_0_0, 0))
        self.connect((self.blocks_throttle2_0_0, 0), (self.digital_symbol_sync_xx_0_0, 0))
        self.connect((self.blocks_throttle2_0_0_0, 0), (self.zeromq_pub_sink_0_0, 0))
        self.connect((self.blocks_unpack_k_bits_bb_0, 0), (self.digital_correlate_access_code_xx_ts_0, 0))
        self.connect((self.blocks_unpack_k_bits_bb_0_0, 0), (self.blocks_char_to_float_0_0, 0))
        self.connect((self.blocks_unpack_k_bits_bb_0_0, 0), (self.digital_correlate_access_code_xx_ts_0_0, 0))
        self.connect((self.digital_constellation_decoder_cb_0, 0), (self.digital_diff_decoder_bb_0, 0))
        self.connect((self.digital_constellation_decoder_cb_0_0, 0), (self.digital_diff_decoder_bb_0_0, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.qtgui_const_sink_x_1, 0))
        self.connect((self.digital_constellation_modulator_0_0, 0), (self.blocks_throttle2_0_0_0, 0))
        self.connect((self.digital_correlate_access_code_xx_ts_0, 0), (self.blocks_repack_bits_bb_1_0_0, 0))
        self.connect((self.digital_correlate_access_code_xx_ts_0_0, 0), (self.blocks_repack_bits_bb_1_0_0_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.digital_constellation_decoder_cb_0, 0))
        self.connect((self.digital_costas_loop_cc_0_0, 0), (self.digital_constellation_decoder_cb_0_0, 0))
        self.connect((self.digital_costas_loop_cc_0_0, 0), (self.qtgui_const_sink_x_0_1, 0))
        self.connect((self.digital_diff_decoder_bb_0, 0), (self.digital_map_bb_0, 0))
        self.connect((self.digital_diff_decoder_bb_0_0, 0), (self.digital_map_bb_0_0, 0))
        self.connect((self.digital_linear_equalizer_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.digital_linear_equalizer_0_0, 0), (self.digital_costas_loop_cc_0_0, 0))
        self.connect((self.digital_map_bb_0, 0), (self.blocks_unpack_k_bits_bb_0, 0))
        self.connect((self.digital_map_bb_0_0, 0), (self.blocks_unpack_k_bits_bb_0_0, 0))
        self.connect((self.digital_symbol_sync_xx_0, 0), (self.digital_linear_equalizer_0_0, 0))
        self.connect((self.digital_symbol_sync_xx_0_0, 0), (self.digital_linear_equalizer_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0, 0), (self.blocks_tagged_stream_mux_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0_0, 0), (self.blocks_tagged_stream_mux_0, 1))
        self.connect((self.pdu_pdu_to_tagged_stream_0_0_0, 0), (self.blocks_tagged_stream_mux_0_0, 1))
        self.connect((self.pdu_pdu_to_tagged_stream_0_1, 0), (self.blocks_tagged_stream_mux_0_0, 0))
        self.connect((self.soapy_bladerf_source_0_0, 0), (self.digital_symbol_sync_xx_0, 0))
        self.connect((self.zeromq_sub_source_0, 0), (self.blocks_throttle2_0_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "srnew")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts, 1.0/float(self.sps), 0.35, 11*self.sps*self.nfilts))
        self.set_rrc_taps_0(firdes.root_raised_cosine(self.nfilts, self.nfilts, 1.0/float(self.sps), 0.35, 11*self.sps*self.nfilts))
        self.digital_symbol_sync_xx_0.set_sps(self.sps)
        self.digital_symbol_sync_xx_0_0.set_sps(self.sps)

    def get_qpsk(self):
        return self.qpsk

    def set_qpsk(self, qpsk):
        self.qpsk = qpsk
        self.digital_constellation_decoder_cb_0.set_constellation(self.qpsk)
        self.digital_constellation_decoder_cb_0_0.set_constellation(self.qpsk)

    def get_nfilts(self):
        return self.nfilts

    def set_nfilts(self, nfilts):
        self.nfilts = nfilts
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts, 1.0/float(self.sps), 0.35, 11*self.sps*self.nfilts))
        self.set_rrc_taps_0(firdes.root_raised_cosine(self.nfilts, self.nfilts, 1.0/float(self.sps), 0.35, 11*self.sps*self.nfilts))

    def get_access_key(self):
        return self.access_key

    def set_access_key(self, access_key):
        self.access_key = access_key
        self.set_hdr_format(digital.header_format_default(self.access_key, 0))
        self.set_hdr_format_0(digital.header_format_default(self.access_key, 0))

    def get_variable_header_format_default_0_0(self):
        return self.variable_header_format_default_0_0

    def set_variable_header_format_default_0_0(self, variable_header_format_default_0_0):
        self.variable_header_format_default_0_0 = variable_header_format_default_0_0

    def get_variable_header_format_default_0(self):
        return self.variable_header_format_default_0

    def set_variable_header_format_default_0(self, variable_header_format_default_0):
        self.variable_header_format_default_0 = variable_header_format_default_0

    def get_variable_adaptive_algorithm_0_0(self):
        return self.variable_adaptive_algorithm_0_0

    def set_variable_adaptive_algorithm_0_0(self, variable_adaptive_algorithm_0_0):
        self.variable_adaptive_algorithm_0_0 = variable_adaptive_algorithm_0_0

    def get_variable_adaptive_algorithm_0(self):
        return self.variable_adaptive_algorithm_0

    def set_variable_adaptive_algorithm_0(self, variable_adaptive_algorithm_0):
        self.variable_adaptive_algorithm_0 = variable_adaptive_algorithm_0

    def get_time_offset(self):
        return self.time_offset

    def set_time_offset(self, time_offset):
        self.time_offset = time_offset

    def get_thresh_1(self):
        return self.thresh_1

    def set_thresh_1(self, thresh_1):
        self.thresh_1 = thresh_1

    def get_thresh_0(self):
        return self.thresh_0

    def set_thresh_0(self, thresh_0):
        self.thresh_0 = thresh_0

    def get_thresh(self):
        return self.thresh

    def set_thresh(self, thresh):
        self.thresh = thresh

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle2_0_0.set_sample_rate(self.samp_rate)
        self.blocks_throttle2_0_0_0.set_sample_rate(self.samp_rate)
        self.qtgui_time_sink_x_1.set_samp_rate(self.samp_rate)
        self.soapy_bladerf_sink_0.set_sample_rate(0, self.samp_rate)
        self.soapy_bladerf_source_0_0.set_sample_rate(0, self.samp_rate)

    def get_rrc_taps_0(self):
        return self.rrc_taps_0

    def set_rrc_taps_0(self, rrc_taps_0):
        self.rrc_taps_0 = rrc_taps_0

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps

    def get_phase_bw_0(self):
        return self.phase_bw_0

    def set_phase_bw_0(self, phase_bw_0):
        self.phase_bw_0 = phase_bw_0

    def get_phase_bw(self):
        return self.phase_bw

    def set_phase_bw(self, phase_bw):
        self.phase_bw = phase_bw
        self.digital_costas_loop_cc_0.set_loop_bandwidth(self.phase_bw)
        self.digital_costas_loop_cc_0_0.set_loop_bandwidth(self.phase_bw)

    def get_noise_volt(self):
        return self.noise_volt

    def set_noise_volt(self, noise_volt):
        self.noise_volt = noise_volt

    def get_nfilts_0(self):
        return self.nfilts_0

    def set_nfilts_0(self, nfilts_0):
        self.nfilts_0 = nfilts_0

    def get_hdr_format_0(self):
        return self.hdr_format_0

    def set_hdr_format_0(self, hdr_format_0):
        self.hdr_format_0 = hdr_format_0

    def get_hdr_format(self):
        return self.hdr_format

    def set_hdr_format(self, hdr_format):
        self.hdr_format = hdr_format

    def get_freq_offset(self):
        return self.freq_offset

    def set_freq_offset(self, freq_offset):
        self.freq_offset = freq_offset

    def get_freq2_0(self):
        return self.freq2_0

    def set_freq2_0(self, freq2_0):
        self.freq2_0 = freq2_0

    def get_freq2(self):
        return self.freq2

    def set_freq2(self, freq2):
        self.freq2 = freq2

    def get_freq1_0(self):
        return self.freq1_0

    def set_freq1_0(self, freq1_0):
        self.freq1_0 = freq1_0
        self.soapy_bladerf_sink_0.set_frequency(0, self.freq1_0)
        self.soapy_bladerf_source_0_0.set_frequency(0, self.freq1_0)

    def get_freq1(self):
        return self.freq1

    def set_freq1(self, freq1):
        self.freq1 = freq1

    def get_excess_bw(self):
        return self.excess_bw

    def set_excess_bw(self, excess_bw):
        self.excess_bw = excess_bw

    def get_equalizer(self):
        return self.equalizer

    def set_equalizer(self, equalizer):
        self.equalizer = equalizer

    def get_delay(self):
        return self.delay

    def set_delay(self, delay):
        self.delay = delay

    def get_access_key_0(self):
        return self.access_key_0

    def set_access_key_0(self, access_key_0):
        self.access_key_0 = access_key_0




def main(top_block_cls=srnew, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
