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

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QObject
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QTableWidgetItem
from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes, QgsRectangle, QgsMapLayerProxyModel
from qgis.gui import QgsMapToolEmitPoint
# Initialize Qt resources from file resources.py

# Import the code for the DockWidget
from ..ways_calc_select_layers_dialog import WaysCalcSelectLayerDialog
from ..station_ways_click_res_dialog import WaysCalcClickResDialog
from .infrastructure import CommonTools

class IntersectionWays:
    def __init__(self, iface, dockWidget):
        self.iface = iface
        self.dockWidget = dockWidget
        print('init')

        self.map_clicked_dlg = WaysCalcClickResDialog()
        self.sel_layer_dlg = WaysCalcSelectLayerDialog()

        self.layer_ways = None
        self.layer_current = None
        self.layer_current_selected_fs = None
        # self.dockwidget.show()

        self.onLoadModule()

    def onLoadModule(self):
        print('loadModule')
        self.map_clicked_dlg.tableClickedWays.itemSelectionChanged.connect(self.onMapClickedTableSeChanged)

    def onUnLoadModule(self):
        print('unloadModule')
        self.map_clicked_dlg.tableClickedWays.itemSelectionChanged.disconnect(self.onMapClickedTableSeChanged)

    def onMapClickedTableSeChanged(self):
        print('aaaa')

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
            self.layer_ways = self.sel_layer_dlg.mMapLayerComboBox.currentLayer()


    def checkLayers(self):
        current_layer = self.iface.activeLayer()
        if (current_layer is not None and
                type(current_layer) == QgsVectorLayer and
                current_layer.geometryType() ==  QgsWkbTypes.LineGeometry):
            self.layer_current = current_layer
        else:
            self.iface.messageBar().pushMessage(f'Выберите векторный линейный слой, содержащий объект сравнения', f'', duration=5, level=2)
            return False

        if self.layer_ways is None:
            self.initLayerWays(current_layer)

        if self.layer_current is None or self.layer_ways is None:
            return False
        return True
    
    
    def insersection_take_way(self, point):
        self.layer_current.removeSelection()
        width = self.iface.mapCanvas().mapUnitsPerPixel() * 5
        rect = QgsRectangle(point.x() - width,
            point.y() - width,
            point.x() + width,
            point.y() + width)
        self.layer_current.selectByRect(rect)

        if self.layer_current.selectedFeatureCount() > 0:
            # self.iface.messageBar().clearWidgets()
            self.showClickedFeaturesList()


    def showClickedFeaturesList(self):
        table = self.map_clicked_dlg.tableClickedWays
        self.layer_current_selected_fs = []
        self.layer_current_selected_fs = CommonTools.populateTableByClickedFeatures(
                                                self.layer_current, table)

        self.map_clicked_dlg.show()


    # def showClickedFeaturesList(self):
    #     if self.map_clicked_dlg is None:
    #         self.map_clicked_dlg = WaysCalcClickResDialog()

    #     header_labels_list = []
    #     header_labels_list.append('feature_id')
    #     field_aliases_dict = self.layer_current.attributeAliases()
    #     for k in field_aliases_dict.keys():
    #         field = field_aliases_dict[k] if field_aliases_dict[k] else k
    #         header_labels_list.append(field)

    #     self.layer_current_selected_fs = []
    #     for feature in self.layer_current.selectedFeatures():
    #         feature_attributes_dict = {}
    #         feature_attributes_dict["feature_id"]=feature.id()
    #         for field_name in field_aliases_dict.keys():
    #             feature_attributes_dict[field_name] = feature[field_name]
    #         self.layer_current_selected_fs.append(feature_attributes_dict)

    #     features_cnt = self.layer_current.selectedFeatureCount()
    #     columns_cnt = len(header_labels_list)
    #     self.map_clicked_dlg.tableClickedWays.setRowCount(features_cnt)
    #     self.map_clicked_dlg.tableClickedWays.setColumnCount(columns_cnt)

    #     for rownum in range(features_cnt):
    #         for f_idx, fieldname in enumerate(self.layer_current_selected_fs[0].keys()):
    #             attr_value = self.layer_current_selected_fs[rownum][fieldname]
    #             # item = self.createTableItem(rownum, fieldname, self.layer_current, attr_value)
    #             item = CommonTools.createTableItem(fieldname, self.layer_current, attr_value)
    #             self.map_clicked_dlg.tableClickedWays.setItem(rownum, f_idx, item)


    #     self.map_clicked_dlg.tableClickedWays.setHorizontalHeaderLabels(header_labels_list)
    #     self.map_clicked_dlg.tableClickedWays.resizeColumnsToContents()
    #     self.map_clicked_dlg.tableClickedWays.setColumnHidden(0, True)

    #     self.map_clicked_dlg.show()