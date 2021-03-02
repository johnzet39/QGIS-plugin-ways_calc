"""
/***************************************************************************
 WaysCalc
                                 A QGIS plugin
 ways calculator
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-02-25
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Zlatanov Evgeniy
        email                : johnzet@yandex.ru
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QObject, QVariant
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QAction, QTableWidgetItem, QListWidget, QListWidgetItem, QDialogButtonBox
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes, QgsRectangle,
    QgsMapLayerProxyModel,
    QgsGeometry
)
from qgis.gui import (
        QgsMapToolEmitPoint,
        QgsHighlight
)
# Initialize Qt resources from file resources.py

# Import the code for the DockWidget
from ..ways_calc_select_layers_dialog import WaysCalcSelectLayerDialog
from ..ways_calc_click_res_dialog import WaysCalcClickResDialog
from .infrastructure import CommonTools

import json
import os

class IntersectionWays:
    def __init__(self, iface, dockWidget):
        self.iface = iface
        self.dockWidget = dockWidget
        self.plugin_dir = os.path.dirname(__file__)
        print('init')

        self.map_clicked_dlg = WaysCalcClickResDialog()
        self.sel_layer_dlg = WaysCalcSelectLayerDialog()
        self.buttonOk = self.map_clicked_dlg.button_box.button( QDialogButtonBox.Ok )

        self.inters_layer = None # слой сравнения
        self.current_layer = None # текущий выбранный слой
        self.current_layer_selected_fs = None # объекты, которые попали под курсор на карте (лист словарей)

        self.settings = None
        self.settings_layer = None

        self.mapclicked_h_list = []
        self.onLoadModule()


    def onLoadModule(self):
        print('loadModule')
        self.map_clicked_dlg.tableClickedWays.itemSelectionChanged.connect(self.onMapClickedTableSelChanged)
        self.dockWidget.visibilityChanged.connect(self.onDockVisibilityChanged)
        self.initSettings()


    def onUnLoadModule(self):
        print('unloadModule')
        self.map_clicked_dlg.tableClickedWays.itemSelectionChanged.disconnect(self.onMapClickedTableSelChanged)
        self.dockWidget.visibilityChanged.disconnect(self.onDockVisibilityChanged)
        
        self.clearMapselectedHighlight()

    def initSettings(self):
        with open(os.path.join(self.plugin_dir, "..\settings.json"), "r") as read_file:
            self.settings = json.load(read_file)


    def onDockVisibilityChanged(self):
        if self.dockWidget.isHidden():
            self.clearMapselectedHighlight()
            self.current_layer.removeSelection()

    def onMapClickedTableSelChanged(self):
        cur_row_index = self.map_clicked_dlg.tableClickedWays.currentRow()
        if cur_row_index > -1:
            self.clearMapselectedHighlight()

            f_geometry = QgsGeometry()
            f_geometry = QgsGeometry.fromWkt(
                    self.map_clicked_dlg.tableClickedWays.item(cur_row_index, 1).text())

            h = QgsHighlight(self.iface.mapCanvas(), f_geometry, self.current_layer)
            h.setColor(QColor(0,100,200,220))
            h.setWidth(6)
            h.setFillColor(QColor(0,150,200,150))
            self.mapclicked_h_list.append(h)

        self.setButtonOkStatus()


    def setButtonOkStatus(self):
        if self.map_clicked_dlg.tableClickedWays.currentRow() > -1:
            self.buttonOk.setEnabled(True)
        else:
            self.buttonOk.setEnabled(False)


    def clearMapselectedHighlight(self):
        for i, h in enumerate(self.mapclicked_h_list):
            self.mapclicked_h_list.pop(i)
            self.iface.mapCanvas().scene().removeItem(h)


    def __del__(self):
        print('deleted')


    def initLayerWays(self, current_layer = None):
        self.sel_layer_dlg.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.LineLayer)
        if current_layer is not None:
            if current_layer.geometryType() ==  QgsWkbTypes.LineGeometry:
                self.sel_layer_dlg.mMapLayerComboBox.setLayer(current_layer)
        self.sel_layer_dlg.show()
        result = self.sel_layer_dlg.exec_()
        if result:
            self.inters_layer = self.sel_layer_dlg.mMapLayerComboBox.currentLayer()
            self.settings_layer = self.settings["modules"]["intersection_ways"]["layers"].get(self.inters_layer.name())
            self.clearFiltersDlg() # очистить форму от фильтров
            self.addFiltersDlg() # добавить фильтры на форму


    def checkLayers(self):
        current_layer = self.iface.activeLayer()
        if (current_layer is not None and
                type(current_layer) == QgsVectorLayer and
                current_layer.geometryType() ==  QgsWkbTypes.LineGeometry):
            self.current_layer = current_layer
        else:
            self.iface.messageBar().pushMessage(f'Выберите векторный линейный слой, содержащий объект сравнения', f'', duration=5, level=2)
            return False

        if self.inters_layer is None:
            self.initLayerWays(current_layer)

        if self.current_layer is None or self.inters_layer is None:
            return False
        return True
    
    
    def insersection_take_way(self, point):
        self.current_layer.removeSelection()
        width = self.iface.mapCanvas().mapUnitsPerPixel() * 5
        rect = QgsRectangle(point.x() - width,
            point.y() - width,
            point.x() + width,
            point.y() + width)
        self.current_layer.selectByRect(rect)

        if self.current_layer.selectedFeatureCount() > 0:
            # self.iface.messageBar().clearWidgets()
            self.showClickedFeaturesList()


    def showClickedFeaturesList(self):
        table = self.map_clicked_dlg.tableClickedWays
        table.reset()
        self.current_layer_selected_fs = []
        self.current_layer_selected_fs = CommonTools.populateTableByClickedFeatures(
                                                self.current_layer, table)

        self.current_layer.removeSelection()

        self.setButtonOkStatus()
        self.map_clicked_dlg.show()
        result = self.map_clicked_dlg.exec_()
        if result:
            self.calcIntersects()
            self.dockWidget.show()
        else:
            self.clearMapselectedHighlight()


    def clearFiltersDlg(self):
        CommonTools.clearFiltersLayout(self.map_clicked_dlg.groupBox_filter.layout())


    def addFiltersDlg(self):
        if self.settings["modules"].get("intersection_ways") is not None:
            if self.settings_layer is not None:
                ava_filters_fields = self.settings_layer.get("filters_fields")
                if ava_filters_fields is not None:
                    for field in ava_filters_fields:
                        CommonTools.addFilter(
                            field,
                            self.inters_layer,
                            self.map_clicked_dlg.groupBox_filter.layout(),
                            self.settings_layer)

                    
    def calcIntersects(self):
        current_feature_idx = self.map_clicked_dlg.tableClickedWays.currentRow()
        current_feature_id = int(self.map_clicked_dlg.tableClickedWays.item(current_feature_idx, 0).text())
        current_feature = self.current_layer.getFeature(current_feature_id)   

        # field_percent_json = self.settings_layer["filters_fields"].get("_percent")
        # if field_percent_json is not None:
        filters_dict = {}
        for fieldname in self.settings_layer["filters_fields"]:
            filters_dict[fieldname] = CommonTools.getFilterValues(fieldname, self.map_clicked_dlg.groupBox_filter.layout())
            print(filters_dict)

        if self.settings_layer is not None:
            buffer_size = float(self.settings_layer.get("buffer_size", ".0"))
        else:
            buffer_size = .0

        cf_buffer = current_feature.geometry().buffer(buffer_size, 5)

        for intfeat in self.inters_layer.getFeatures():
            if intfeat.id() == current_feature_id and self.current_layer == self.inters_layer: #отсекаем сравниваемую линию
                continue
            if intfeat.geometry().intersects(cf_buffer):
                intfeat_buffer = intfeat.geometry().buffer(buffer_size, 5) # буфер пересекающихся линий, для отображения пересечений
                intersection_buffers = QgsGeometry(cf_buffer).intersection(intfeat_buffer) # для отображения пересечений
                intersection_line = QgsGeometry(current_feature.geometry()).intersection(intfeat_buffer) # части текущей линии, которые попали в буфер сравниваемого объекта

                intfeat_length = intfeat.geometry().length()
                intersection_line_length = intersection_line.length()

