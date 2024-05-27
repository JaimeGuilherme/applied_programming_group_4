from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingException,
                       QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink, QgsProcessingParameterDistance,
                       QgsProcessingParameterString, QgsProcessingParameterField,
                       QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry, QgsPointXY,
                       QgsWkbTypes)
from qgis import processing

class Projeto3Solucao(QgsProcessingAlgorithm):
    # Definição dos identificadores dos parâmetros e saídas
    INPUT_PONTOS = 'INPUT_PONTOS'
    INPUT_DIA_1 = 'INPUT_DIA_1'
    INPUT_DIA_2 = 'INPUT_DIA_2'
    INPUT_TOL = 'INPUT_TOL'
    INPUT_PRIMARY_KEY = 'INPUT_PRIMARY_KEY'
    INPUT_IGNORA = 'INPUT_IGNORA'
    OUTPUT_CURVA = 'OUTPUT_CURVA'
    CREATION_TIME_FIELD = 'creation_time'

    def tr(self, string):
        return QCoreApplication.translate('Projeto3Solucao', string)

    def createInstance(self):
        return Projeto3Solucao()

    def name(self):
        return 'projeto3solucao'

    def displayName(self):
        return self.tr('Solução Projeto 3 - Grupo 4')

    def group(self):
        return self.tr('Exemplos')

    def groupId(self):
        return 'exemplos'

    def shortHelpString(self):
        return self.tr("Este algoritmo é parte da solução do Grupo 4 para identificar as mudanças não coerentes do caminho percorrido pelo reambulador")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_PONTOS, self.tr('Camada de Pontos Percorridos'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_DIA_1, self.tr('Camada do dia 1'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_DIA_2, self.tr('Camada do dia 2'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterDistance(self.INPUT_TOL, self.tr('Distância de Tolerância'), defaultValue=10))
        self.addParameter(QgsProcessingParameterField(self.INPUT_PRIMARY_KEY, self.tr('Chave Primária'), None, self.INPUT_DIA_1))
        self.addParameter(QgsProcessingParameterField(self.INPUT_IGNORA, self.tr('Atributo a ignorar'), None, self.INPUT_DIA_2))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_CURVA, self.tr('Saída de Rota Percorrida'), QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):
        # Obter as camadas e parâmetros de entrada
        pontos_layer = self.parameterAsVectorLayer(parameters, self.INPUT_PONTOS, context)
        dia1_layer = self.parameterAsVectorLayer(parameters, self.INPUT_DIA_1, context)
        dia2_layer = self.parameterAsVectorLayer(parameters, self.INPUT_DIA_2, context)
        tol = self.parameterAsDouble(parameters, self.INPUT_TOL, context)
        primary_key = self.parameterAsString(parameters, self.INPUT_PRIMARY_KEY, context)
        ignora = self.parameterAsString(parameters, self.INPUT_IGNORA, context)

        # Converter a string de atributos a ignorar em uma lista
        ignore_fields = set(ignora.split(',')) if ignora else set()

        # Garantir que o campo "creation_time" exista na camada de pontos
        if self.CREATION_TIME_FIELD not in [field.name() for field in pontos_layer.fields()]:
            raise QgsProcessingException(f'O campo "{self.CREATION_TIME_FIELD}" não foi encontrado na camada de pontos.')

        # Ordenar os pontos pela data de criação
        pontos_features = list(pontos_layer.getFeatures())
        pontos_features.sort(key=lambda feat: feat[self.CREATION_TIME_FIELD])

        # Criar uma linha a partir dos pontos percorridos
        points = [QgsPointXY(feat.geometry().asPoint()) for feat in pontos_features]
        line_geometry = QgsGeometry.fromPolylineXY(points)

        # Criar uma nova camada de linha para a saída
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT_CURVA, context, pontos_layer.fields(), QgsWkbTypes.LineString, pontos_layer.sourceCrs())

        # Adicionar a linha como uma feição na camada de saída
        new_feature = QgsFeature()
        new_feature.setGeometry(line_geometry)
        sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        # Comparar os pontos dos dias e identificar mudanças não coerentes
        dia1_features = {feat[primary_key]: feat for feat in dia1_layer.getFeatures()}
        dia2_features = {feat[primary_key]: feat for feat in dia2_layer.getFeatures()}

        incoherent_changes = []

        for key in dia1_features:
            if key in dia2_features:
                geom1 = dia1_features[key].geometry()
                geom2 = dia2_features[key].geometry()
                if geom1.distance(geom2) > tol:
                    incoherent_changes.append(key)

        if incoherent_changes:
            feedback.pushInfo(f'Mudanças não coerentes encontradas nas chaves primárias: {", ".join(map(str, incoherent_changes))}')
        
        return {self.OUTPUT_CURVA: dest_id}

# Para registrar o algoritmo no QGIS
def register_algorithms():
    QgsApplication.processingRegistry().addAlgorithm(Projeto3Solucao())
