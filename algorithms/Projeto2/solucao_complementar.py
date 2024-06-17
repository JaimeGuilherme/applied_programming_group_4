from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, QgsFeatureSink,
                    QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                    QgsProcessingParameterFeatureSink,
                    QgsProcessingParameterRasterLayer, QgsFields, QgsWkbTypes, QgsVectorLayer, QgsFeature, QgsProject)
from qgis import processing
class Projeto2Solucao(QgsProcessingAlgorithm):
    # Definição dos identificadores dos parâmetros e saídas
    INPUT_CURVA = 'INPUT_CURVA'
    INPUT_PISTA_PONTO  = 'INPUT_PISTA_PONTO'
    INPUT_PISTA_LINHA = 'INPUT_PISTA_LINHA'
    INPUT_PISTA_AREA = 'INPUT_PISTA_AREA'
    INPUT_COMBOBOX= 'INPUT_COMBOBOX'
    INPUT_MOLDURA = 'INPUT_MOLDURA'
    INPUT_MDT = 'INPUT_MDT'
    INPUT_ESCALA ='INPUT_ESCALA'
    INPUT_MASCARA = 'INPUT_MASCARA'

    OUTPUT_CURVA = 'OUTPUT_DRENAGEM'
    OUTPUT_PISTA_PONTO = 'OUTPUT_PISTA_PONTO'
    OUTPUT_PISTA_LINHA = 'OUTPUT_PISTA_LINHA'
    OUTPUT_PISTA_AREA = 'OUTPUT_PISTA_AREA'
    OUTPUT_PONTO_COTA = 'OUTPUT_PONTO_COTA'

    def tr(self, string):
        return QCoreApplication.translate('Projeto2Solucao', string)

    def createInstance(self):
        return Projeto2Solucao()

    def name(self):
        return 'projeto2solucao'

    def displayName(self):
        return self.tr('Solução Projeto 2 - Grupo 4')

    def group(self):
        return self.tr('Exemplos')

    def groupId(self):
        return 'exemplos'

    def shortHelpString(self):
        return self.tr("Este algoritmo é parte da solução do Grupo 4 para identificação da curva mestra.")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_CURVA, self.tr('Curva de Nível'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_MASCARA, self.tr("Camada de Moldura "), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_MOLDURA, self.tr("Camada MDT")))

       # Outputs
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_PONTO_COTA, self.tr('Saída Cota'),QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        # Obter as camadas e parâmetros de entrada
        curvaNivel = self.parameterAsVectorLayer(parameters, self.INPUT_CURVA, context)
        raster = self.parameterAsRasterLayer(parameters, self.INPUT_MOLDURA, context)
        moldura = self.parameterAsVectorLayer(parameters, self.INPUT_MASCARA, context)

        # Processamento: Criar campo altitude 

        
        # Filtrar curvas de nível dentro da área recortada do MDT
        feedback.pushInfo('Filtrando curvas de nível dentro da área recortada...')
        filteredCurvas = processing.run("native:extractbylocation", {
            'INPUT': curvaNivel,
            'PREDICATE': [0],  # Intersect
            'INTERSECT': moldura,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)['OUTPUT']       

         # Recortar o MDT com a camada de moldura
        feedback.pushInfo('Recortando o MDT com a camada de moldura...')
        clippedRaster = processing.run("gdal:cliprasterbymasklayer", {
            'INPUT': raster,
            'MASK': moldura,  # Supõe-se que a camada de moldura é a mesma que a camada de curvas de nível
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback)['OUTPUT']

        # Identificar curvas de nível que não têm outras dentro
        feedback.pushInfo('Identificando curvas isoladas...')
        isolatedCurves = []
        for feature in filteredCurvas.getFeatures():
            isIsolated = True
            for otherFeature in filteredCurvas.getFeatures():
                if feature.id() != otherFeature.id() and feature.geometry().contains(otherFeature.geometry()):
                    isIsolated = False
                    break
            if isIsolated:
                isolatedCurves.append(feature)

                # Adicionando feedback sobre o número de curvas isoladas encontradas
        feedback.pushInfo(f'Número de curvas isoladas encontradas: {len(isolatedCurves)}')

        # Processar cada curva isolada para encontrar o ponto mais elevado
        feedback.pushInfo('Processando cada curva isolada para encontrar o ponto mais elevado...')
        maxPoints = []
        for curve in isolatedCurves:
            # Criar uma camada temporária para a máscara
            maskLayer = QgsVectorLayer("Polygon?crs=epsg:4326", "temporary_mask", "memory")
            prov = maskLayer.dataProvider()
            feat = QgsFeature()
            feat.setGeometry(curve.geometry())
            prov.addFeature(feat)
            QgsProject.instance().addMapLayer(maskLayer)  # Adicionar ao projeto se necessário para debug

            # Usar a camada temporária como máscara
            curveRaster = processing.run("gdal:cliprasterbymasklayer", {
                'INPUT': raster,
                'MASK': maskLayer,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }, context=context, feedback=feedback)['OUTPUT']

            # Converter pixels do raster em pontos
            pointsLayer = processing.run("qgis:rasterpixelstopoints", {
                'INPUT': curveRaster,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }, context=context, feedback=feedback)['OUTPUT']

            # Encontrar o ponto de maior elevação
            maxElevation = float('-inf')
            maxPoint = None
            for point in pointsLayer.getFeatures():
                if point['rvalue'] > maxElevation:
                    maxElevation = point['rvalue']
                    maxPoint = point.geometry()

            if maxPoint:
                maxPoints.append((maxPoint, maxElevation))

            QgsProject.instance().removeMapLayer(maskLayer)  # Remover a camada temporária após uso

        # Criar a camada de saída com os pontos de maior elevação
        (sinkpontoCota, sinkpontoCotaId) = self.parameterAsSink(parameters, self.OUTPUT_PONTO_COTA, context, QgsFields(), QgsWkbTypes.Point, raster.crs())
        for point, elevation in maxPoints:
            feat = QgsFeature()
            feat.setGeometry(point)
            feat.setAttributes([elevation])
            sinkpontoCota.addFeature(feat, QgsFeatureSink.FastInsert)


        # Garantir que todos os resultados dos processamentos sejam incluídos no dicionário de retorno
        return {
            self.OUTPUT_PONTO_COTA: sinkpontoCotaId,
        }

