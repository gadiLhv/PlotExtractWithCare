# Plot Extractor / Curve Digitizer

Plot Extractor (with care) is a simple PyQt-based tool that allows you to digitize data points from plotted curves inside images.
Load a graph image, define the coordinate system, add curves, and click points — the tool converts pixel clicks into real-world X/Y values (linear or logarithmic) and exports them to CSV.

## ✨ Features

✔ Load an image file (JPG/PNG/BMP etc.)

✔ Define the chart coordinate system manually (in pixels)

✔ Support for linear or logarithmic X/Y axes

✔ Add multiple curves with names & colors

✔ Click to create ordered data points per-curve

✔ Optional point-editing mode

✔ Normalizes pixel coordinates properly even if the window is resized

✔ Export curve data to CSV files

✔ Last-saved folder remembered when exporting

## 🖥️ Screenshot (optional)

(Add a screenshot here if you want — users really appreciate it!)

## 🚀 Installation
### Requirements

* Python 3.8+

* PyQt5

* NumPy

### Install dependencies:

`pip install pyqt5 numpy`

(Add others like matplotlib if you later use them.)

▶️ Running the Application
`python curve_digitizer.py`

## 📌 How It Works

### Load an image

Enter the pixel locations of the origin and axis endpoints

Enter the real-world coordinate values (min/max for X and Y)

Choose whether X and Y are linear or log scale

Add a curve and begin clicking points

Export your data to CSV when done 🎉

Points are always kept sorted by X-value automatically.

### 📝 CSV Export Format

Exports contain two columns:

`
x,y
1.23,4.56
...
`

## ⚠️ Disclaimer

Curve Digitizer is provided without any warranty.
See the license section for more details.

## 📄 License

### Plot Extractor (with care) 
Copyright © 2026 Gadi Lahav — RF With Care
Contact: gadi@rfwithcare.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3 (GPLv3) or (at your option) any later version.

You should have received a copy of the GNU General Public License along with this program.
If not, see: https://www.gnu.org/licenses/

### 🤝 Contributing

Pull requests and feature suggestions are welcome!

### 🙏 Acknowledgements

Thanks to the open-source community for the tools and libraries that make this possible
