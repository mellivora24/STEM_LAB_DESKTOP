import sys
import time
import webbrowser
import matplotlib
import numpy as np
import pandas as pd
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore
import serial.tools.list_ports
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

matplotlib.use('Qt5Agg')


class Arduino(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)

    def __init__(self):
        super(Arduino, self).__init__()
        self.is_connected = True
        self.is_sended = False
        self.connect_serial()

    def run(self):
        while True:
            try:
                data = self.ArduinoSerial.readline().decode('ascii').strip()
                if data:
                    self.data_received.emit(data)
                time.sleep(0.1)
            except Exception as e:
                pass

    def connect_serial(self, port=None, baudrate=None, timeout=None):
        try:
            self.ArduinoSerial = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as e:
            self.is_connected = False

    def disconnect_serial(self):
        try:
            self.ArduinoSerial.close()
        except Exception as e:
            pass

    def send(self, message):
        try:
            self.ArduinoSerial.write(message.encode())
            self.is_sended = True
            # print(f"Sent: {message}")
        except Exception as e:
            self.is_sended = False
            # print(f"Send failed: {e}")


class Chart(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.line = None
        fig = Figure(figsize=(width, height), dpi=dpi)
        super(Chart, self).__init__(fig)
        self.setParent(parent)

        self.axes = fig.add_subplot(111)
        self.global_index = 1
        self.data = {
            'humidity': {'x': [], 'y': []},
            'temperature': {'x': [], 'y': []},
            'ph': {'x': [], 'y': []},
            'oxygen': {'x': [], 'y': []}
        }

        self.canvas = FigureCanvas(fig)

        self.annot = self.axes.annotate("Details", xy=(0, 0), xytext=(20, 20),
                                        textcoords="offset points",
                                        bbox=dict(boxstyle="round", fc="w"),
                                        arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.parent().ui.gridLayout.addWidget(self.toolbar, 0, 1)
        self.parent().ui.gridLayout.addWidget(self.canvas, 1, 1)
        self.canvas.mpl_connect("motion_notify_event", self.hover)

    @QtCore.pyqtSlot(str)
    def handle_data(self, data):
        if data:
            converted_data = int(data)
            if converted_data <= 100:
                self.append_data(self.global_index, converted_data)
                self.update_chart()

    def append_data(self, index, value):
        if index == 1:
            self.data['humidity']['x'].append(len(self.data['humidity']['x']))
            self.data['humidity']['y'].append(value)
            self.parent().realtime_value.display(value)
        elif index == 2:
            self.data['temperature']['x'].append(len(self.data['temperature']['x']))
            self.data['temperature']['y'].append(value)
            self.parent().realtime_value.display(value)
        elif index == 3:
            self.data['ph']['x'].append(len(self.data['ph']['x']))
            self.data['ph']['y'].append(value)
            self.parent().realtime_value.display(value)
        elif index == 4:
            self.data['oxygen']['x'].append(len(self.data['oxygen']['x']))
            self.data['oxygen']['y'].append(value)
            self.parent().realtime_value.display(value)

    def update_chart(self):
        self.axes.cla()  # Clear the axes
        if self.global_index == 1:
            self.line, = self.axes.plot(self.data['humidity']['x'], self.data['humidity']['y'], 'r', lw=2)
            self.axes.set_ylabel("Humidity")
        elif self.global_index == 2:
            self.line, = self.axes.plot(self.data['temperature']['x'], self.data['temperature']['y'], 'r', lw=2)
            self.axes.set_ylabel("Temperature")
        elif self.global_index == 3:
            self.line, = self.axes.plot(self.data['ph']['x'], self.data['ph']['y'], 'r', lw=2)
            self.axes.set_ylabel("PH")
        elif self.global_index == 4:
            self.line, = self.axes.plot(self.data['oxygen']['x'], self.data['oxygen']['y'], 'r', lw=2)
            self.axes.set_ylabel("Oxygen")
        self.axes.set_xlabel('Time (s)')
        self.canvas.draw_idle()

    def hover(self, event):
        if not self.parent().allow_read:
            vis = self.annot.get_visible()
            if event.inaxes == self.axes:
                for line in self.axes.get_lines():
                    cont, ind = line.contains(event)
                    if cont:
                        x, y = line.get_data()
                        if "ind" in ind and len(ind["ind"]) > 0:
                            idx = ind["ind"][0]
                            text = f"Time: {x[idx]:.2f}\nValue: {y[idx]:.2f}"
                            self.annot.get_bbox_patch().set_alpha(0.4)
                            self.annot = self.axes.annotate(text=text, xy=(x[idx], y[idx]), xytext=(15, 15),
                                                            textcoords="offset points",
                                                            bbox=dict(boxstyle="round", fc="w"),
                                                            arrowprops=dict(arrowstyle="->"))
                            if not vis:
                                self.annot.set_visible(True)
                            else:
                                self.annot.set_visible(False)
                            self.canvas.draw_idle()

    def export_excel(self):
        all_times = set(self.data['humidity']['x'] +
                        self.data['temperature']['x'] +
                        self.data['ph']['x'] +
                        self.data['oxygen']['x'])
        data_dict = {'Time (s)': [], 'Humidity (%)': [], 'Temperature (*C)': [], 'PH': [], 'Oxygen (%)': []}
        for time in sorted(all_times):
            data_dict['Time'].append(time)
            data_dict['Humidity'].append(self.data['humidity']['y'][self.data['humidity']['x'].index(time)]
                                         if time in self.data['humidity']['x'] else None)
            data_dict['Temperature'].append(self.data['temperature']['y'][self.data['temperature']['x'].index(time)]
                                            if time in self.data['temperature']['x'] else None)
            data_dict['PH'].append(self.data['ph']['y'][self.data['ph']['x'].index(time)]
                                   if time in self.data['ph']['x'] else None)
            data_dict['Oxygen'].append(self.data['oxygen']['y'][self.data['oxygen']['x'].index(time)]
                                       if time in self.data['oxygen']['x'] else None)
        df = pd.DataFrame(data_dict)
        df.to_excel('Result.xlsx', index=False, engine='openpyxl')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("HomeScreen_v2.ui", self)
        self.setWindowIcon(QIcon("assets/icon.ico"))
        self.setFixedSize(1252, 670)
        self.show()

        self.setup_menubar()

        self.baud = 9600
        self.chart_index = 1
        self.allow_read = True
        self.port = '/dev/ttyUSB0'

        self.ChartCanvas = Chart(self)
        self.ArduinoSerial = Arduino()
        self.connect_arduino()

        self.ArduinoSerial.data_received.connect(self.ChartCanvas.handle_data)
        self.ArduinoSerial.start()

        self.switch_chart("BIỂU ĐỒ ĐỘ ẨM", 1)

    def setup_menubar(self):
        list_ports = serial.tools.list_ports.comports()
        ports = [port.device for port in list_ports]
        for port in ports:
            com_title = f'{port}'
            com_action = QAction(com_title, self)
            self.com_selection.addAction(com_action)
            com_action.triggered.connect(lambda checked, port=port: self.setup_com(port))

        baud_rates = [300, 1200, 2400, 4800, 9600, 19200, 14400, 28800, 38400, 57600, 115200]
        for baud in baud_rates:
            baud_tile = f'{baud} baud'
            baud_action = QAction(baud_tile, self)
            self.com_baudrate.addAction(baud_action)
            baud_action.triggered.connect(lambda checked, baud=baud: self.setup_baudrate(baud))

        self.close_app.triggered.connect(self.quit)
        self.help.triggered.connect(self.readTheDocs)
        self.stop_record.clicked.connect(self.pause_receive)
        self.export_excel.triggered.connect(self.to_excel)
        self.show_pH.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ ĐỘ PH", 3))
        self.show_oxi.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ LƯỢNG OXI", 4))
        self.show_humidity.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ ĐỘ ẨM", 1))
        self.show_temperature.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ NHIỆT ĐỘ", 2))

    def setup_com(self, port):
        self.port = port
        self.connect_arduino()

    def setup_baudrate(self, baudrate):
        self.baud = baudrate
        self.connect_arduino()

    def connect_arduino(self):
        try:
            self.ArduinoSerial.connect_serial(port=self.port, baudrate=self.baud, timeout=1)
            self.allow_read = True
            self.ArduinoSerial.start()
            self.stop_record.setText("STOP")
            # print(f"Connected to on port {self.port}, baudrate {self.baud}!")
        except Exception as e:
            # print(f"Connection failed: {e}")
            self.ArduinoSerial.is_connected = False
            self.stop_record.setText("START")

    def pause_receive(self):
        if self.allow_read:
            self.allow_read = False
            self.ArduinoSerial.terminate()
            self.stop_record.setText("CONTINUE")
            # print("STOP receiving data from Serial")
        else:
            self.allow_read = True
            self.ArduinoSerial.start()
            self.stop_record.setText("STOP")
            # print("CONTINUE receiving data from Serial")

    def show_chart(self):
        pass

    def switch_chart(self, chart_title, chart_index):
        self.ChartCanvas.global_index = chart_index
        self.chart_index = chart_index
        self.chart_title.setText(chart_title)
        self.values_title.setText(f"{chart_title[8:]}")
        self.ArduinoSerial.send(str(chart_index))

    def to_excel(self):
        self.ChartCanvas.export_excel()

    def readTheDocs(self):
        # print("Open web browser at: https://docs.stemvn.vn/vi/latest/")
        webbrowser.open("https://docs.stemvn.vn/vi/latest/")

    def quit(self) -> None:
        # print("Close app")
        self.ArduinoSerial.disconnect_serial()
        QApplication.quit()
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
