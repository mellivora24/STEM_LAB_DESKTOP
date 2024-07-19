import sys
import threading
import time
import matplotlib
import webbrowser
from serial import Serial
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore
import serial.tools.list_ports
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

matplotlib.use('Qt5Agg')
ArduinoSerial = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        self.setParent(parent)

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
        self.global_index = 1

        self.data = {
            'humidity': {'x': [], 'y': []},
            'temperature': {'x': [], 'y': []},
            'ph': {'x': [], 'y': []},
            'oxygen': {'x': [], 'y': []}
        }

        self.ui = uic.loadUi('HomeScreen_v2.ui', self)
        self.setFixedSize(1252, 670)
        self.switch_chart("BIỂU ĐỒ ĐỘ ẨM", 1)
        self.show()

        self.scan_ports()

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ui.gridLayout.addWidget(self.toolbar, 0, 1)
        self.ui.gridLayout.addWidget(self.canvas, 1, 1)
        self.update_chart()

        self.worker = Worker()
        self.worker.data_received.connect(self.handle_data)
        self.worker.start()

        self.help.triggered.connect(self.help_link)
        self.close_app.triggered.connect(self.stop_app)
        self.show_pH.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ ĐỘ PH", 3))
        self.show_oxi.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ LƯỢNG OXI", 4))
        self.show_humidity.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ ĐỘ ẨM", 1))
        self.show_temperature.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ NHIỆT ĐỘ", 2))

        steps_y = [0.5, 1, 2, 5, 10, 20, 50, 100, 1000]
        for step in steps_y:
            action_name = f'_step_y{step}'
            action_tile = f'{step}'
            steps_y_action = QAction(action_tile, self)
            self.steps_y_menu.addAction(steps_y_action)
            steps_y_action.triggered.connect(lambda checked, step=step: self.set_rangeY(step))

        baud_rates = [300, 1200, 2400, 4800, 9600, 19200, 14400, 28800, 38400, 57600, 115200]
        for baud in baud_rates:
            action_name = f'_baud{baud}'
            action_tile = f'{baud} baud'
            baud_action = QAction(action_tile, self)
            self.com_baudrate.addAction(baud_action)
            baud_action.triggered.connect(lambda checked, baud=baud: self.set_baudrate(baud))

        self.stop_record.clicked.connect(self.stop_read)

    @QtCore.pyqtSlot(str)
    def handle_data(self, dataReceivedSerial):
        if dataReceivedSerial:
            convertedData = int(dataReceivedSerial)
            if convertedData:
                self.append_data(self.global_index, convertedData)
                self.update_chart()

    def append_data(self, index, value):
        if index == 1:
            self.data['humidity']['x'].append(len(self.data['humidity']['x']))
            self.data['humidity']['y'].append(value)
            self.humi_lcd.display(value)
        elif index == 2:
            self.data['temperature']['x'].append(len(self.data['temperature']['x']))
            self.data['temperature']['y'].append(value)
            self.temp_lcd.display(value)
        elif index == 3:
            self.data['ph']['x'].append(len(self.data['ph']['x']))
            self.data['ph']['y'].append(value)
            self.ph_lcd.display(value)
        elif index == 4:
            self.data['oxygen']['x'].append(len(self.data['oxygen']['x']))
            self.data['oxygen']['y'].append(value)
            self.oxi_lcd.display(value)

    def update_chart(self):
        self.canvas.axes.cla()
        if self.global_index == 1:
            self.canvas.axes.plot(self.data['humidity']['x'], self.data['humidity']['y'], 'r')
        elif self.global_index == 2:
            self.canvas.axes.plot(self.data['temperature']['x'], self.data['temperature']['y'], 'r')
        elif self.global_index == 3:
            self.canvas.axes.plot(self.data['ph']['x'], self.data['ph']['y'], 'r')
        elif self.global_index == 4:
            self.canvas.axes.plot(self.data['oxygen']['x'], self.data['oxygen']['y'], 'r')
        self.canvas.draw()

    def set_rangeY(self, step):
        self.canvas.axes.yaxis.set_major_locator(MultipleLocator(step))

    def switch_chart(self, title, index):
        self.global_index = index
        self.chart_title.setText(title)
        try:
            ArduinoSerial.write(str(index).encode())
        except:
            print("Error...retrying!")

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
            action.triggered.connect(lambda checked, port=port: self.set_com(port))
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
