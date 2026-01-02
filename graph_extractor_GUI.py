import sys
import math
import numpy as np
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from scipy.integrate.tests.test_odeint_jac import rhs


def map_axis(v, p0, p1, d0, d1, logscale=False, invertAxis = False):
    if logscale:
        d0 = math.log10(d0)
        d1 = math.log10(d1)
    if invertAxis:
        t = (p1 - v) / (p1 - p0)
    else:
        t = (v - p0) / (p1 - p0)
    
    dv = d0 + t * (d1 - d0)
    return 10**dv if logscale else dv

class ImageView(QWidget):
    clicked = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()
        self.pix = None
        self.px0 = self.py0 = 0.1
        self.px1 = self.py1 = 10
        
        self.curvePts = None

    def set_pixmap(self, pixmap):
        self.pix = pixmap
        self.update()

    def set_axis_pixels(self, px0, py0, px1, py1):
        self.px0, self.py0, self.px1, self.py1 = px0, py0, px1, py1
        self.update()

    def set_curve_pixels(self, curvePts,rW,rH):
        # 
        self.curvePts = curvePts.copy()
        for pIdx in range(len(self.curvePts)):
            cPt = self.curvePts[pIdx]
            self.curvePts[pIdx] = (cPt[0],cPt[1],cPt[2]*rW,cPt[3]*rH)
            
        self.update()
        
    def mousePressEvent(self, event):
        if self.pix:
            self.clicked.emit(event.pos().x(), event.pos().y())

    def sizeHint(self):
        return QSize(600, 400)

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.pix:
            painter.drawPixmap(self.rect(), self.pix)

            # Draw axes --------------------------------------------------------
            painter.setRenderHint(QPainter.Antialiasing)
    
            # X axis = red
            self.draw_arrow(
                painter,
                QPointF(self.px0, self.py0),
                QPointF(self.px1, self.py0),
                QColor(220, 0, 0),
            )
    
            # Y axis = green
            self.draw_arrow(
                painter,
                QPointF(self.px0, self.py0),
                QPointF(self.px0, self.py1),
                QColor(0, 180, 0),
            )
            
            # Stop here if there are no curves
            if not self.curvePts:
                return
            
            cColor = QColor(50,50,255)
            rectSize = 6
            halfRectSize = rectSize/2 
            pen = QPen(cColor, 2)
            painter.setPen(pen)
            painter.setBrush(cColor)
            # Draw curves, if available
            for pIdx in range(len(self.curvePts)):
                cPt0 = QPointF(self.curvePts[pIdx][2],self.curvePts[pIdx][3])
                painter.drawRect(int(cPt0.x() - halfRectSize), int(cPt0.y() - halfRectSize), rectSize, rectSize)
                
                if not (pIdx == (len(self.curvePts) - 1)):
                    cPt1 = QPointF(self.curvePts[pIdx + 1][2],self.curvePts[pIdx + 1][3])
                    painter.drawLine(cPt0, cPt1)

    def draw_arrow(self, painter, p0, p1, color):
        pen = QPen(color, 4)
        painter.setPen(pen)

        # main line
        painter.drawLine(p0, p1)

        # arrow head
        angle = math.atan2(p1.y() - p0.y(), p1.x() - p0.x())
        size = 10

        left = QPointF(
            p1.x() - size * math.cos(angle - math.pi / 6),
            p1.y() - size * math.sin(angle - math.pi / 6),
        )
        right = QPointF(
            p1.x() - size * math.cos(angle + math.pi / 6),
            p1.y() - size * math.sin(angle + math.pi / 6),
        )

        painter.drawLine(p1, left)
        painter.drawLine(p1, right)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Curve Digitizer")

        self.image_label = ImageView()
        self.image_label.clicked.connect(self.on_click)
        self.image = None
        
        # Install event filter
        self.image_label.installEventFilter(self)
        
        # pixel CS
        self.px0 = QLineEdit("N/A")
        self.py0 = QLineEdit("N/A")
        self.px1 = QLineEdit("N/A")
        self.py1 = QLineEdit("N/A")

        # data CS
        self.x0 = QLineEdit("0.1")
        self.x1 = QLineEdit("10")
        self.y0 = QLineEdit("0.1")
        self.y1 = QLineEdit("10")

        self.xscale = QComboBox()
        self.yscale = QComboBox()
        self.xscale.addItems(["linear", "log"])
        self.yscale.addItems(["linear", "log"])
        
        self.curve_list = QListWidget()
        self.curve_list.currentRowChanged.connect(self.on_curve_changed)
        
        self.add_curve_btn = QPushButton("Add Curve")
        self.add_curve_btn.clicked.connect(self.add_curve)

        self.point_edit_btn = QPushButton("Add Points Mode")
        self.point_edit_btn.clicked.connect(self.switch_edit_add)
        self.addPointsMode = True
        self.point_edit_btn.setCheckable(True)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["X", "Y"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.export_csv_btn = QPushButton("Export As CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)

        self.curves = {}
        self.current_curve = None

        self.layout_ui()
        if self.image:
            self.update_axes_drawn()
            
            
        # Disable all buttons
        self.enableButtons(False)

    def eventFilter(self, obj, event):
        # This is a handler for all events
        if obj is self.image_label and event.type() == event.Resize:
            
            # Current image width and height in pixels
            self.cImgW = self.image_label.width()
            self.cImgH = self.image_label.height()
            
            if self.image:
                self.update_axes_drawn()
                
                # Update curves, if there is a current curve selection
                if self.current_curve:
                    rW = self.cImgW/self.oImgW
                    rH = self.cImgH/self.oImgH
                    
                    pts = self.curves[self.current_curve]
                    self.image_label.set_curve_pixels(pts,rW,rH)
            
        return super().eventFilter(obj, event)

    def switch_edit_add(self):
        if self.addPointsMode:
            self.point_edit_btn.setText("Move/Edit Points Mode")
            self.table.setEnabled(True)
        else:
            self.point_edit_btn.setText("Add Points Mode")
            self.table.setEnabled(False)
        
        self.addPointsMode = not self.addPointsMode 

    def layout_ui(self):
        load_btn = QPushButton("Load Image")
        load_btn.clicked.connect(self.load_image)

        form = QFormLayout()
        
        self.img_size_label = QLabel("Image Size = (N/A,N/A) [px]")
        form.addRow(self.img_size_label)
        
        form.addRow("CS Start X [px]", self.px0)
        form.addRow("CS Start Y [px]", self.py0)
        form.addRow("Dx (X+) [px]", self.px1)
        form.addRow("Dy (Y+) [px]", self.py1)
        form.addRow("Data X min", self.x0)
        form.addRow("Data X max", self.x1)
        form.addRow("Data Y min", self.y0)
        form.addRow("Data Y max", self.y1)
        form.addRow("X scale", self.xscale)
        form.addRow("Y scale", self.yscale)

        # update axes overlay when inputs change
        for w in [self.px0, self.py0, self.px1, self.py1]:
            w.textChanged.connect(self.update_axes_drawn)

        left = QVBoxLayout()
        left.addWidget(load_btn)
        left.addWidget(self.image_label)

        right = QVBoxLayout()
        right.addLayout(form)
        right.addWidget(QLabel("Curves"))
        right.addWidget(self.add_curve_btn)
        right.addWidget(self.curve_list)
        right.addWidget(self.point_edit_btn)
        right.addWidget(self.table)
        right.addWidget(self.export_csv_btn)


        layout = QHBoxLayout()
        layout.addLayout(left, 3)
        layout.addLayout(right, 2)

        self.setLayout(layout)
        
        pass

    def enableButtons(self,buttonEn = True):
        self.px0.setEnabled(buttonEn)
        self.px1.setEnabled(buttonEn)
        self.py0.setEnabled(buttonEn)
        self.py1.setEnabled(buttonEn)

        self.x0.setEnabled(buttonEn)
        self.x1.setEnabled(buttonEn)
        self.y0.setEnabled(buttonEn)
        self.y1.setEnabled(buttonEn)
        
        self.xscale.setEnabled(buttonEn)
        self.yscale.setEnabled(buttonEn)
        
        self.point_edit_btn.setEnabled(buttonEn)
        self.add_curve_btn.setEnabled(buttonEn)
        
        self.table.setEnabled(buttonEn)
        
        self.export_csv_btn.setEnabled(buttonEn)

    def export_csv(self):
        # Check if a curve is even chosen
        if not self.current_curve:
            _ = self.show_message_box("No curve is selected")
            return
        
        # Get Points
        pts = self.curves[self.current_curve]
        
        # Check that there are points to export in the curve
        if len(pts) == 0:
            _ = self.show_message_box("No points available in curve")
            return
        
        # Build 2-column numpy array (x, y)
        arr = np.array([(x, y) for (x, y, *_) in pts], dtype=float)
    
        # Default filename suggestion
        default_name = f"{self.current_curve}.csv"
    
        # Ask user where to save
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Curve as CSV",
            default_name,
            "CSV Files (*.csv);;All Files (*)"
        )
    
        # User cancelled?
        if not path:
            return
    
        try:
            # Save CSV with header and no '#' before header
            np.savetxt(
                path,
                arr,
                delimiter=",",
                header="x,y",
                comments="",
                fmt="%.10g"
            )
    
            QMessageBox.information(
                self,
                "Export Complete",
                f"Saved {len(arr)} points to:\n{os.path.basename(path)}"
            )
    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not save file:\n{e}"
            )
        
    
    def show_message_box(self,strToDisp):
        """Displays a simple information message box."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(strToDisp)
        msg.setWindowTitle("Example Title")
        msg.setStandardButtons(QMessageBox.Ok)
        
        # The exec_() method runs the dialog's local event loop and returns the button clicked
        returnValue = msg.exec_()
        return returnValue
    
    def update_axes_drawn(self):
        try:
            # This should be done only if there is an
            # image loaded
            if self.image:
                # The pixels are gi
                px0 = float(self.px0.text())
                px1 = float(self.px1.text())
                
                py0 = self.oImgH - float(self.py0.text())
                py1 = self.oImgH - float(self.py1.text())
                
                rH = self.cImgH/self.oImgH
                rW = self.cImgW/self.oImgW
                # Re-normalize according to current size
                px0 *= rW
                px1 *= rW
                py0 *= rH
                py1 *= rH
                
                self.image_label.set_axis_pixels(px0, py0, px1, py1)
            
        except Exception:
            pass
        
    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image")
        if not path:
            return
        self.image = QPixmap(path)
        self.image_label.set_pixmap(self.image)

        # Current image width and height in pixels
        self.cImgW = self.image_label.width()
        self.cImgH = self.image_label.height()
        
        # Original image width and height in pixels
        self.oImgW = self.image.width()
        self.oImgH = self.image.height()

        # Update all text boxes with pixel CS
        self.enableButtons()
        
        self.px0.setText(str(math.floor(self.oImgW*0.25)))
        self.py0.setText(str(math.floor(self.oImgH*0.25)))
        self.px1.setText(str(math.floor(self.oImgW*0.75)))
        self.py1.setText(str(math.floor(self.oImgH*0.75)))

        self.img_size_label.setText(f"Image Size = ({self.oImgW},{self.oImgH}) [px]")

        self.update_axes_drawn()

    def add_curve(self):
        name, ok = QInputDialog.getText(self, "Curve name", "Name:")
        if not ok or not name:
            return
        self.curves[name] = []
        self.curve_list.addItem(name)
        self.curve_list.setCurrentRow(self.curve_list.count() - 1)
        self.current_curve = name
        self.update_table()        
     
    def on_click(self, px, py):
        # Check if there is a current curve
        if not self.current_curve:
            return
        
        # Check if it is currently in add points mode
        if not self.addPointsMode:
            return
        
        px0 = float(self.px0.text())
        py0 = float(self.py0.text())
        px1 = float(self.px1.text())
        py1 = float(self.py1.text())

        x0 = float(self.x0.text())
        x1 = float(self.x1.text())
        y0 = float(self.y0.text())
        y1 = float(self.y1.text())

        logx = self.xscale.currentText() == "log"
        logy = self.yscale.currentText() == "log"

        x = map_axis(px, px0, px1, x0, x1, logx)
        y = map_axis(py, py0, py1, y0, y1, logy, True)

        # Pixels should be stored in the *original* image
        # pixel coordinate system, as that doesn't resize
        rW = self.oImgW/self.cImgW
        rH = self.oImgH/self.cImgH
        
        ox_px = px*rW
        oy_px = py*rH 

        pts = self.curves[self.current_curve]
        pts.append((x, y, ox_px, oy_px))
        pts.sort(key=lambda p: p[0])
        self.curves[self.current_curve] = pts
        
        self.update_table()
        self.send_curve_to_image()

    def send_curve_to_image(self):
        
        pts = self.curves[self.current_curve]
        rW = self.cImgW/self.oImgW
        rH = self.cImgH/self.oImgH
        
        self.image_label.set_curve_pixels(pts,rW,rH)

    def on_curve_changed(self, row):
        if row < 0:
            self.current_curve = None
            self.table.setRowCount(0)
            self.image_label.set_curve_pixels(None, 1, 1)
            return
    
        # Get the curve name from the list widget
        self.current_curve = self.curve_list.item(row).text()
    
        # Update the table for this curve
        self.update_table()
        self.send_curve_to_image()

    def update_table(self):
        if not self.current_curve:
            self.table.setRowCount(0)
            return

        pts = self.curves[self.current_curve]
        self.table.setRowCount(len(pts))
        
        if len(pts) == 0:
            return

        editable = self.point_edit_btn.isChecked()
        trig = (
            QAbstractItemView.DoubleClicked
            if editable
            else QAbstractItemView.NoEditTriggers
        )
        self.table.setEditTriggers(trig)

        for i, (x, y, _, _) in enumerate(pts):
            self.table.setItem(i, 0, QTableWidgetItem(f"{x:g}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{y:g}"))


app = QApplication(sys.argv)
w = App()
w.show()
sys.exit(app.exec_())
