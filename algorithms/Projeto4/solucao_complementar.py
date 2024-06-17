from collections import defaultdict
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsProcessing, QgsFeatureSink, QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink, QgsFeature, QgsGeometry, QgsWkbTypes, 
    QgsApplication, QgsProcessingProvider, QgsFields, QgsField, QgsProcessingException, QgsFeatureRequest
)
from qgis import processing

class Projeto4SolucaoComplementar(QgsProcessingAlgorithm):
    INPUT_PONTOS = 'INPUT_PONTOS'
    INPUT_DRENAGEM = 'INPUT_DRENAGEM'
    INPUT_VIA = 'INPUT_VIA'
    INPUT_BARRAGEM = 'INPUT_BARRAGEM'
    INPUT_MASSA_DAGUA = 'INPUT_MASSA_DAGUA'
    OUTPUT_ERRORS = 'OUTPUT_ERRORS'

    def tr(self, string):
        return QCoreApplication.translate('Projeto4SolucaoComplementar', string)
    def createInstance(self):
        return Projeto4SolucaoComplementar()

    def name(self):
        return 'Projeto4solucaocomplementar'

    def displayName(self):
        return self.tr('Solução Complementar Projeto 4 - Grupo 4')

    def group(self):
        return self.tr('Exemplos')

    def groupId(self):
        return 'exemplos'

    def shortHelpString(self):
        return self.tr("Valida os dados conforme regras específicas e identifica erros.")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_PONTOS, self.tr('Camada de Pontos'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_DRENAGEM, self.tr('Camada de Trecho de Drenagem'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_VIA, self.tr('Camada de Via de Deslocamento'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_BARRAGEM, self.tr('Camada de Barragem'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_MASSA_DAGUA, self.tr('Camada de Massa d\'Água'), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_ERRORS, self.tr('Camada de Erros'), QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        pontos_layer = self.parameterAsVectorLayer(parameters, self.INPUT_PONTOS, context)
        drenagem_layer = self.parameterAsVectorLayer(parameters, self.INPUT_DRENAGEM, context)
        via_layer = self.parameterAsVectorLayer(parameters, self.INPUT_VIA, context)
        barragem_layer = self.parameterAsVectorLayer(parameters, self.INPUT_BARRAGEM, context)
        massa_dagua_layer = self.parameterAsVectorLayer(parameters, self.INPUT_MASSA_DAGUA, context)
        
        fields = QgsFields()
        fields.append(QgsField("erro", QVariant.String))
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT_ERRORS, context, fields, QgsWkbTypes.Point, pontos_layer.crs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_ERRORS))

        def add_error(geometry, message):
            feature = QgsFeature()
            feature.setGeometry(geometry)
            feature.setAttributes([message])
            sink.addFeature(feature, QgsFeatureSink.FastInsert)


        # Regra 6: Borda de represa/açude deve coincidir com barragem
        for massa in massa_dagua_layer.getFeatures():
            valid = False
            for barragem in barragem_layer.getFeatures():
                if massa.geometry().intersects(barragem.geometry()):
                    valid = True
                    break
            if not valid:
                add_error(massa.geometry().centroid(), "Erro na borda da represa/açude")

        # Regra 7: Atributo "sobreposto_transportes" das barragens deve estar correto
        for barragem in barragem_layer.getFeatures():
            sobreposto_transportes = "Não"
            for via in via_layer.getFeatures():
                if barragem.geometry().intersects(via.geometry()):
                    sobreposto_transportes = "Sim"
                    break
            if barragem["sobreposto_transportes"] != sobreposto_transportes:
                add_error(barragem.geometry().centroid(), "Erro no atributo sobreposto_transportes")

        return {self.OUTPUT_ERRORS: dest_id}

def register_algorithms():
    QgsApplication.processingRegistry().addAlgorithm(Projeto4SolucaoComplementar())
