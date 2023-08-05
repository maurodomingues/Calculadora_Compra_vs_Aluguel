from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import matplotlib.pyplot as plt
import io
import base64
import json
import locale
import matplotlib

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
matplotlib.use('Agg')

app=FastAPI()

def calc(valor_aluguel, valor_imovel, taxa_valorizacao_imovel,taxa_reajuste_aluguel, taxa_juros_aplicacao,anos):
    valor_aluguel = float(valor_aluguel)
    valor_imovel = float(valor_imovel)
    taxa_valorizacao_imovel = float(taxa_valorizacao_imovel)/100
    taxa_reajuste_aluguel = float(taxa_reajuste_aluguel)/100
    taxa_juros_aplicacao = float(taxa_juros_aplicacao)/100
    anos = int(anos)

# Transformando a taxa de juros de anual para mensal
    taxa_juros_aplicacao_mensal = (1 + taxa_juros_aplicacao) ** (1/12) - 1
    taxa_juros_valorizacao_mensal = (1 + taxa_valorizacao_imovel) ** (1/12) - 1

# Inicializando os valores iniciais
    valor_aplicacao = valor_imovel
    valor_aluguel_atual = valor_aluguel

    # Inicializando listas para armazenar os resultados mês a mês
    meses = []
    valores_aplicacao = []
    valores_imovel = []
    turnover = []

    # Simulando o cenário mês a mês ao longo dos anos (entrada da função)
    for mes in range(1, 12*anos+1):
        # Atualizando o valor do imóvel com a taxa de valorização mensal
        valor_imovel *= (1 + taxa_juros_valorizacao_mensal)

        # Atualizando o valor da aplicação com os juros mensais subtraindo o valor do aluguel
        valor_aplicacao *= (1 + taxa_juros_aplicacao_mensal)
        valor_aplicacao -= valor_aluguel_atual

        # Atualizando o valor do aluguel com o reajuste anual
        if mes % 12 == 0:  # Verifica se é o mês de reajuste (a cada 12 meses)
            valor_aluguel_atual *= (1 + taxa_reajuste_aluguel)

        # Salva os resultados do mês atual nas listas
        meses.append(mes)
        valores_aplicacao.append(valor_aplicacao)
        valores_imovel.append(valor_imovel)

        if mes == 1:
          if valor_aplicacao > valor_imovel:
            montante_maior = "A"
          else:
            montante_maior = "I"

        if montante_maior == "A":
          if valor_aplicacao < valor_imovel:
            turnover.append("SIM")
            montante_maior = "I"
          else:
            turnover.append("NAO")
        elif montante_maior == "I":
          if valor_imovel < valor_aplicacao:
            turnover.append("SIM")
            montante_maior = "A"
          else:
            turnover.append("NAO")

    lista_combinada = list(zip(meses, valores_aplicacao, valores_imovel, turnover))

    dicionario = {}

    for mes, aplicacao, imovel, ponto_turnover in lista_combinada:
        dicionario[mes] = (aplicacao, imovel, ponto_turnover)


    return dicionario

@app.get('/calculo/{valor_aluguel}/{valor_imovel}/{taxa_valorizacao_imovel}/{taxa_reajuste_aluguel}/{taxa_juros_aplicacao}/{anos}')
def obter_resultado(valor_aluguel,valor_imovel,taxa_valorizacao_imovel,taxa_reajuste_aluguel,taxa_juros_aplicacao,anos):
    resultado = calc(valor_aluguel,valor_imovel,taxa_valorizacao_imovel,taxa_reajuste_aluguel,taxa_juros_aplicacao,anos)
    return resultado

@app.get('/resumo/{valor_aluguel}/{valor_imovel}/{taxa_valorizacao_imovel}/{taxa_reajuste_aluguel}/{taxa_juros_aplicacao}/{anos}')
def obter_resultado1(valor_aluguel,valor_imovel,taxa_valorizacao_imovel,taxa_reajuste_aluguel,taxa_juros_aplicacao,anos):
    resultado    = calc(valor_aluguel,valor_imovel,taxa_valorizacao_imovel,taxa_reajuste_aluguel,taxa_juros_aplicacao,anos)
    chave_ultima = max(resultado.keys())
    valor_ultima = resultado[chave_ultima]

    aplicacao_final = valor_ultima[0]
    imovel_final    = valor_ultima[1]

    aplicacao_final_f = locale.currency(aplicacao_final, grouping=True)
    imovel_final_f    = locale.currency(imovel_final, grouping=True)

    mes_turnover = 0

    if  aplicacao_final > imovel_final:
        texto_melhor_escolha = "Após {} anos".format(anos) ,f"O valor total da Aplicação será {aplicacao_final_f}.",f"O valor total do Imóvel será {imovel_final_f}.","Portanto é mais vantajoso ALUGAR o imóvel."
    else:
        texto_melhor_escolha = "Após {} anos".format(anos) ,f"O valor total da Aplicação será {aplicacao_final_f}.",f"O valor total do Imóvel será {imovel_final_f}.","Portanto é mais vantajoso COMPRAR o imóvel." 
   
    for chave, valor in resultado.items():
        if "SIM" in valor:
           mes_turnover = chave
        
        if mes_turnover > 0:
           valor_turnover_aplicacao = locale.currency(resultado[mes_turnover][0], grouping=True)
           valor_turnover_imovel    = locale.currency(resultado[mes_turnover][1], grouping=True)

           texto_turnover_mes       = f"Turnover após {mes_turnover} meses"
           texto_turnover_aplicacao = f"Valor da aplicação: {valor_turnover_aplicacao}"
           texto_turnover_imovel    = f"Valor do imóvel: {valor_turnover_imovel}"

           if resultado[mes_turnover][0] > resultado[mes_turnover][1]:
               diferenca = resultado[mes_turnover][0] - resultado[mes_turnover][1]
           else:
               diferenca = resultado[mes_turnover][1] - resultado[mes_turnover][0]

           diferenca = locale.currency(diferenca, grouping=True)

           texto_turnover_diferenca = f"Diferença: {diferenca}"
           texto_turnover_resumo    = texto_turnover_mes, texto_turnover_aplicacao, texto_turnover_imovel, texto_turnover_diferenca

           texto = texto_melhor_escolha, texto_turnover_resumo
        else:
           texto = texto_melhor_escolha, "Não houve Turnover"   
    return texto

@app.get('/grafico/{valor_aluguel}/{valor_imovel}/{taxa_valorizacao_imovel}/{taxa_reajuste_aluguel}/{taxa_juros_aplicacao}/{anos}',response_class=HTMLResponse)
def obter_resultado2(valor_aluguel,valor_imovel,taxa_valorizacao_imovel,taxa_reajuste_aluguel,taxa_juros_aplicacao,anos):
    resultado = calc(valor_aluguel,valor_imovel,taxa_valorizacao_imovel,taxa_reajuste_aluguel,taxa_juros_aplicacao,anos)
    
    meses = list(resultado.keys())
    aplicacao = [valor[0] for valor in resultado.values()]
    imovel = [valor[1] for valor in resultado.values()]

    # Cria o gráfico usando Matplotlib
    plt.plot(meses, aplicacao, label='Montante Aplicação')
    plt.plot(meses, imovel, label='Valorização Imovel')

    # Configurações do gráfico
    plt.xlabel('Mês')
    plt.ylabel('Valor R$')
    plt.title('Comparação entre a Aplicação e a Valorização do Imóvel')
    plt.legend()  # Mostra a legenda com os rótulos dos valores
    
    # Salva o gráfico em um buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    # Codifica o gráfico em base64 para exibição no HTML
    encoded_graph = base64.b64encode(buffer.read()).decode()

    # Monta a tag HTML com a imagem incorporada
    html_content = f"<img src='data:image/png;base64,{encoded_graph}'/>"

    return html_content

@app.get('/exporta/{valor_aluguel}/{valor_imovel}/{taxa_valorizacao_imovel}/{taxa_reajuste_aluguel}/{taxa_juros_aplicacao}/{anos}')
def obter_resultado3(valor_aluguel,valor_imovel,taxa_valorizacao_imovel,taxa_reajuste_aluguel,taxa_juros_aplicacao,anos):
    resultado = calc(valor_aluguel,valor_imovel,taxa_valorizacao_imovel,taxa_reajuste_aluguel,taxa_juros_aplicacao,anos)
    
    try:
      arquivo_json = 'dados.json'

      with open(arquivo_json, 'w') as arquivo:
          json.dump(resultado, arquivo)
      mensagem = f"Resultados mês a mês exportados com sucesso no arquivo {arquivo_json}"
    except:
      mensagem = f"Falha ao tentar exportar arquivo"
      
    return mensagem