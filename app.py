import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit, QRadioButton, QGroupBox, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QSlider

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import numpy as np

from transmissor import Transmissor
from receptor import Receiver as Receptor


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize server for Receptor
        self.receptor = Receptor()
        self.receptor.start_server()

        # Main layout - horizontal layout
        self.main_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()  # For Transmissor and Modulação
        self.right_layout = QVBoxLayout()  # For Receptor and Enlace

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        # Font for larger labels
        large_font = QFont()
        large_font.setPointSize(20)

        # Create Transmissor layout
        self.create_transmissor_layout(large_font)

        # Create Modulador layout
        self.create_modulator_layout(large_font)

        # Add left_layout (Transmissor and Modulador) to main_layout
        self.main_layout.addLayout(self.left_layout, 1)

        # Create Receptor layout
        self.create_receptor_layout(large_font)

        # Create Enlace layout
        self.create_enlace_layout()

        # Add right_layout (Receptor and Enlace) to main_layout
        self.main_layout.addLayout(self.right_layout, 1)

        # Connect button signal
        self.transmit_button.clicked.connect(self.transmit_and_receive)

        # Set window to full-screen
        self.showMaximized()

    def create_transmissor_layout(self, large_font):
        # Transmissor layout
        self.transmissor_layout = QVBoxLayout()
        self.transmissor_label = QLabel("Transmissor")
        self.transmissor_label.setFont(large_font)
        self.transmissor_label.setAlignment(Qt.AlignCenter)
        self.transmissor_layout.addWidget(self.transmissor_label)

        # Create Transmissor layout - vertical
        self.transmissor_layout = QVBoxLayout()
        self.transmissor_label = QLabel("Transmissor")
        self.transmissor_label.setFont(large_font)
        self.transmissor_label.setAlignment(Qt.AlignCenter)
        self.transmissor_layout.addWidget(self.transmissor_label)

        # QLineEdit for input with placeholder and padding
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(
            "Enter your text here")  # Set placeholder text
        self.input_field.setStyleSheet(
            "QLineEdit { padding: 10px; }")  # Set padding
        self.transmissor_layout.addWidget(self.input_field)

        # Radio buttons for encoding selection
        self.radio_group_box = QGroupBox()
        self.radio_layout = QHBoxLayout()
        self.radio_nrz = QRadioButton("NRZ")
        self.radio_manchester = QRadioButton("Manchester")
        self.radio_bipolar = QRadioButton("Bipolar")
        self.radio_nrz.setChecked(True)  # Set default selection
        self.radio_layout.addWidget(self.radio_nrz)
        self.radio_layout.addWidget(self.radio_manchester)
        self.radio_layout.addWidget(self.radio_bipolar)
        self.radio_group_box.setLayout(self.radio_layout)
        self.transmissor_layout.addWidget(self.radio_group_box)

        self.transmit_button = QPushButton("Transmitir")
        self.transmissor_layout.addWidget(self.transmit_button)

        # TextEdit for Transmissor (if needed for displaying any information)
        self.transmissor_text_edit = QTextEdit()
        # Make it read-only if it's just for display
        self.transmissor_text_edit.setReadOnly(True)
        self.transmissor_layout.addWidget(self.transmissor_text_edit)

        # Create a Matplotlib figure and FigureCanvas
        self.figure = Figure(facecolor='lightgray')
        self.canvas = FigureCanvas(self.figure)
        self.transmissor_layout.addWidget(self.canvas)

        # Slider for the first chart
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.transmissor_layout.addWidget(self.slider)
        self.slider.valueChanged.connect(self.update_plot)

        # Add Transmissor layout to left_layout with 50% height
        self.left_layout.addLayout(self.transmissor_layout, 1)

    def create_modulator_layout(self, large_font):
        # Modulador layout
        self.modulator_layout = QVBoxLayout()
        modulator_label = QLabel("Modulador")
        modulator_label.setFont(large_font)
        modulator_label.setAlignment(Qt.AlignCenter)
        self.modulator_layout.addWidget(modulator_label)

        # Radio buttons for modulator selection
        modulator_radio_group_box = QGroupBox()
        modulator_radio_layout = QHBoxLayout()
        self.radio_ask = QRadioButton("ASK")
        self.radio_fsk = QRadioButton("FSK")
        self.radio_8qam = QRadioButton("8-QAM")
        self.radio_ask.setChecked(True)  # Set default selection
        modulator_radio_layout.addWidget(self.radio_ask)
        modulator_radio_layout.addWidget(self.radio_fsk)
        modulator_radio_layout.addWidget(self.radio_8qam)
        modulator_radio_group_box.setLayout(modulator_radio_layout)
        self.modulator_layout.addWidget(modulator_radio_group_box)

        # Chart for Modulator
        self.figure_mod = Figure(facecolor='lightgray')
        self.canvas_mod = FigureCanvas(self.figure_mod)

        self.modulator_layout.addWidget(self.canvas_mod)

        # Slider for the modulated data chart
        self.slider_mod = QSlider(Qt.Horizontal)
        self.slider_mod.setMinimum(0)
        self.modulator_layout.addWidget(self.slider_mod)
        self.slider_mod.valueChanged.connect(self.update_plot_mod)

        # Add Modulador layout to left_layout with 50% height
        self.left_layout.addLayout(self.modulator_layout, 1)

    def create_receptor_layout(self, large_font):
        # Receptor layout
        self.receptor_layout = QVBoxLayout()
        self.receptor_label = QLabel("Receptor")
        self.receptor_label.setFont(large_font)
        self.receptor_label.setAlignment(Qt.AlignCenter)
        self.receptor_layout.addWidget(self.receptor_label)

        # TextEdit for displaying results
        self.results_text_edit = QTextEdit()
        self.results_text_edit.setReadOnly(True)  # Make it read-only
        self.receptor_layout.addWidget(self.results_text_edit)

        # Main Modulador layout - horizontal
        self.modulator_layout = QHBoxLayout()

        # Add Receptor layout to right_layout with 80% height
        self.right_layout.addLayout(self.receptor_layout, 8)

    def create_enlace_layout(self):
        # Enlace layout
        self.enlace_layout = QVBoxLayout()

        # Radio buttons for Enquadramento de dados
        enquadramento_radio_group_box1 = QGroupBox()
        enquadramento_radio_layout = QHBoxLayout()
        enq_label = QLabel("Enquadramento")
        enq_label.setStyleSheet(
            "font-weight: bold; font-size: 14pt;")
        self.radio_enq1 = QRadioButton("Cont. de Caracteres")
        self.radio_enq2 = QRadioButton("Inserção de Bits")
        self.radio_enq3 = QRadioButton("Inserção de Bytes")
        self.radio_enq1.setChecked(True)  # Set default selection
        enquadramento_radio_layout.addWidget(enq_label)
        enquadramento_radio_layout.addWidget(self.radio_enq1)
        enquadramento_radio_layout.addWidget(self.radio_enq2)
        enquadramento_radio_layout.addWidget(self.radio_enq3)
        enquadramento_radio_group_box1.setLayout(enquadramento_radio_layout)
        self.enlace_layout.addWidget(enquadramento_radio_group_box1)

        # Radio buttons for detecção/correção de erro
        corr_radio_group_box2 = QGroupBox()
        corr_radio_layout2 = QHBoxLayout()
        corr_radio_group_box2 = QGroupBox()
        detection_label = QLabel("Detecção/Correção de Erro")
        detection_label.setStyleSheet(
            "font-weight: bold; font-size: 11pt;")
        self.radio_corr1 = QRadioButton("Bit de Paridade Par")
        self.radio_corr2 = QRadioButton("CRC32")
        self.radio_corr3 = QRadioButton("Hamming")
        self.radio_corr1.setChecked(True)  # Set default selection
        corr_radio_layout2.addWidget(detection_label)
        corr_radio_layout2.addWidget(self.radio_corr1)
        corr_radio_layout2.addWidget(self.radio_corr2)
        corr_radio_layout2.addWidget(self.radio_corr3)
        corr_radio_group_box2.setLayout(corr_radio_layout2)
        self.enlace_layout.addWidget(corr_radio_group_box2)

        # Add Enlace layout to right_layout with 20% height
        self.right_layout.addLayout(self.enlace_layout, 2)

    def update_plot(self, value):
        if (value < 0):
            return
        # This function will be called when the slider is moved
        window_size = 10  # The size of your 'view window'
        self.ax.set_xlim(value, value + window_size)
        self.canvas.draw()

    def update_plot_mod(self, value):
        if (value < 0):
            return
        # This function will be called when the slider for modulated data is moved
        if self.radio_8qam.isChecked():
            window_size = 1
        else:
            window_size = 1000  # The size of your 'view window'
        self.ax_mod.set_xlim(value, value + window_size)
        self.canvas_mod.draw()

    def plot_data(self, data):
        if (len(data) == 0):
            return

        # Clear the previous plot
        self.figure.clear()

        # Create an axis
        ax = self.figure.add_subplot()
        ax.set_xlim(0, 10)

        # Set margins and background color
        ax.margins(0)  # Remove default margins
        self.figure.patch.set_facecolor(
            '#FAFAFA')  # Soft gray background color
        ax.set_facecolor('#FAFAFA')  # Match the figure's background color

        # Remove top and right spines and make bottom and left spines thinner
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(0.5)
        ax.spines['left'].set_linewidth(0.5)

        # Define V value for the signal amplitude and convert digital data (0 and 1) to signal levels (-V and V)
        V = 1  # Adjust V based on your signal's amplitude
        signal = [V if bit == 1 else 0 if bit == 0 else -V for bit in data]

        # Plot data as a digital signal with a custom color and line width
        ax.step(np.arange(len(data)), signal, where='post',
                color='#007ACC', linewidth=2)

        # Add a horizontal line at y=0, make it subtle
        ax.axhline(y=0, color='#CCCCCC', linestyle='--', linewidth=0.5)

        # Customize tick marks and gridlines for better readability
        ax.xaxis.set_tick_params(
            which='both', width=0.5, colors='#555555')  # Custom tick color
        ax.yaxis.set_tick_params(which='both', width=0.5, colors='#555555')
        ax.grid(True, which='both', linestyle='--',
                linewidth=0.5, color='#BBBBBB')

        # Set y-axis ticks and labels for -V and V
        ax.set_yticks([-V, V])
        # Dark grey color for tick labels
        ax.set_yticklabels(['-V', 'V'], color='#333333')

        # Set y-axis limits to slightly above and below the signal levels
        ax.set_ylim(-V-0.5, V+0.5)

        # Customize font size for tick labels
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontsize(10)

        # Optionally, remove the x-axis labels if they are not necessary
        ax.set_xticklabels([])

        # Center x-axis at y=0
        ax.spines['bottom'].set_position('zero')

        self.slider.setMaximum(len(data))
        # Set the axis for data
        self.ax = self.figure.gca()

        # Refresh the canvas
        self.canvas.draw()

    def plot_data_mod(self, data, tempo=None, balds=None):
        if (len(data) == 0):
            return

        if self.radio_8qam.isChecked():
            # Clear the previous plot
            self.figure_mod.clear()

            time_max = int(np.max(tempo))

            # Create an axis
            ax = self.figure_mod.add_subplot()

            ax.set_xlim(0, 1)
            self.slider_mod.setMaximum(time_max)
            self.ax_mod = self.figure_mod.gca()
            self.slider_mod.valueChanged.connect(self.update_plot_mod)

            for i in range(balds):
                ax.step(tempo[i * 100: (i + 1) * 100],
                        np.real(data[i * 100: (i + 1) * 100]), where='post', linewidth=2)

            ax.legend(loc='upper right', title=' - Bauds',
                      fontsize=6, bbox_to_anchor=(1.1, 1.1))

            # Remove top and right spines and make bottom and left spines thinner
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_linewidth(0.5)

            # Set margins and background color
            ax.margins(0)  # Remove default margins
            self.figure_mod.patch.set_facecolor(
                '#FAFAFA')  # Soft gray background color
            ax.set_facecolor('#FAFAFA')  # Match the figure's background color

            # Refresh the canvas
            self.canvas_mod.draw()

        else:

            # Clear the previous plot
            self.figure_mod.clear()

            # Create an axis
            ax = self.figure_mod.add_subplot()
            ax.set_xlim(0, 1000)

            # Set margins and background color
            ax.margins(0)  # Remove default margins
            self.figure_mod.patch.set_facecolor(
                '#FAFAFA')  # Soft gray background color
            ax.set_facecolor('#FAFAFA')  # Match the figure's background color

            # Remove top and right spines and make bottom and left spines thinner
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_linewidth(0.5)

            # Plot the digital signal with a custom color and line width
            ax.step(np.arange(len(data)), data, where='post',
                    color='#007ACC', linewidth=2)

            # Add a horizontal line at y=0, make it subtle
            ax.axhline(y=0, color='#CCCCCC', linestyle='--', linewidth=0.5)

            # Customize tick marks and gridlines for better readability
            ax.xaxis.set_tick_params(
                which='both', width=0.5, colors='#555555')  # Custom tick color
            ax.yaxis.set_tick_params(which='both', width=0.5, colors='#555555')
            ax.grid(True, which='both', linestyle='--',
                    linewidth=0.5, color='#BBBBBB')

            # Set y-axis limits to slightly above and below the signal levels
            max_val = max(data)
            min_val = min(data)
            ax.set_ylim(min_val, max_val)

            # Customize font size for tick labels
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontsize(10)
                label.set_color('#333333')  # Dark grey color for tick labels

            self.slider_mod.setMaximum(len(data))
            # Set the axis for modulated data
            self.ax_mod = self.figure_mod.gca()

            # Refresh the canvas
            self.canvas_mod.draw()

    def transmit_and_receive(self):
        # Get input text and selected encoding
        text = self.input_field.text()

        if self.radio_nrz.isChecked():
            self.encoding = "NRZ"
        elif self.radio_manchester.isChecked():
            self.encoding = "Manchester"
        elif self.radio_bipolar.isChecked():
            self.encoding = "Bipolar"

            # Plot modulated data
        if (self.radio_ask.isChecked()):
            self.modulation = "ask"
        elif (self.radio_fsk.isChecked()):
            self.modulation = "fsk"
        elif (self.radio_8qam.isChecked()):
            self.modulation = "8qam"

        # Enlace de dados
        if (self.radio_enq1.isChecked()):
            self.framing = "character_count"
        elif (self.radio_enq2.isChecked()):
            self.framing = "bits_insertion"
        elif (self.radio_enq3.isChecked()):
            self.framing = "byte_insertion"

        # Detecção e correção de erro
        if (self.radio_corr1.isChecked()):
            self. error_detection = "even_parity"
        elif (self.radio_corr2.isChecked()):
            self.error_detection = "crc"
        elif (self.radio_corr3.isChecked()):
            self.error_detection = "hamming"

        # Create a Transmissor object and perform transmission
        transmissor = Transmissor(text)

        # Runs and sends message to Receiver
        result = transmissor.run(self.encoding, self.framing,
                                 self.error_detection, self.modulation)

        self.receivedMessageRaw, self.receivedMessageBits, self.receivedMessageText = self.receptor.run(
            self.encoding, self.framing, self.error_detection)

        if self.radio_8qam.isChecked():
            self.bit_array = result[0]
            self.encoded_bits = result[1]
            self.balds = result[2][0]
            self.tempo = result[2][1]
            self.signal = result[2][2]
            self.plot_data_mod(self.signal, self.tempo, self.balds)

        else:
            self.bit_array = result[0]
            self.encoded_bits = result[1]
            self.signal = result[2]
            self.plot_data_mod(self.signal)

        self.plot_data(self.encoded_bits)

        self.bitsream = ''.join([str(c) for c in self.bit_array])
        self.transmitted_data = ''.join([str(c) for c in self.encoded_bits])

        transmissor_text_edit_str = f"""
        <p style='text-align: justify; font-size: 14pt;'>
            Fluxo de bits: {self.bitsream}<br><br>
            <span style='color: skyblue; margin-top:50px;'>Codificação ({self.encoding}): {self.transmitted_data}</span>
        </p>"""
        self.transmissor_text_edit.setHtml(transmissor_text_edit_str)

        results_str = f"""
        <p style='text-align: justify;'>
            <span style='color: skyblue; font-size: 14pt;'>Dados recebidos: {self.receivedMessageRaw}</span>
            <p></p>
            <span style='font-size: 14pt;'>Fluxo de bits decodificado: {self.receivedMessageBits}</span><br><br>

            <span style='color: lightgreen; 'font-size: 14pt;'>Texto decodificado: {self.receivedMessageText}</span>
        </p>"""
        self.results_text_edit.setHtml(results_str)


def main():
    app = QApplication(sys.argv)
    mainWin = Window()
    mainWin.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
