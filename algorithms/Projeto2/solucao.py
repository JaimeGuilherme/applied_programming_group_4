from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingException,
                    QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                    QgsProcessingParameterFeatureSink, QgsProcessingParameterDistance,
                    QgsProcessingParameterRasterLayer,
                    QgsCoordinateReferenceSystem)
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

    OUTPUT_CURVA = 'OUTPUT_DRENAGEM'
    OUTPUT_PISTA_PONTO = 'OUTPUT_PISTA_PONTO'
    OUTPUT_PISTA_LINHA = 'OUTPUT_PISTA_LINHA'
    OUTPUT_PISTA_AREA = 'OUTPUT_PISTA_AREA'
    OUTPUT_MOLDURA_COMPLEMENTAR ='OUTPUT_MOLDURA_COMPLEMENTAR'


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
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_PISTA_PONTO , self.tr('Camada Ponto da Pista'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_PISTA_AREA, self.tr("Camada Área da Pista "), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_PISTA_LINHA, self.tr("Camada Linha da Pista "), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_MOLDURA, self.tr("Camada MDT")))
       
       # Outputs
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_CURVA, self.tr('Saída Curva'),QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_PISTA_PONTO, self.tr('Saída ponto'),QgsProcessing.TypeVectorPoint))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_PISTA_AREA, self.tr('Saída Area'),QgsProcessing.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_PISTA_LINHA, self.tr('Saída Linha'),QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_MOLDURA_COMPLEMENTAR, self.tr('Saída Complementar'),QgsProcessing.TypeVectorRaster))

    def processAlgorithm(self, parameters, context, feedback):
        # Obter as camadas e parâmetros de entrada
        curvaNivel = self.parameterAsVectorLayer(parameters, self.INPUT_CURVA, context)
        pistaPonto = self.parameterAsVectorLayer(parameters, self.INPUT_PISTA_PONTO , context)
        pistaLinha = self.parameterAsVectorLayer(parameters, self.INPUT_PISTA_LINHA, context)
        pistaArea = self.parameterAsVectorLayer(parameters, self.INPUT_PISTA_AREA, context)
        
        # As demais camadas seguem a mesma lógica para obtenção
        
        # Processamento: Criar campo altitude 

        processing.run("native:fieldcalculator", {'INPUT':curvaNivel,
                                                  'FIELD_NAME':'altitude',
                                                  'FIELD_TYPE':0,
                                                  'FIELD_LENGTH':0,
                                                  'FIELD_PRECISION':0,
                                                  'FORMULA':CASE WHEN "cota" % 50 = 0 THEN concat('mestra (', 1, ')') ELSE concat('normal (', 2, ')') END,

                                                  'OUTPUT':'TEMPORARY_OUTPUT'})
        

        # Processamento: Criar buffer para a vegetação (mata ciliar)
        bufferVegetacaoResult = processing.run("native:buffer", {
            'INPUT': vegetacaoLayer,
            'DISTANCE': raioMataCiliar,
            'SEGMENTS': 5,
            'DISSOLVE': False,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        bufferVegetacaoLayer = bufferVegetacaoResult['OUTPUT']

        # Salvando o resultado dos buffers nas saídas correspondentes
       

        (sinkVegetacao, sinkVegetacaoId) = self.parameterAsSink(parameters, self.OUTPUT_MATA_CILIAR, context, bufferVegetacaoLayer.fields(), bufferVegetacaoLayer.wkbType(), bufferVegetacaoLayer.sourceCrs())
        for feature in bufferVegetacaoLayer.getFeatures():
            sinkVegetacao.addFeature(feature, QgsFeatureSink.FastInsert)

        # Exemplo para processar e extrair vias federais e estaduais
        # Este passo requer que você defina a expressão correta para sua lógica de seleção
        expressao = '"tipo"  = 2 and ( "jurisdicao" = 1 or  "jurisdicao" =2 )'
        viasFederaisEstaduaisResult = processing.run("native:extractbyexpression", {
            'INPUT': bufferViasLayer,
            'EXPRESSION': expressao,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        viasFederaisEstaduaisLayer = viasFederaisEstaduaisResult['OUTPUT']

        (sinkViasFederaisEstaduais, sinkViasFederaisEstaduaisId) = self.parameterAsSink(parameters, self.OUTPUT_VIA_FEDERAL_ESTADUAL, context, viasFederaisEstaduaisLayer.fields(), viasFederaisEstaduaisLayer.wkbType(), viasFederaisEstaduaisLayer.sourceCrs())
        for feature in viasFederaisEstaduaisLayer.getFeatures():
            sinkViasFederaisEstaduais.addFeature(feature, QgsFeatureSink.FastInsert)
        
        # Obter terreno exposto 
        expressao = '"tipo" = 1000'
        terrenoExpostoResult = processing.run("native:extractbyexpression", {
            'INPUT': vegetacaoLayer,
            'EXPRESSION': expressao,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        terrenoExpostoLayer = terrenoExpostoResult['OUTPUT']

        (sinkTerrenoExposto, sinkTerrenoExpostoId) = self.parameterAsSink(parameters, self.OUTPUT_CAMPO, context, terrenoExpostoLayer.fields(), terrenoExpostoLayer.wkbType(), terrenoExpostoLayer.sourceCrs())
        for feature in terrenoExpostoLayer.getFeatures():
            sinkTerrenoExposto.addFeature(feature, QgsFeatureSink.FastInsert)
        
        # Obter Floresta
        expressao = '"tipo" = 601 or "tipo" = 602'
        FlorestaResult = processing.run("native:extractbyexpression", {
            'INPUT': vegetacaoLayer,
            'EXPRESSION': expressao,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        FlorestaLayer = FlorestaResult['OUTPUT']

        (sinkFloresta, sinkFlorestaId) = self.parameterAsSink(parameters, self.OUTPUT_FLORESTA, context, FlorestaLayer.fields(),FlorestaLayer.wkbType(), FlorestaLayer.sourceCrs())
        for feature in FlorestaLayer.getFeatures():
            sinkFloresta.addFeature(feature, QgsFeatureSink.FastInsert)

        # Obter Vegetação complementar
        expressao = '"tipo" != 601 and "tipo" != 602 and "tipo" != 1000 '
        vegetacaoComplementarResult = processing.run("native:extractbyexpression", {
            'INPUT': vegetacaoLayer,
            'EXPRESSION': expressao,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        vegetacaoComplementarLayer = vegetacaoComplementarResult['OUTPUT']

        (sinkVegetacaoComplementar, sinkVegetacaoComplementarId) = self.parameterAsSink(parameters, self.OUTPUT_VEGETACAO_COMPLEMENTAR, context, FlorestaLayer.fields(),FlorestaLayer.wkbType(), FlorestaLayer.sourceCrs())
        for feature in vegetacaoComplementarLayer.getFeatures():
            sinkVegetacaoComplementar.addFeature(feature, QgsFeatureSink.FastInsert)

        # Criar raster 
            processing.run("native:createconstantrasterlayer", {'EXTENT':'547886.788400000,560216.559200000,6625525.024400000,6653514.503900000 [EPSG:31981]',
                                                                'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:31981'),
                                                                'PIXEL_SIZE':1, # Tamanho do pixel 
                                                                'NUMBER':1,
                                                                'OUTPUT_TYPE':5,
                                                                'OUTPUT':'memory:'})

        
        # Garanta que todos os resultados dos processamentos sejam incluídos no dicionário de retorno
        return {
            self.OUTPUT_VIA: sinkViasId,
            self.OUTPUT_CURVA: sinkDrenagemId,  # Garanta que sinkDrenagemId seja definido corretamente
            self.OUTPUT_MATA_CILIAR: sinkVegetacaoId,  # Garanta que sinkVegetacaoId seja definido corretamente
            self.OUTPUT_VIA_FEDERAL_ESTADUAL: sinkViasFederaisEstaduaisId,
            self.OUTPUT_VIA_COMPLEMENTAR: sinkViasComplementarId,
            self.OUTPUT_CAMPO: sinkTerrenoExpostoId,
            self.OUTPUT_FLORESTA: sinkFlorestaId,
            self.OUTPUT_VEGETACAO_COMPLEMENTAR: sinkVegetacaoComplementarId,
        }