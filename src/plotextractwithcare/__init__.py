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

"""
plotextractwithCare — a simple tool to manually extract graph curves to CSV.

This file makes the package importable:
    import plotextractwithcare
"""

from .plot_extractor_gui import main

__all__ = ["main"]
