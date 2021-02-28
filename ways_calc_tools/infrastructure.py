from qgis.PyQt.QtWidgets import QTableWidgetItem
from qgis.PyQt.QtCore import Qt

class CommonTools:
    
    @staticmethod
    def createTableItem(column_name, layer, value):
        idx_field = layer.fields().indexFromName(column_name)
        field_type = layer.editorWidgetSetup(idx_field).type()

        # value = self.layer_current_selected_fs[rownum][column_name]

        # подставляем значения в соответствии с заданными справочниками в виджетах
        if field_type == 'ValueMap':
            valuemap = layer.editorWidgetSetup(idx_field).config()['map']
            # почему-то некоторые "Карты значений" представлены в виде словарей,
            # а некоторые в виде списков словарей. Объединяем последние в словари
            if isinstance(valuemap, list): 
                newvaluemap = {}
                for d in valuemap:
                    newvaluemap[list(d.keys())[0]] = d[list(d.keys())[0]]
                valuemap = newvaluemap

            # если число как строка или float, то преобразуем его в int.
            # т.е. '1' или 1.0 в 1 
            if isinstance(value, str):
                if value.isnumeric():
                    value = int(value)
            if isinstance(value, float):
                value = int(value)
            # значение из словаря
            value = list(valuemap.keys())[list(valuemap.values()).index(str(value))]

        item = QTableWidgetItem()
        item.setData(Qt.EditRole, value)
        return item


    @staticmethod
    def populateTableByClickedFeatures(layer, table):
        header_labels_list = []
        header_labels_list.append('feature_id')
        field_aliases_dict = layer.attributeAliases()
        for k in field_aliases_dict.keys():
            field = field_aliases_dict[k] if field_aliases_dict[k] else k
            header_labels_list.append(field)

        layer_current_selected_fs = []
        for feature in layer.selectedFeatures():
            feature_attributes_dict = {}
            feature_attributes_dict["feature_id"]=feature.id()
            for field_name in field_aliases_dict.keys():
                feature_attributes_dict[field_name] = feature[field_name]
            layer_current_selected_fs.append(feature_attributes_dict)

        features_cnt = layer.selectedFeatureCount()
        columns_cnt = len(header_labels_list)
        table.setRowCount(features_cnt)
        table.setColumnCount(columns_cnt)

        for rownum in range(features_cnt):
            for f_idx, fieldname in enumerate(layer_current_selected_fs[0].keys()):
                attr_value = layer_current_selected_fs[rownum][fieldname]
                # item = self.createTableItem(rownum, fieldname, self.layer_current, attr_value)
                item = CommonTools.createTableItem(fieldname, layer, attr_value)
                table.setItem(rownum, f_idx, item)

        table.setHorizontalHeaderLabels(header_labels_list)
        table.resizeColumnsToContents()
        table.setColumnHidden(0, True)
        return layer_current_selected_fs