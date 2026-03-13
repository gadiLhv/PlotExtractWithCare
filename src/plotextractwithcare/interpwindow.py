"""
Interpolation Window for PlotExtractWithCare
-------------------------------------------
Standalone module (NOT connected to main app yet).

Features:
- Curve selection dropdown (dummy curves for now)
- Interpolation type: linear / cubic / spline
- Radio buttons: number of samples OR step size
- Start/Stop inputs
- Points / Step size input (context-sensitive)
- Live matplotlib plot comparing original and interpolated data
- Axis scale preserved (passed in later; defaults to data bounds here)

Dependencies:
- numpy
- scipy
- matplotlib
- PySide6 (preferred) or PyQt5 (fallback)
"""

import numpy as np

# --- Qt imports (PySide6 preferred) ---
try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
        QRadioButton, QButtonGroup, QLineEdit, QApplication
    )
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
        QRadioButton, QButtonGroup, QLineEdit, QApplication
    )
    from PyQt5.QtCore import Qt

# --- Matplotlib ---
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- SciPy interpolation ---
from scipy.interpolate import interp1d, CubicSpline, UnivariateSpline


class InterpolationWindow(QWidget):
    def __init__(self, curves=None, axis_limits=None, parent=None):
        """
        curves: dict[str, (x_array, y_array)]
        axis_limits: (xmin, xmax, ymin, ymax) or None
        """
        super().__init__(parent)
        self.setWindowTitle("Interpolation Tool")
        self.resize(900, 600)

        # Dummy curves if none provided
        if curves is None:
            x = np.linspace(0, 10, 20)
            curves = {
                "Curve A": (x, np.sin(x)),
                "Curve B": (x, np.cos(x)),
            }

        self.curves = curves
        self.axis_limits = axis_limits

        self._build_ui()
        self._connect_signals()
        self._update_plot()

    # ------------------------------------------------------------------
    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # ===== Left control panel =====
        control_layout = QVBoxLayout()

        # Curve selector
        control_layout.addWidget(QLabel("Curve:"))
        self.curve_combo = QComboBox()
        self.curve_combo.addItems(self.curves.keys())
        control_layout.addWidget(self.curve_combo)

        # Interpolation type
        control_layout.addWidget(QLabel("Interpolation type:"))
        self.interp_combo = QComboBox()
        self.interp_combo.addItems(["linear", "cubic", "spline"])
        control_layout.addWidget(self.interp_combo)

        # Sampling mode
        control_layout.addWidget(QLabel("Sampling mode:"))
        self.radio_npoints = QRadioButton("Number of samples")
        self.radio_stepsize = QRadioButton("Step size")
        self.radio_npoints.setChecked(True)

        self.sample_group = QButtonGroup()
        self.sample_group.addButton(self.radio_npoints)
        self.sample_group.addButton(self.radio_stepsize)

        control_layout.addWidget(self.radio_npoints)
        control_layout.addWidget(self.radio_stepsize)

        # Range inputs
        control_layout.addWidget(QLabel("Start X:"))
        self.start_edit = QLineEdit("0")
        control_layout.addWidget(self.start_edit)

        control_layout.addWidget(QLabel("Stop X:"))
        self.stop_edit = QLineEdit("10")
        control_layout.addWidget(self.stop_edit)

        # Points / step
        self.points_label = QLabel("Number of points:")
        self.points_edit = QLineEdit("200")
        control_layout.addWidget(self.points_label)
        control_layout.addWidget(self.points_edit)

        control_layout.addStretch(1)

        # ===== Plot area =====
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        main_layout.addLayout(control_layout, 0)
        main_layout.addWidget(self.canvas, 1)

    # ------------------------------------------------------------------
    def _connect_signals(self):
        self.curve_combo.currentIndexChanged.connect(self._update_plot)
        self.interp_combo.currentIndexChanged.connect(self._update_plot)
        self.radio_npoints.toggled.connect(self._update_sampling_mode)

        for w in [
            self.start_edit,
            self.stop_edit,
            self.points_edit,
        ]:
            w.editingFinished.connect(self._update_plot)

    # ------------------------------------------------------------------
    def _update_sampling_mode(self):
        if self.radio_npoints.isChecked():
            self.points_label.setText("Number of points:")
            self.points_edit.setText("200")
        else:
            self.points_label.setText("Step size:")
            self.points_edit.setText("0.05")
        self._update_plot()

    # ------------------------------------------------------------------
    def _update_plot(self):
        self.ax.clear()

        # Get selected curve
        name = self.curve_combo.currentText()
        x, y = self.curves[name]

        try:
            x_start = float(self.start_edit.text())
            x_stop = float(self.stop_edit.text())
            param = float(self.points_edit.text())
        except ValueError:
            return

        if x_start >= x_stop:
            return

        # Build new x-axis
        if self.radio_npoints.isChecked():
            x_new = np.linspace(x_start, x_stop, int(param))
        else:
            x_new = np.arange(x_start, x_stop, param)

        # Interpolator
        interp_type = self.interp_combo.currentText()

        try:
            if interp_type == "linear":
                f = interp1d(x, y, kind="linear", fill_value="extrapolate")
            elif interp_type == "cubic":
                f = interp1d(x, y, kind="cubic", fill_value="extrapolate")
            else:  # spline
                f = UnivariateSpline(x, y, s=0)

            y_new = f(x_new)
        except Exception:
            return

        # Plot original and interpolated
        self.ax.plot(x, y, "o", label="Original data")
        self.ax.plot(x_new, y_new, "-", label="Interpolated")

        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.legend()

        # Axis limits
        if self.axis_limits:
            self.ax.set_xlim(self.axis_limits[0], self.axis_limits[1])
            self.ax.set_ylim(self.axis_limits[2], self.axis_limits[3])
        else:
            self.ax.relim()
            self.ax.autoscale()

        self.canvas.draw()


# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = InterpolationWindow()
    w.show()
    sys.exit(app.exec())
