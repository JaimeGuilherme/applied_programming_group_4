from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingException,
                    QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                    QgsProcessingParameterFeatureSink, QgsProcessingParameterDistance,
                    QgsProcessingParameterRasterLayer,
                    QgsCoordinateReferenceSystem)
from qgis import processing

class Projeto1Solucao(QgsProcessingAlgorithm):
    # Definição dos identificadores dos parâmetros e saídas
    INPUT_VIA = 'INPUT_VIA'
    INPUT_RVIA = 'INPUT_RVIA'
    INPUT_VGT = 'INPUT_VGT'
    INPUT_MDA = 'INPUT_MDA'
    INPUT_TD = 'INPUT_TD'
    INPUT_RTD = 'INPUT_RTD'
    INPUT_RMC = 'INPUT_RMC'
    INPUT_AED = 'INPUT_AED'
    INPUT_ASD = 'INPUT_ASD'
    INPUT_MDT = 'INPUT_MDT'
    INPUT_TP = 'INPUT_TP'
    OUTPUT_VIA = 'OUTPUT_VIA'
    OUTPUT_DRENAGEM = 'OUTPUT_DRENAGEM'
    OUTPUT_MATA_CILIAR = 'OUTPUT_MATA_CILIAR'
    OUTPUT_VIA_FEDERAL_ESTADUAL = 'OUTPUT_VIA_FEDERAL_ESTADUAL'
    OUTPUT_VIA_COMPLEMENTAR = 'OUTPUT__VIA_COMPLEMENTAR'
    OUTPUT_CAMPO ='OUTPUT_CAMPO'
    OUTPUT_FLORESTA ='OUTPUT_FLORESTA'
    OUTPUT_VEGETACAO_COMPLEMENTAR ='OUTPUT_VEGETACAO_COMPLEMENTAR'


    def tr(self, string):
        return QCoreApplication.translate('Projeto1Solucao', string)

    def createInstance(self):
        return Projeto1Solucao()

    def name(self):
        return 'projeto1solucao'

    def displayName(self):
        return self.tr('Solução Projeto 1 - Grupo 4')

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return 'Projeto 1'

    def shortHelpString(self):
        return self.tr("Este algoritmo é parte da solução do Grupo 4 para análise de trafegabilidade.")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_VIA, self.tr('Via de deslocamento'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterDistance(self.INPUT_RVIA, self.tr('Buffer para via de deslocamento'), parentParameterName=self.INPUT_VIA, defaultValue=100))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_VGT, self.tr('Camada Vegetação'), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_MDA, self.tr("Camada Massa d'agua "), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_TD, self.tr('Camada Trecho de Drenagem'), [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterDistance(self.INPUT_RTD, self.tr('Buffer Trecho de deslocamento'), parentParameterName=self.INPUT_TD, defaultValue=50))
        self.addParameter(QgsProcessingParameterDistance(self.INPUT_RMC, self.tr('Buffer da Mata ciliar'), parentParameterName=self.INPUT_VGT, defaultValue=30))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_AED, self.tr("Camada Área edificada"), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_ASD, self.tr("Camada Área sem dados"), [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_MDT, self.tr("Camada MDT")))
        self.addParameter(QgsProcessingParameterDistance(self.INPUT_TP, self.tr('Tamanho do pixel'), parentParameterName=self.INPUT_MDT, defaultValue=10))
       # Outputs
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_VIA, self.tr('Saída Via de deslocamento'),QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_DRENAGEM, self.tr('Saída Trecho de Drenagem'),QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_MATA_CILIAR, self.tr('Saída Mata Ciliar'),QgsProcessing.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_VIA_FEDERAL_ESTADUAL, self.tr('Saída Via Federal Estadual'),QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_VIA_COMPLEMENTAR, self.tr('Saída Via Complementar'),QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_CAMPO, self.tr('Saída Campo'),QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_FLORESTA, self.tr('Saída Floresta'),QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_VEGETACAO_COMPLEMENTAR, self.tr('Saída Vegetação Complementar '),QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):
        # Obter as camadas e parâmetros de entrada
        viasLayer = self.parameterAsVectorLayer(parameters, self.INPUT_VIA, context)
        raioVia = self.parameterAsDouble(parameters, self.INPUT_RVIA, context)
        vegetacaoLayer = self.parameterAsVectorLayer(parameters, self.INPUT_VGT, context)
        raioMataCiliar = self.parameterAsDouble(parameters, self.INPUT_RMC, context)
        trechoDrenagemLayer = self.parameterAsVectorLayer(parameters, self.INPUT_TD, context)
        raioTrechoDrenagem = self.parameterAsDouble(parameters, self.INPUT_RTD, context)
        # As demais camadas seguem a mesma lógica para obtenção
        
        # Processamento: Criar buffer para a via de deslocamento
        bufferViasResult = processing.run("native:buffer", {
            'INPUT': viasLayer,
            'DISTANCE': raioVia,
            'SEGMENTS': 5,
            'DISSOLVE': False,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        bufferViasLayer = bufferViasResult['OUTPUT']

        # Processamento: Criar buffer para a vegetação (mata ciliar)
        bufferVegetacaoResult = processing.run("native:buffer", {
            'INPUT': vegetacaoLayer,
            'DISTANCE': raioMataCiliar,
            'SEGMENTS': 5,
            'DISSOLVE': False,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        bufferVegetacaoLayer = bufferVegetacaoResult['OUTPUT']

        # Processamento: Criar buffer para o trecho de drenagem
        bufferDrenagemResult = processing.run("native:buffer", {
            'INPUT': trechoDrenagemLayer,
            'DISTANCE': raioTrechoDrenagem,
            'SEGMENTS': 5,
            'DISSOLVE': False,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        bufferDrenagemLayer = bufferDrenagemResult['OUTPUT']

        # Salvando o resultado dos buffers nas saídas correspondentes
        (sinkVias, sinkViasId) = self.parameterAsSink(parameters, self.OUTPUT_VIA, context, bufferViasLayer.fields(), bufferViasLayer.wkbType(), bufferViasLayer.sourceCrs())
        for feature in bufferViasLayer.getFeatures():
            sinkVias.addFeature(feature, QgsFeatureSink.FastInsert)

        (sinkVegetacao, sinkVegetacaoId) = self.parameterAsSink(parameters, self.OUTPUT_MATA_CILIAR, context, bufferVegetacaoLayer.fields(), bufferVegetacaoLayer.wkbType(), bufferVegetacaoLayer.sourceCrs())
        for feature in bufferVegetacaoLayer.getFeatures():
            sinkVegetacao.addFeature(feature, QgsFeatureSink.FastInsert)

        (sinkDrenagem, sinkDrenagemId) = self.parameterAsSink(parameters, self.OUTPUT_DRENAGEM, context, bufferDrenagemLayer.fields(), bufferDrenagemLayer.wkbType(), bufferDrenagemLayer.sourceCrs())
        for feature in bufferDrenagemLayer.getFeatures():
            sinkDrenagem.addFeature(feature, QgsFeatureSink.FastInsert)

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

        # Via sem ser federal ou estadual 
        expressao = '"tipo"  != 2 or ( "jurisdicao" != 1 and  "jurisdicao" !=2 )'
        viasComplementaresResult = processing.run("native:extractbyexpression", {
            'INPUT': bufferViasLayer,
            'EXPRESSION': expressao,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)
        viasComplementaresLayer = viasComplementaresResult['OUTPUT']

        (sinkViasComplementar, sinkViasComplementarId) = self.parameterAsSink(parameters, self.OUTPUT_VIA_COMPLEMENTAR, context, viasComplementaresLayer.fields(), viasComplementaresLayer.wkbType(), viasComplementaresLayer.sourceCrs())
        for feature in viasComplementaresLayer.getFeatures():
            sinkViasComplementar.addFeature(feature, QgsFeatureSink.FastInsert)

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

        # # Criar raster 
        #     processing.run("native:createconstantrasterlayer", {'EXTENT':'547886.788400000,560216.559200000,6625525.024400000,6653514.503900000 [EPSG:31981]',
        #                                                         'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:31981'),
        #                                                         'PIXEL_SIZE':1, # Tamanho do pixel 
        #                                                         'NUMBER':1,
        #                                                         'OUTPUT_TYPE':5,
        #                                                         'OUTPUT':'TEMPORARY_OUTPUT'})

        
        # Garanta que todos os resultados dos processamentos sejam incluídos no dicionário de retorno
        return {
            self.OUTPUT_VIA: sinkViasId,
            self.OUTPUT_DRENAGEM: sinkDrenagemId,  # Garanta que sinkDrenagemId seja definido corretamente
            self.OUTPUT_MATA_CILIAR: sinkVegetacaoId,  # Garanta que sinkVegetacaoId seja definido corretamente
            self.OUTPUT_VIA_FEDERAL_ESTADUAL: sinkViasFederaisEstaduaisId,
            self.OUTPUT_VIA_COMPLEMENTAR: sinkViasComplementarId,
            self.OUTPUT_CAMPO: sinkTerrenoExpostoId,
            self.OUTPUT_FLORESTA: sinkFlorestaId,
            self.OUTPUT_VEGETACAO_COMPLEMENTAR: sinkVegetacaoComplementarId,
        }