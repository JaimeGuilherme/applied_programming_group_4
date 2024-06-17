from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingException, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterFeatureSink,
                       QgsFeature, QgsGeometry, QgsPointXY, QgsWkbTypes, QgsApplication,
                       QgsProcessingProvider, QgsFields, QgsField, QgsFeatureRequest, QgsVectorLayer)
from collections import defaultdict
import processing
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsWkbTypes,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY,
                       QgsFields,
                       QgsField,
                       QgsFeatureRequest)
from qgis import processing
from collections import defaultdict

class Projeto4Solucao(QgsProcessingAlgorithm):
    INPUT_PONTOS = 'INPUT_PONTOS'
    INPUT_DRENAGEM = 'INPUT_DRENAGEM'
    INPUT_VIA = 'INPUT_VIA'
    INPUT_BARRAGEM = 'INPUT_BARRAGEM'
    INPUT_MASSA_DAGUA = 'INPUT_MASSA_DAGUA'
    OUTPUT_ERRORS = 'OUTPUT_ERRORS'

    def tr(self, string):
        return QCoreApplication.translate('Projeto4Solucao', string)

    def createInstance(self):
        return Projeto4Solucao()

    def name(self):
        return 'projeto4solucao'

    def displayName(self):
        return self.tr('Solução Projeto 4 - Grupo 4')

    def group(self):
        return self.tr('Exemplos')

    def groupId(self):
        return 'exemplos'

    def shortHelpString(self):
        return self.tr("Valida os dados conforme regras específicas e identifica erros.")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_PONTOS, self.tr('Camada de Pontos'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_DRENAGEM, self.tr('Camada de Trecho de Drenagem'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_VIA, self.tr('Camada de Via de Deslocamento'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_BARRAGEM, self.tr('Camada de Barragem'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_MASSA_DAGUA, self.tr('Camada de Massa d\'Água'), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_ERRORS, self.tr('Camada de Erros'), QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        pontos_layer = self.parameterAsVectorLayer(parameters, self.INPUT_PONTOS, context)
        via_layer = self.parameterAsVectorLayer(parameters, self.INPUT_VIA, context)
        drenagem_layer = self.parameterAsVectorLayer(parameters, self.INPUT_DRENAGEM, context)
        
        error_fields = QgsFields(pontos_layer.fields())
        error_fields.append(QgsField('Error_Desc', QVariant.String))
        
        (error_sink, error_id) = self.parameterAsSink(parameters, self.OUTPUT_ERRORS, context,
                                                    error_fields, QgsWkbTypes.Point, via_layer.sourceCrs())

        all_errors = []
        
        # Executar o algoritmo de interseções de linha
        # Processamento para encontrar interseções entre camadas
        intersection_result = processing.run("native:lineintersections", {
            'INPUT': drenagem_layer,
            'INTERSECT': via_layer,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)

        # Verificar interseções nos vértices de qualquer uma das geometrias
        for feature in intersection_result['OUTPUT'].getFeatures():
            intersection_point = feature.geometry().asPoint()
            via_id = feature['id_2']
            drenagem_id = feature['id']

            # Obtenha geometrias usando uma expressão de filtro
            via_geom = next(via_layer.getFeatures(QgsFeatureRequest().setFilterExpression(f'"id"=\'{via_id}\'')), None).geometry()
            drenagem_geom = next(drenagem_layer.getFeatures(QgsFeatureRequest().setFilterExpression(f'"id"=\'{drenagem_id}\'')), None).geometry()

            # Verifica se o ponto de interseção é um vértice em qualquer uma das geometrias
            if via_geom.isVertex(intersection_point) >= 0 or drenagem_geom.isVertex(intersection_point) >= 0:
                continue  # Esta interseção é considerada válida
            else:
                # Se a interseção não ocorrer em um vértice de nenhuma geometria, registre como erro
                error_feature = QgsFeature(error_fields)
                error_feature.setGeometry(QgsGeometry.fromPointXY(intersection_point))
                error_feature['Error_Desc'] = 'Interseção não ocorre em vértices da via ou da drenagem.'
                error_sink.addFeature(error_feature, QgsFeatureSink.FastInsert)

        # Verificação das regras para pontos - Regra 1
        for feature in pontos_layer.getFeatures():
            errors = []
            material_construcao = feature['material_construcao']
            tipo = feature['tipo']

            nr_pistas = feature['nr_pistas']
            nr_faixas = feature['nr_faixas']
            if tipo == 203: # Verifica se é ponte
                if type(nr_pistas) != str or type(nr_faixas) != str:
                    errors.append("Numero de pistas deve ser no mínimo igual a 1.")
                elif int(nr_pistas) < 1 or int(nr_faixas) < 1 or int(nr_pistas) > int(nr_faixas):
                    errors.append("Numero de pistas deve ser menor ou igual ao de faixas e ambos maiores que 0.")
            
            situacao_fisica = feature['situacao_fisica']
            if situacao_fisica != 3:
                errors.append("Situacao fisica deve ser Construída.")

            if tipo == 401 and material_construcao != 97:
                errors.append("Travessia vau natural deve ter atributo material_construcao como Não Aplicável.")
            
            if errors:
                error_point = feature.geometry().asPoint()
                all_errors.append((error_point, '; '.join(errors)))

        # Verificação das regras para vias
        for feature in via_layer.getFeatures():
            errors = []
            situacao_fisica = feature['situacao_fisica']
            if situacao_fisica != 3:
                errors.append("Situacao fisica deve ser Construída.")

            nr_pistas = feature['nr_pistas']
            nr_faixas = feature['nr_faixas']
        
            if type(nr_pistas) != str or type(nr_faixas) != str:
                errors.append("Numero de pistas deve ser no mínimo igual a 1.")
            elif int(nr_pistas) < 1 or int(nr_faixas) < 1 or int(nr_pistas) > int(nr_faixas):
                errors.append("Numero de pistas deve ser menor ou igual ao de faixas e ambos maiores que 0.")

            if errors:
                error_point = feature.geometry().centroid().asPoint()
                all_errors.append((error_point, '; '.join(errors)))

        for error_point, error_desc in all_errors:
            error_geom = QgsGeometry.fromPointXY(QgsPointXY(error_point))
            new_feature = QgsFeature(error_fields)
            new_feature.setGeometry(error_geom)
            new_feature['Error_Desc'] = error_desc
            error_sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        return {self.OUTPUT_ERRORS: error_id}

def register_algorithms():
    QgsApplication.processingRegistry().addAlgorithm(Projeto4Solucao())