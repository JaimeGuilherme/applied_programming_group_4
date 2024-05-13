from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingException,
                    QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
                    QgsProcessingParameterFeatureSink, QgsProcessingParameterDistance,
                    QgsProcessingParameterRasterLayer,
                    QgsCoordinateReferenceSystem,
                    QgsProcessingParameterEnum,
                    QgsFeature, QgsPointXY)
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
        self.addParameter(QgsProcessingParameterEnum(self.INPUT_ESCALA, self.tr("Selecione uma escala"), options=['1:25000', '1:50000', '1:100000','1:250000'])) # Adicionando a caixa de seleção
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

    def processAlgorithm(self, parameters, context, feedback):
        # Obter as camadas e parâmetros de entrada
        curvaNivel = self.parameterAsVectorLayer(parameters, self.INPUT_CURVA, context)
        pistaPonto = self.parameterAsVectorLayer(parameters, self.INPUT_PISTA_PONTO , context)
        pistaLinha = self.parameterAsVectorLayer(parameters, self.INPUT_PISTA_LINHA, context)
        pistaArea = self.parameterAsVectorLayer(parameters, self.INPUT_PISTA_AREA, context)
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



        # (sinkViasFederaisEstaduais, sinkViasFederaisEstaduaisId) = self.parameterAsSink(parameters, self.OUTPUT_VIA_FEDERAL_ESTADUAL, context, viasFederaisEstaduaisLayer.fields(), viasFederaisEstaduaisLayer.wkbType(), viasFederaisEstaduaisLayer.sourceCrs())
        # for feature in viasFederaisEstaduaisLayer.getFeatures():
        #     sinkViasFederaisEstaduais.addFeature(feature, QgsFeatureSink.FastInsert)
        
        # # Obter terreno exposto 
        # expressao = '"tipo" = 1000'
        # terrenoExpostoResult = processing.run("native:extractbyexpression", {
        #     'INPUT': vegetacaoLayer,
        #     'EXPRESSION': expressao,
        #     'OUTPUT': 'memory:'
        # }, context=context, feedback=feedback)
        # terrenoExpostoLayer = terrenoExpostoResult['OUTPUT']

        # (sinkTerrenoExposto, sinkTerrenoExpostoId) = self.parameterAsSink(parameters, self.OUTPUT_CAMPO, context, terrenoExpostoLayer.fields(), terrenoExpostoLayer.wkbType(), terrenoExpostoLayer.sourceCrs())
        # for feature in terrenoExpostoLayer.getFeatures():
        #     sinkTerrenoExposto.addFeature(feature, QgsFeatureSink.FastInsert)


        
        # Garanta que todos os resultados dos processamentos sejam incluídos no dicionário de retorno
        return {
            
            self.OUTPUT_CURVA: sinkCurvaNivelId,  # Garanta que sinkDrenagemId seja definido corretamente
            
        }