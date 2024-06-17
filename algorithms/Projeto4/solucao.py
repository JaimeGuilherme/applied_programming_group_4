from collections import defaultdict
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsProcessing, QgsFeatureSink, QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink, QgsFeature, QgsGeometry, QgsWkbTypes, 
    QgsApplication, QgsFields, QgsField, QgsProcessingException, QgsFeatureRequest
)
from qgis import processing

class Projeto4Solucao(QgsProcessingAlgorithm):
    INPUT_PONTOS = 'INPUT_PONTOS'
    INPUT_DRENAGEM = 'INPUT_DRENAGEM'
    INPUT_VIA = 'INPUT_VIA'
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
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_PONTOS, self.tr('Camada de Pontos'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_DRENAGEM, self.tr('Camada de Trecho de Drenagem'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_VIA, self.tr('Camada de Via de Deslocamento'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_ERRORS, self.tr('Camada de Erros'), QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        pontos_layer = self.parameterAsVectorLayer(parameters, self.INPUT_PONTOS, context)
        drenagem_layer = self.parameterAsVectorLayer(parameters, self.INPUT_DRENAGEM, context)
        via_layer = self.parameterAsVectorLayer(parameters, self.INPUT_VIA, context)
        
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

# Regra 1: Validação dos atributos para pontos
        for feature in pontos_layer.getFeatures():
            errors = []
            material_construcao = feature['material_construcao']
            tipo = feature['tipo']
            nr_pistas = feature['nr_pistas']
            nr_faixas = feature['nr_faixas']

            if tipo == 203:
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
                add_error(feature.geometry(), '; '.join(errors))
        
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
                add_error(feature.geometry().centroid(), '; '.join(errors))

        # Regra 2: Interseção única entre via de deslocamento e trecho de drenagem
        intersection_result = processing.run("native:lineintersections", {
            'INPUT': via_layer,
            'INTERSECT': drenagem_layer,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)

        intersection_counts = defaultdict(int)
        for feature in intersection_result['OUTPUT'].getFeatures():
            via_id = feature['id']
            drenagem_id = feature['id_2']
            intersection_counts[(via_id, drenagem_id)] += 1

        for (via_id, drenagem_id), count in intersection_counts.items():
            if count != 1:
                via_geom = next(via_layer.getFeatures(QgsFeatureRequest().setFilterExpression(f"id = '{via_id}'"))).geometry()
                drenagem_geom = next(drenagem_layer.getFeatures(QgsFeatureRequest().setFilterExpression(f"id = '{drenagem_id}'"))).geometry()
                add_error(via_geom.intersection(drenagem_geom), "Interseção inválida: deve haver exatamente um ponto de interseção por par de feições de via e drenagem")
            else:
                via_geom = next(via_layer.getFeatures(QgsFeatureRequest().setFilterExpression(f"id = '{via_id}'"))).geometry()
                drenagem_geom = next(drenagem_layer.getFeatures(QgsFeatureRequest().setFilterExpression(f"id = '{drenagem_id}'"))).geometry()
                intersection_point = via_geom.intersection(drenagem_geom)
                
                via_vertices = []
                drenagem_vertices = []
                
                if via_geom.isMultipart():
                    for geom_part in via_geom.asMultiPolyline():
                        via_vertices.extend(geom_part)
                else:
                    via_vertices = via_geom.asPolyline()
                
                if drenagem_geom.isMultipart():
                    for geom_part in drenagem_geom.asMultiPolyline():
                        drenagem_vertices.extend(geom_part)
                else:
                    drenagem_vertices = drenagem_geom.asPolyline()
                
                intersection_point_geom = QgsGeometry.fromPointXY(intersection_point.asPoint())
                
                if not any(intersection_point_geom.equals(QgsGeometry.fromPointXY(v)) for v in via_vertices) or \
                   not any(intersection_point_geom.equals(QgsGeometry.fromPointXY(v)) for v in drenagem_vertices):
                    add_error(intersection_point_geom, "Interseção inválida: o ponto de interseção não é um vértice compartilhado")

        # Regra 3: Interseções devem ter uma ponte, galeria/bueiro ou vau
        pontos_tipos = processing.run("native:extractbyexpression", {
            'INPUT': pontos_layer,
            'EXPRESSION': '"tipo" IN (401, 501, 203)',
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)['OUTPUT']

        for intersec_feature in intersection_result['OUTPUT'].getFeatures():
            intersec_geom = intersec_feature.geometry()
            valid = False
            for feature in pontos_tipos.getFeatures():
                if intersec_geom.intersects(feature.geometry()):
                    valid = True
                    break
            if not valid:
                add_error(intersec_geom, "Interseção inválida: Falta de ponte/galeria/bueiro em interseção de via e drenagem")

        

        # Regra 4: Pontes, galerias/bueiros ou vaus rodoviários devem estar em interseções válidas
        pontos_modal_rodoviario = processing.run("native:extractbyexpression", {
            'INPUT': pontos_layer,
            'EXPRESSION': '"modal_uso" = 4',
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)['OUTPUT']

        for ponto in pontos_modal_rodoviario.getFeatures():
            valid = False
            for feature in intersection_result['OUTPUT'].getFeatures():
                if ponto.geometry().intersects(feature.geometry()):
                    valid = True
                    break
            if not valid:
                add_error(ponto.geometry(), "Erro em ponte/galeria/bueiro/vau rodoviário não está numa interseção válida")

        # Regra 5: Atributos das pontes devem coincidir com os da via de deslocamento
        for ponto in pontos_layer.getFeatures():
            if ponto["tipo"] == "401":
                for feature in intersection_result['OUTPUT'].getFeatures():
                    if ponto.geometry().intersects(feature.geometry()):
                        via_geom = next(via_layer.getFeatures(QgsFeatureRequest().setFilterExpression(f"id = '{feature['input:ID']}'"))).geometry()
                        via_attrs = via_geom.attributes()
                        if (ponto["nr_faixas"] != via_attrs["nr_faixas"] or ponto["nr_pistas"] != via_attrs["nr_pistas"] or ponto["situacao_fisica"] != via_attrs["situacao_fisica"]):
                            add_error(ponto.geometry(), "Erro nos atributos da ponte")



        return {self.OUTPUT_ERRORS: dest_id}


def register_algorithms():
    QgsApplication.processingRegistry().addAlgorithm(Projeto4Solucao())
