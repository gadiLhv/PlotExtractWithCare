# Plot data extractor/Curve Digitizer
# Copyright (C) 2026  Gadi Lahav, RF With Care
# Contact: gadi@rfwithcare.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import math
import numpy as np
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

def map_axis(v, p0, p1, d0, d1, logscale=False):
    if logscale:
        d0 = math.log10(d0)
        d1 = math.log10(d1)
    
    t = (v - p0) / (p1 - p0)
    dv = d0 + t * (d1 - d0)
    return 10**dv if logscale else dv

def inv_map_axis(dv, p0, p1, d0, d1, logscale=False):
    if logscale:
        d0 = math.log10(d0)
        d1 = math.log10(d1)
    
    # Convert to logarithmic if necessary
    v = math.log10(dv) if logscale else dv
    t = (v - d0)/(d1 - d0)
    
    v = p0 + t*(p1 - p0)
        
    return v
    
class ImageView(QWidget):
    clicked = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()
        self.pix = None
        self.px0 = self.py0 = 0.1
        self.px1 = self.py1 = 10
        self.curvePts = None
        self.curveColor = QColor(50,50,255)
        
        # Square dragging interface
        self.dragging = False
        self.drag_curve = -1
        self.drag_index = None
        self.rectSize = 6
        
        self.squareList = []
        
        self.setMouseTracking(True)

    def set_pixmap(self, pixmap):
        self.pix = pixmap
        self.update()

    def set_axis_pixels(self, px0, py0, px1, py1):
        self.px0, self.py0, self.px1, self.py1 = px0, py0, px1, py1
        self.update()

    def set_curve_pixels(self, curvePts, rW, rH, color):
        
        # Convert points to resized coordinate system
        self.curvePts = None if curvePts is None else [
            (x, y, ox*rW, oy*rH) for (x, y, ox, oy) in curvePts
        ]
        
        self.curveColor = color
        self.update()

    def mousePressEvent(self, event):
        gui = self.parent()

        if not self.pix:
            return
        # Add Mode: Send coordinates
        if gui.addPointsMode:            
            self.clicked.emit(event.pos().x(), event.pos().y())
            return
    
        # Move/Edit mode
        if event.buttons() & Qt.LeftButton:
            hit = self.find_point(event.pos())
            
            # Go into dragging mode 
            if hit[1] >= 0:
                self.dragging = True
                self.drag_curve, self.drag_index = hit
                return
        
    def mouseMoveEvent(self, event):

        gui = self.parent()
    
        # Cursor feedback when hovering
        if not gui.addPointsMode:
            hit = self.find_point(event.pos())
            if (hit[1] >= 0):
                self.setCursor(Qt.CrossCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
    
        # Dragging
        if self.dragging:
            # Don't update the table while dragging
            if self.drag_index >= 0:
                
                # Current plot size pixels
                px = event.pos().x()
                py = event.pos().y()
                
                # Curve points
                self.curvePts[self.drag_index] = (
                    self.curvePts[self.drag_index][0],
                    self.curvePts[self.drag_index][1],
                    px,
                    py)
                
                self.update()
            else:
                pass

    def mouseReleaseEvent(self, event):
        
        if self.dragging:
            
            
            # Recalculate this curve point in local coordinates
            # and send it to main gui
            gui = self.parent()
            
            rW = gui.oImgW/gui.cImgW
            rH = gui.oImgH/gui.cImgH
            
            # Get the reference
            updatedCurvePts = gui.curves[self.drag_curve]
            
            # recalculate x and y for graph
            px0, py0, px1, py1, x0, x1, y0, y1 = gui.get_startstop_pixels()
            oImgH = gui.oImgH
            
            # Iterate through points, and recalculate
            for i, (x,y,cx,cy) in enumerate(self.curvePts):
                
                # Convert to original image pixel CS
                ox = cx*rW
                oy = cy*rH
                
                

                logx = gui.xscale.currentText() == "log"
                logy = gui.yscale.currentText() == "log"
                
                x = map_axis(ox        , px0, px1, x0, x1, logx)
                y = map_axis(oImgH - oy, py0, py1, y0, y1, logy)
                
                updatedCurvePts[i] = (x,y,ox,oy)
            
            gui.curves[self.drag_curve] = updatedCurvePts
            gui.update_table()
            
            self.dragging = False
            self.drag_index = -1
            self.drag_curve = None
    
        super().mouseReleaseEvent(event)

    def sizeHint(self):
        return QSize(600, 400)

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.pix:
            painter.drawPixmap(self.rect(), self.pix)
            painter.setRenderHint(QPainter.Antialiasing)

            # X axis (red)
            self.draw_arrow(
                painter,
                QPointF(self.px0, self.py0),
                QPointF(self.px1, self.py0),
                QColor(220, 0, 0),
            )

            # Y axis (green)
            self.draw_arrow(
                painter,
                QPointF(self.px0, self.py0),
                QPointF(self.px0, self.py1),
                QColor(0, 180, 0),
            )

            if not self.curvePts:
                return

            cColor = self.curveColor
            pen = QPen(cColor, 2)
            painter.setPen(pen)
            painter.setBrush(cColor)
            
            rectSize = self.rectSize
            half = rectSize / 2

            for i in range(len(self.curvePts)):
                _, _, x, y = self.curvePts[i]
                painter.drawRect(int(x-half), int(y-half), rectSize, rectSize)
                if i < len(self.curvePts) - 1:
                    painter.drawLine(
                        QPointF(self.curvePts[i][2], self.curvePts[i][3]),
                        QPointF(self.curvePts[i+1][2], self.curvePts[i+1][3])
                    )

    def draw_arrow(self, painter, p0, p1, color):
        pen = QPen(color, 4)
        painter.setPen(pen)
        painter.drawLine(p0, p1)

        angle = math.atan2(p1.y()-p0.y(), p1.x()-p0.x())
        size = 10
        left = QPointF(
            p1.x() - size*math.cos(angle-math.pi/6),
            p1.y() - size*math.sin(angle-math.pi/6),
        )
        right = QPointF(
            p1.x() - size*math.cos(angle+math.pi/6),
            p1.y() - size*math.sin(angle+math.pi/6),
        )
        painter.drawLine(p1, left)
        painter.drawLine(p1, right)

    def find_point(self, pos, radius=None):
        if self.parent() is None:
            return None
    
        if not radius:
            radius = self.rectSize
    
        # Search for nearest point in currently 
        # chosen curve
        gui = self.parent()
        cname = gui.current_curve;
        for i,(_,_,px,py) in enumerate(self.curvePts):
            if (pos.x()-px)**2 + (pos.y()-py)**2 <= radius**2:
                return cname, i
        
        return None,-1
    
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plot Extractor by RF With Care")

        self.image_label = ImageView()
        self.image_label.clicked.connect(self.on_click)
        self.image = None
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
        
        # curve color button
        self.color_btn = QPushButton()
        # self.color_btn.setFixedSize(30, 30)
        self.color_btn.clicked.connect(self.choose_color)
        self.curveColor = QColor(50, 50, 255) # Initialize as blue
        self.set_color_button(self.curveColor)
        
        self.curve_list = QListWidget()
        self.curve_list.currentRowChanged.connect(self.on_curve_changed)
        
        # Initialize curve dictionary
        self.curves = {}
        self.current_curve = None
        
        self.add_curve_btn = QPushButton("Add Curve")
        self.add_curve_btn.clicked.connect(self.add_curve)
        
        self.point_edit_btn = QPushButton("Current mode: Add Points")
        self.point_edit_btn.setCheckable(True)
        self.point_edit_btn.clicked.connect(self.switch_edit_add)
        self.addPointsMode = True
        
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["X", "Y"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setColumnWidth(2, 40)   # small delete button column

        # guard flag to prevent recursion
        self._updating_table = False
        self.table.itemChanged.connect(self.on_table_item_changed)

        self.export_csv_btn = QPushButton("Export As CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)

        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self.reset_all)
        
        self.layout_ui()
        if self.image:
            self.update_axes_drawn()
            
        self.last_path = ""
        
        # Disable all buttons
        self.enableButtons(False)

    def eventFilter(self, obj, event):
        if obj is self.image_label and event.type() == event.Resize:
            self.cImgW = self.image_label.width()
            self.cImgH = self.image_label.height()

            if self.image:
                self.update_axes_drawn()

                if self.current_curve:
                    rW = self.cImgW/self.oImgW
                    rH = self.cImgH/self.oImgH
                    pts = self.curves[self.current_curve]
                    self.image_label.set_curve_pixels(pts, rW, rH, self.curveColor)

        return super().eventFilter(obj, event)

    def switch_edit_add(self):
        if self.addPointsMode:
            self.point_edit_btn.setText("Current mode: Move/Edit Points")
        else:
            self.point_edit_btn.setText("Current mode: Add Points")
        
        self.table.setEnabled(self.addPointsMode)
        # self.point_edit_btn.setChecked(self.addPointsMode)

        self.addPointsMode = not self.addPointsMode
        self.update_table()

    def layout_ui(self):
        load_btn = QPushButton("Load Image")
        load_btn.clicked.connect(self.load_image)

        form = QFormLayout()
        self.img_size_label = QLabel("Image Size = (N/A,N/A) [px]")
        form.addRow(self.img_size_label)

        form.addRow("CS Start X [px]", self.px0)
        form.addRow("CS Start Y [px]", self.py0)
        form.addRow("CS End X [px]", self.px1)
        form.addRow("CS End Y [px]", self.py1)
        form.addRow("Data X min", self.x0)
        form.addRow("Data X max", self.x1)
        form.addRow("Data Y min", self.y0)
        form.addRow("Data Y max", self.y1)
        form.addRow("X scale", self.xscale)
        form.addRow("Y scale", self.yscale)

        for w in [self.px0, self.py0, self.px1, self.py1]:
            w.textChanged.connect(self.update_axes_drawn)

        left = QVBoxLayout()
        left.addWidget(load_btn)
        left.addWidget(self.image_label)

        right = QVBoxLayout()
        right.addLayout(form)
        
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Curve Color"))
        color_layout.addWidget(self.color_btn)
        right.addLayout(color_layout)
        
        right.addWidget(QLabel("Curves"))
        right.addWidget(self.add_curve_btn)
        right.addWidget(self.curve_list)
        right.addWidget(self.point_edit_btn)
        
        right.addWidget(self.table)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.export_csv_btn)
        btn_row.addWidget(self.reset_btn)
        right.addLayout(btn_row)

        layout = QHBoxLayout()
        layout.addLayout(left, 3)
        layout.addLayout(right, 2)
        self.setLayout(layout)

    def enableButtons(self, en=True):
        for w in [
            self.px0, self.px1, self.py0, self.py1,
            self.x0, self.x1, self.y0, self.y1,
            self.xscale, self.yscale,
            self.point_edit_btn, self.add_curve_btn,
            self.export_csv_btn,
            self.color_btn
        ]:
            w.setEnabled(en)
        
        self.table.setEnabled(not self. addPointsMode)
    
    def set_color_button(self, color):
        self.color_btn.setStyleSheet(
            f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});"
        )
        
    def choose_color(self):
        # if not self.current_curve:
        #     return

        menu = QMenu()

        colors = [
            ("Black", QColor(0, 0, 0)),
            ("White", QColor(255, 255, 255)),
            ("Gray", QColor(128, 128, 128)),
            ("Blue", QColor(50, 50, 255)),
            ("Red", QColor(255, 0, 0)),
            ("Green", QColor(0, 180, 0)),
        ]

        for name, col in colors:
            act = QAction(name, self)
            act.triggered.connect(lambda _, c=col: self.set_curve_color(c))
            menu.addAction(act)

        menu.exec_(QCursor.pos())
    
    def set_curve_color(self, color):
        self.curveColor = color
        
        if not self.current_curve:
            return
        
        self.set_color_button(self.curveColor)
        self.send_curve_to_image()
    
    def export_csv(self):
        if not self.current_curve:
            QMessageBox.information(self, "Export", "No curve is selected")
        pts = self.curves.get(self.current_curve, [])
        if not pts:
            QMessageBox.information(self, "Export", "No points available")
            return

        arr = np.array([(x, y) for (x, y, *_ ) in pts], float)

        default_name = f"{self.current_curve}.csv"
        
        start_dir = self.last_path if self.last_path else ""
        
        # Ask user where to save
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Curve as CSV",
            os.path.join(start_dir, default_name),
            "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
    
        # Get last path
        self.last_path,_ = os.path.split(path)
        
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
            if self.image:
                px0 = float(self.px0.text())
                px1 = float(self.px1.text())
                py0 = self.oImgH - float(self.py0.text())
                py1 = self.oImgH - float(self.py1.text())

                rH = self.cImgH/self.oImgH
                rW = self.cImgW/self.oImgW

                self.image_label.set_axis_pixels(
                    px0*rW, py0*rH, px1*rW, py1*rH
                )
        except Exception:
            pass

    def load_image(self):
        # Define starting directory, if available
        start_dir = self.last_path if self.last_path else ""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Image File",
            start_dir,
            "Image Files (*.bmp *.jpg *.jpeg *.png *.gif);;All Files (*)")
        
        if not path:
            return
        
        # Store last path
        self.last_path, _ = os.path.split(path)
        
        self.image = QPixmap(path)
        self.image_label.set_pixmap(self.image)

        self.cImgW = self.image_label.width()
        self.cImgH = self.image_label.height()
        self.oImgW = self.image.width()
        self.oImgH = self.image.height()

        self.enableButtons(True)

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

    def on_click(self, px, py):
        if not self.current_curve or not self.addPointsMode:
            return

        px0, py0, px1, py1, x0, x1, y0, y1 = self.get_startstop_pixels()

        logx = self.xscale.currentText() == "log"
        logy = self.yscale.currentText() == "log"

        rW = self.oImgW/self.cImgW
        rH = self.oImgH/self.cImgH
        ox = px*rW
        oy = py*rH

        # Invert y axis only while mapping
        x = map_axis(ox             , px0, px1, x0, x1, logx)
        y = map_axis(self.oImgH - oy, py0, py1, y0, y1, logy)
        
        pts = self.curves[self.current_curve]
        pts.append((x, y, ox, oy))
        pts.sort(key=lambda p: p[0])

        self.update_table()
        self.send_curve_to_image()

    def send_curve_to_image(self):
        if not self.current_curve:
            return
        pts = self.curves[self.current_curve]
        rW = self.cImgW/self.oImgW
        rH = self.cImgH/self.oImgH
        self.image_label.set_curve_pixels(pts, rW, rH, self.curveColor)

    def on_curve_changed(self, row):
        if row < 0:
            self.current_curve = None
            self.table.setRowCount(0)
            self.image_label.set_curve_pixels(None, 1, 1, self.curveColor)
            return

        self.current_curve = self.curve_list.item(row).text()
        self.update_table()

    def update_table(self):
        if not self.current_curve:
            self.table.setRowCount(0)
            return

        pts = self.curves[self.current_curve]
        pts.sort(key=lambda p: p[0])
        self.curves[self.current_curve] = pts
        
        self._updating_table = True
        self.table.setRowCount(len(pts))

        editable = not self.addPointsMode
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.SelectedClicked |
            QAbstractItemView.EditKeyPressed
            if editable else QAbstractItemView.NoEditTriggers
        )

        for i, (x, y, _, _) in enumerate(pts):
            self.table.setItem(i, 0, QTableWidgetItem(f"{x:g}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{y:g}"))
            self.add_delete_button(i)

        self._updating_table = False
        self.send_curve_to_image()

    def on_table_item_changed(self, item):
        if self._updating_table or self.addPointsMode or not self.current_curve:
            return

        row = item.row()
        col = item.column()

        try:
            new_val = float(item.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid value", "Please enter a numeric value.")
            self.update_table()
            return

        pts = self.curves[self.current_curve]
        if row >= len(pts):
            return

        # Update 1st or 2nd column
        x, y, _, _ = pts[row]
        if col == 0:
            x = new_val
        else:
            y = new_val

        # Re-calculate the x and y coordinates, in 
        # the *original* image coordinate system
        logx = self.xscale.currentText() == "log"
        logy = self.yscale.currentText() == "log"

        px0, py0, px1, py1, x0, x1, y0, y1 = self.get_startstop_pixels()
        
        ox = inv_map_axis(x, px0, px1, x0, x1, logx)
        oy = inv_map_axis(y, py0, py1, y0, y1, logy)
        
        # Flip oy, as inversion should be done while mapping only
        oy = self.oImgH - oy
        
        pts[row] = (x, y, ox, oy)
        pts.sort(key=lambda p: p[0])
        self.curves[self.current_curve] = pts
        
        self.update_table()
        self.send_curve_to_image()
    
    def add_delete_button(self, row):
        btn = QPushButton("X")
        btn.setFixedWidth(30)
    
        # disable when NOT in edit mode
        btn.setEnabled(not self.addPointsMode)
    
        btn.clicked.connect(lambda _, r=row: self.delete_point(r))
        self.table.setCellWidget(row, 2, btn)

    def delete_point(self, row):
        if self.addPointsMode:
            return  # deletion only in edit mode
    
        if not self.current_curve:
            return
    
        pts = self.curves[self.current_curve]
    
        if 0 <= row < len(pts):
            pts.pop(row)
    
        self.update_table()
 
    def get_startstop_pixels(self):
        px0 = float(self.px0.text())
        py0 = float(self.py0.text())
        px1 = float(self.px1.text())
        py1 = float(self.py1.text())

        x0 = float(self.x0.text())
        x1 = float(self.x1.text())
        y0 = float(self.y0.text())
        y1 = float(self.y1.text())

        return px0, py0, px1, py1, x0, x1, y0, y1        
    
    def reset_all(self):
        self.image = None
        self.image_label.set_pixmap(None)

        self.curves.clear()
        self.curve_list.clear()
        self.table.setRowCount(0)
        self.current_curve = None

        self.enableButtons(False)
        self.img_size_label.setText("Image Size = (N/A,N/A) [px]")

def main():
    app = QApplication(sys.argv)
    w = App()
    w.show()
    # existing code to launch your window goes here
    # e.g. window = MyMainWindow()
    #       window.show()
    sys.exit(app.exec_())

# Optional: allow running this file directly
if __name__ == "__main__":
    main()
