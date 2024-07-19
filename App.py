import sys
import random
import matplotlib
import webbrowser
from serial import Serial
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore
import serial.tools.list_ports
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

matplotlib.use('Qt5Agg')


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        self.setParent(parent)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Global variable in class
        self.baudrate = 9600

        # Load UI
        self.ui = uic.loadUi('HomeScreen_v2.ui', self)
        self.setFixedSize(1252, 670)
        self.switch_chart("BIỂU ĐỒ ĐỘ ẨM", 1)
        self.show()

        # Scan and add com ports
        self.scan_ports()

        # Triggered for menu bar
        self.help.triggered.connect(self.help_link)
        self.close_app.triggered.connect(self.stop_app)
        self.show_pH.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ ĐỘ PH", 3))
        self.show_oxi.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ LƯỢNG OXI", 4))
        self.show_humidity.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ ĐỘ ẨM", 1))
        self.show_temperature.triggered.connect(lambda: self.switch_chart("BIỂU ĐỒ NHIỆT ĐỘ", 2))

        # Set up and triggered step in Y axis
        steps_y = [0.5, 1, 2, 5, 10, 20, 50, 100, 1000]
        for step in steps_y:
            action_name = f'_step_y{step}'
            action_tile = f'{step}'
            action = getattr(self, action_name, None)
            steps_y_action = QAction(action_tile, self)
            self.steps_y_menu.addAction(steps_y_action)
            if action:
                action.triggered.connect(lambda checked, step=step: self.set_rangeY(step))

        # Set up and triggered baudrate
        baud_rates = [300, 1200, 2400, 4800, 9600, 19200, 14400, 28800, 38400, 57600, 115200]
        for baud in baud_rates:
            action_name = f'_baud{baud}'
            action_tile = f'{baud} baud'
            action = getattr(self, action_name, None)
            baud_action = QAction(action_tile, self)
            self.com_baudrate.addAction(baud_action)
            if action:
                action.triggered.connect(lambda: self.set_baudrate(baud))

        # Set up the chart widget
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.ui.gridLayout.addWidget(self.canvas, 1, 1)

        n_data = 50
        self.xdata = list(range(n_data))
        self.ydata = [random.randint(0, 10) for i in range(n_data)]
        self.update_plot()

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def update_plot(self):
        self.ydata = self.ydata[1:] + [random.randint(0, 10)]
        self.canvas.axes.cla()  # Clear the canvas.
        self.canvas.axes.plot(self.xdata, self.ydata, 'r')
        self.canvas.draw()

    def set_rangeY(self, step):
        self.canvas.axes.yaxis.set_major_locator(MultipleLocator(step))

    def switch_chart(self, title, index):
        self.chart_title.setText(title)

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
        self.Arduino = Serial(com_name, self.baudrate)
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
