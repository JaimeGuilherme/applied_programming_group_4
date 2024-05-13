from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingException,
                    QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                    QgsProcessingParameterFeatureSink, QgsProcessingParameterDistance,
                    QgsProcessingParameterRasterLayer,
                    QgsCoordinateReferenceSystem,
                    QgsProcessingParameterEnum,
                    QgsFeature, QgsPointXY, QgsGeometry)
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
        self.addParameter(QgsProcessingParameterEnum(self.INPUT_ESCALA, self.tr("Selecione uma escala"), options=['1:25000', '1:50000', '1:100000','1:250000'])) # Adicionando a caixa de seleção
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_CURVA, self.tr('Curva de Nível'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_PISTA_PONTO , self.tr('Camada Ponto da Pista'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_PISTA_AREA, self.tr("Camada Área da Pista "), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_PISTA_LINHA, self.tr("Camada Linha da Pista "), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_MASCARA, self.tr("Camada de Moldura "), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_MOLDURA, self.tr("Camada MDT")))

       # Outputs
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_CURVA, self.tr('Saída Curva'),QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_PISTA_PONTO, self.tr('Saída ponto'),QgsProcessing.TypeVectorPoint))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_PISTA_AREA, self.tr('Saída Area'),QgsProcessing.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_PISTA_LINHA, self.tr('Saída Linha'),QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_PONTO_COTA, self.tr('Saída Cota'),QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        # Obter as camadas e parâmetros de entrada
        curvaNivel = self.parameterAsVectorLayer(parameters, self.INPUT_CURVA, context)
        pistaPonto = self.parameterAsVectorLayer(parameters, self.INPUT_PISTA_PONTO , context)
        pistaLinha = self.parameterAsVectorLayer(parameters, self.INPUT_PISTA_LINHA, context)
        pistaArea = self.parameterAsVectorLayer(parameters, self.INPUT_PISTA_AREA, context)
        raster = self.parameterAsRasterLayer(parameters, self.INPUT_MOLDURA, context)
        moldura = self.parameterAsVectorLayer(parameters, self.INPUT_MASCARA, context)        
        escala = self.parameterAsString(parameters, self.INPUT_ESCALA, context)

        #dicionario escala 
        equidistancia_dict = {'0':10,
                              '1':20,
                              '2':50,
                              '3':100,
                              }
        eqd = equidistancia_dict[escala]
        
        # As demais camadas seguem a mesma lógica para obtenção
        
        # Processamento: Criar campo altitude 

        
        # Filtrar curvas de nível dentro da área recortada do MDT
        feedback.pushInfo('Filtrando curvas de nível dentro da área recortada...')
        filteredCurvas = processing.run("native:extractbylocation", {
            'INPUT': curvaNivel,
            'PREDICATE': [0],  # Intersect
            'INTERSECT': moldura,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)['OUTPUT']
        
        
        curvaNivel = processing.run("native:fieldcalculator", {'INPUT':curvaNivel,
                                                  'FIELD_NAME':'curva mestra',
                                                  'FIELD_TYPE':0,
                                                  'FIELD_LENGTH':0,
                                                  'FIELD_PRECISION':0,
                                                  'FORMULA':f"CASE WHEN cota % {5*eqd} = 0 THEN '1' WHEN cota % {eqd} = 0 THEN '2' ELSE '3' END",
                                                  'OUTPUT':'memory:'})
        curvaNivelLayer = curvaNivel['OUTPUT']

        
        # Salvando o resultado dos buffers nas saídas correspondentes
        # Exemplo para processar e extrair vias federais e estaduais
        # Este passo requer que você defina a expressão correta para sua lógica de seleção
        expressao = '"curva mestra" != 3'
        curvaNivelresult = processing.run("native:extractbyexpression", {
            'INPUT': curvaNivelLayer,
            'EXPRESSION': expressao,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        curvaNivelLayer = curvaNivelresult['OUTPUT']
        
        (sinkCurvaNivel , sinkCurvaNivelId) = self.parameterAsSink(parameters, self.OUTPUT_CURVA, context, curvaNivelLayer.fields(), curvaNivelLayer.wkbType(), curvaNivelLayer.sourceCrs())
        for feature in curvaNivelLayer.getFeatures():
            sinkCurvaNivel.addFeature(feature, QgsFeatureSink.FastInsert)

        # Objetivo 2 
        # Amostragem de raster para a camada de ponto
        pontosMDT = processing.run("native:rastersampling", {
            'INPUT': pistaPonto,
            'RASTERCOPY': raster,
            'COLUMN_PREFIX': 'Altura',
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        pontosMDTLayer = pontosMDT['OUTPUT']


        # Gerar pontos ao longo da linha
        linhaPontos = processing.run("qgis:generatepointspixelcentroidsalongline", {
            'INPUT_RASTER': raster,
            'INPUT_VECTOR': pistaLinha,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        linhaPontosLayer = linhaPontos['OUTPUT']


        # Amostragem de raster para a camada de linha
        linhasMDT = processing.run("native:rastersampling", {
            'INPUT': linhaPontosLayer,
            'RASTERCOPY': raster,
            'COLUMN_PREFIX': 'Altura',
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        linhaMDTLayer = linhasMDT['OUTPUT']

        # Gerar pontos nos centróides dos pixels dentro dos polígonos
        areaPontos = processing.run("native:generatepointspixelcentroidsinsidepolygons", {
            'INPUT_RASTER': raster,
            'INPUT_VECTOR': pistaArea,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        areaPontosLayer = areaPontos['OUTPUT']

        # Amostragem de raster para a camada de área
        areasMDT = processing.run("native:rastersampling", {
            'INPUT': areaPontosLayer,
            'RASTERCOPY': raster,
            'COLUMN_PREFIX': 'Altura',
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        areaMDTLayer = areasMDT['OUTPUT']

        # Configurando as saídas dos processamentos para as camadas de linha e área
        (sinkLinhaMDT, sinkLinhaMDTId) = self.parameterAsSink(parameters, self.OUTPUT_PISTA_LINHA, context, linhaMDTLayer.fields(), linhaMDTLayer.wkbType(), linhaMDTLayer.sourceCrs())
        for feature in linhaMDTLayer.getFeatures():
            sinkLinhaMDT.addFeature(feature, QgsFeatureSink.FastInsert)

        (sinkAreaMDT, sinkAreaMDTId) = self.parameterAsSink(parameters, self.OUTPUT_PISTA_AREA, context, areaMDTLayer.fields(), areaMDTLayer.wkbType(), areaMDTLayer.sourceCrs())
        for feature in areaMDTLayer.getFeatures():
            sinkAreaMDT.addFeature(feature, QgsFeatureSink.FastInsert)

        (sinkPontosMDT, sinkPontosMDTId) = self.parameterAsSink(parameters, self.OUTPUT_PISTA_PONTO, context, pontosMDTLayer.fields(), pontosMDTLayer.wkbType(), pontosMDTLayer.sourceCrs())
        for feature in pontosMDTLayer.getFeatures():
            sinkPontosMDT.addFeature(feature, QgsFeatureSink.FastInsert)    

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
       

        from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsProject

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
                'INPUT': clippedRaster,
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
            self.OUTPUT_CURVA: sinkCurvaNivelId,
            self.OUTPUT_PISTA_PONTO: sinkPontosMDTId,
            self.OUTPUT_PISTA_LINHA: sinkLinhaMDTId,
            self.OUTPUT_PISTA_AREA: sinkAreaMDTId
        }

