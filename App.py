import sys
import time
import matplotlib
import webbrowser
from mplcursors import Cursor
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore
import serial.tools.list_ports
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

matplotlib.use('Qt5Agg')
ArduinoSerial = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, data=None):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        self.setParent(parent)
        self.update_chart(data)
        self.annot = self.axes.annotate("", xy=(0,0), xytext=(20,20),
                                        textcoords="offset points",
                                        bbox=dict(boxstyle="round", fc="w"),
                                        arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)
        self.mpl_connect("motion_notify_event", self.hover)

    def update_chart(self, data, index=None):
        self.axes.cla()
        if index == 1:
            self.line, = self.axes.plot(data['humidity']['x'], data['humidity']['y'], 'r')
            self.axes.set_ylabel("Humidity")
        elif index == 2:
            self.line, = self.axes.plot(data['temperature']['x'], data['temperature']['y'], 'r')
            self.axes.set_ylabel("Temperature")
        elif index == 3:
            self.line, = self.axes.plot(data['ph']['x'], data['ph']['y'], 'r')
            self.axes.set_ylabel("PH")
        elif index == 4:
            self.line, = self.axes.plot(data['oxygen']['x'], data['oxygen']['y'], 'r')
            self.axes.set_ylabel("Oxygen")
        self.axes.set_xlabel('Time (ms)')
        self.draw_idle()

    def update_annot(self, ind):
        x, y = self.line.get_data()
        self.annot.xy = (x[ind["ind"][0]], y[ind["ind"][0]])
        text = f"x: {x[ind['ind'][0]]:.2f}\ny: {y[ind['ind'][0]]:.2f}"
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.4)

    def hover(self, event):
        vis = self.annot.get_visible()
        if event.inaxes == self.axes:
            cont, ind = self.line.contains(event)
            if cont:
                self.update_annot(ind)
                self.annot.set_visible(True)
                self.draw_idle()
            else:
                if vis:
                    self.annot.set_visible(False)
                    self.draw_idle()


class Worker(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)
    def run(self):
        while True:
            try:
                data = ArduinoSerial.readline().decode('ascii').strip()
                if data:
                    self.data_received.emit(data)
                time.sleep(0.1)
            except:
                print("Error...retrying!")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.baudrate = 9600
        self.allow_read = True
        # self.global_index = 1
        #
        # self.data = {
        #     'humidity': {'x': [], 'y': []},
        #     'temperature': {'x': [], 'y': []},
        #     'ph': {'x': [], 'y': []},
        #     'oxygen': {'x': [], 'y': []}
        # }

        self.ui = uic.loadUi('HomeScreen_v2.ui', self)
        self.setFixedSize(1252, 670)
        # self.switch_chart("BIỂU ĐỒ ĐỘ ẨM", 1)
        self.show()

        self.scan_ports()

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ui.gridLayout.addWidget(self.toolbar, 0, 1)
        self.ui.gridLayout.addWidget(self.canvas, 1, 1)
        # self.update_chart()
        #
        # self.worker = Worker()
        # self.worker.data_received.connect(self.handle_data)
        # self.worker.start()

        self.help.triggered.connect(self.help_link)
        self.close_app.triggered.connect(self.stop_app)
        self.show_pH.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ ĐỘ PH", 3))
        self.show_oxi.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ LƯỢNG OXI", 4))
        self.show_humidity.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ ĐỘ ẨM", 1))
        self.show_temperature.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ NHIỆT ĐỘ", 2))

        baud_rates = [300, 1200, 2400, 4800, 9600, 19200, 14400, 28800, 38400, 57600, 115200]
        for baud in baud_rates:
            action_tile = f'{baud} baud'
            baud_action = QAction(action_tile, self)
            self.com_baudrate.addAction(baud_action)
            baud_action.triggered.connect(lambda: self.set_baudrate(baud))

        self.stop_record.clicked.connect(self.stop_read)

    def stop_read(self):
        if self.allow_read:
            self.worker.terminate()
            self.stop_record.setText("CONTINUE")
            self.allow_read = False

        else:
            self.worker.start()
            self.stop_record.setText("STOP")
            self.allow_read = True

    def list_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def scan_ports(self):
        ports = self.list_serial_ports()
        for port in ports:
            action = QAction(port, self)
            action.triggered.connect(lambda: self.set_com(port))
            self.com_selection.addAction(action)

    def set_com(self, com_name):
        ArduinoSerial = serial.Serial(com_name, self.baudrate)
        print(f'Arduino connected: {com_name}')

    def set_baudrate(self, baudrate):
        self.baudrate = baudrate
        print(f'Baudrate set at: {baudrate}')

    def help_link(self):
        webbrowser.open("https://docs.stemvn.vn/vi/latest/")

    def stop_app(self):
        try:
            self.Arduino.close()
        except:
            pass
        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
