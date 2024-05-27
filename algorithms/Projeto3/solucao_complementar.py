from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingException,
                       QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterDistance,
                       QgsProcessingParameterField, QgsProcessingParameterEnum,
                       QgsFeature, QgsGeometry, QgsPointXY, QgsWkbTypes, QgsApplication,
                       QgsField, QgsFields)
from qgis.PyQt.QtCore import QVariant

class Projeto3SolucaoComplementar(QgsProcessingAlgorithm):
    INPUT_PONTOS = 'INPUT_PONTOS'
    INPUT_DIA_1 = 'INPUT_DIA_1'
    INPUT_DIA_2 = 'INPUT_DIA_2'
    INPUT_TOL = 'INPUT_TOL'
    INPUT_PRIMARY_KEY = 'INPUT_PRIMARY_KEY'
    INPUT_IGNORA = 'INPUT_IGNORA'
    OUTPUT_CURVA = 'OUTPUT_CURVA'
    OUTPUT_MODIFICADOS = 'OUTPUT_MODIFICADOS'
    OUTPUT_BUFFER = 'OUTPUT_BUFFER'
    OUTPUT_MODIFICADOS_FORA = 'OUTPUT_MODIFICADOS_FORA'

    def tr(self, string):
        return QCoreApplication.translate('Projeto3SolucaoComplementar', string)

    def createInstance(self):
        return Projeto3SolucaoComplementar()

    def name(self):
        return 'projeto3solucaocomplementar'

    def displayName(self):
        return self.tr('Solução Complementar Projeto 3 - Grupo 4')

    def group(self):
        return self.tr('Exemplos')

    def groupId(self):
        return 'exemplos'

    def shortHelpString(self):
        return self.tr("Identifica e extrai geometrias modificadas fora do buffer.")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_PONTOS, self.tr('Camada de Pontos'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_DIA_1, self.tr('Camada do Dia 1'), [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_DIA_2, self.tr('Camada do Dia 2'), [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterDistance(self.INPUT_TOL, self.tr('Distância de Tolerância'), defaultValue=10))
        self.addParameter(QgsProcessingParameterField(self.INPUT_PRIMARY_KEY, self.tr('Chave Primária'), None, self.INPUT_DIA_1))
        self.addParameter(QgsProcessingParameterEnum(self.INPUT_IGNORA, self.tr('Atributos a ignorar'), [], allowMultiple=True, optional=True))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_CURVA, self.tr('Saída de Rota Percorrida'), QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_MODIFICADOS, self.tr('Geometrias Modificadas'), QgsProcessing.TypeVectorAnyGeometry))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_BUFFER, self.tr('Buffer da Rota'), QgsProcessing.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_MODIFICADOS_FORA, self.tr('Geometrias Modificadas Fora do Buffer'), QgsProcessing.TypeVectorAnyGeometry))

    def processAlgorithm(self, parameters, context, feedback):
        pontos_layer = self.parameterAsVectorLayer(parameters, self.INPUT_PONTOS, context)
        dia1_layer = self.parameterAsVectorLayer(parameters, self.INPUT_DIA_1, context)
        dia2_layer = self.parameterAsVectorLayer(parameters, self.INPUT_DIA_2, context)
        tol = self.parameterAsDouble(parameters, self.INPUT_TOL, context)
        primary_key = self.parameterAsString(parameters, self.INPUT_PRIMARY_KEY, context)
        ignora_indexes = self.parameterAsEnums(parameters, self.INPUT_IGNORA, context)

        pontos_features = sorted(pontos_layer.getFeatures(), key=lambda feat: feat['creation_time'])
        line_geometry = QgsGeometry.fromPolylineXY([QgsPointXY(feat.geometry().asPoint()) for feat in pontos_features])
        (line_sink, line_dest_id) = self.parameterAsSink(parameters, self.OUTPUT_CURVA, context, pontos_layer.fields(), QgsWkbTypes.LineString, pontos_layer.sourceCrs())
        line_feature = QgsFeature()
        line_feature.setGeometry(line_geometry)
        line_sink.addFeature(line_feature, QgsFeatureSink.FastInsert)

        buffer_geometry = line_geometry.buffer(tol, 20)
        (buffer_sink, buffer_dest_id) = self.parameterAsSink(parameters, self.OUTPUT_BUFFER, context, pontos_layer.fields(), QgsWkbTypes.Polygon, pontos_layer.sourceCrs())
        buffer_feature = QgsFeature()
        buffer_feature.setGeometry(buffer_geometry)
        buffer_sink.addFeature(buffer_feature, QgsFeatureSink.FastInsert)

        dia1_features = {feat[primary_key]: feat for feat in dia1_layer.getFeatures()}
        dia2_features = {feat[primary_key]: feat for feat in dia2_layer.getFeatures()}
        modified_features = []
        modified_features_outside_buffer = []

        new_fields = QgsFields()
        for field in dia1_layer.fields():
            new_fields.append(field)
        new_fields.append(QgsField("Tipo de Mudança", QVariant.String))
        new_fields.append(QgsField("Atributos Modificados", QVariant.String))

        # Criando sink para as features modificadas
        (mod_sink, mod_dest_id) = self.parameterAsSink(parameters, self.OUTPUT_MODIFICADOS, context, new_fields, dia1_layer.wkbType(), dia1_layer.sourceCrs())

        # Criando sink para as features modificadas fora do buffer
        (mod_out_sink, mod_out_dest_id) = self.parameterAsSink(parameters, self.OUTPUT_MODIFICADOS_FORA, context, new_fields, dia1_layer.wkbType(), dia1_layer.sourceCrs())

        ignore_fields = {dia1_layer.fields().fieldName(i) for i in ignora_indexes}
        ignore_fields.update(['fid', 'id'])

        for key in dia1_features:
            if key in dia2_features:
                feat1 = dia1_features[key]
                feat2 = dia2_features[key]
                geometry_changed = feat1.geometry().distance(feat2.geometry()) > tol
                if geometry_changed:
                    change_type = "Feição Modificada"
                    changed_attributes = ["geometria"]
                else:
                    changed_attributes = [field for field in feat1.fields().names() if feat1[field] != feat2[field] and field not in ignore_fields]
                    change_type = "Feição Modificada" if changed_attributes else None

                if change_type:
                    new_feat = QgsFeature(new_fields)
                    new_feat.setGeometry(feat2.geometry())
                    new_feat.setAttributes(feat2.attributes() + [change_type, ",".join(changed_attributes)])
                    modified_features.append(new_feat)
                    mod_sink.addFeature(new_feat, QgsFeatureSink.FastInsert)
                    if not buffer_geometry.contains(new_feat.geometry()):
                        modified_features_outside_buffer.append(new_feat)
                        mod_out_sink.addFeature(new_feat, QgsFeatureSink.FastInsert)

        for key in dia2_features:
            if key not in dia1_features:
                feat2 = dia2_features[key]
                new_feat = QgsFeature(new_fields)
                new_feat.setGeometry(feat2.geometry())
                new_feat.setAttributes(feat2.attributes() + ["Feição Adicionada", primary_key])
                modified_features.append(new_feat)
                mod_sink.addFeature(new_feat, QgsFeatureSink.FastInsert)
                if not buffer_geometry.contains(new_feat.geometry()):
                    modified_features_outside_buffer.append(new_feat)
                    mod_out_sink.addFeature(new_feat, QgsFeatureSink.FastInsert)

        for key in dia1_features:
            if key not in dia2_features:
                feat1 = dia1_features[key]
                new_feat = QgsFeature(new_fields)
                new_feat.setGeometry(feat1.geometry())
                new_feat.setAttributes(feat1.attributes() + ["Feição Removida", primary_key])
                modified_features.append(new_feat)
                mod_sink.addFeature(new_feat, QgsFeatureSink.FastInsert)
                if not buffer_geometry.contains(new_feat.geometry()):
                    modified_features_outside_buffer.append(new_feat)
                    mod_out_sink.addFeature(new_feat, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT_CURVA: line_dest_id,
            self.OUTPUT_MODIFICADOS: mod_dest_id,
            self.OUTPUT_BUFFER: buffer_dest_id,
            self.OUTPUT_MODIFICADOS_FORA: mod_out_dest_id
        }

def register_algorithms():
    QgsApplication.processingRegistry().addAlgorithm(Projeto3SolucaoComplementar())
