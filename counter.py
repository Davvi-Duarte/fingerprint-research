from collections import Counter
import json

# Substitua pelo caminho do seu arquivo
caminho_do_arquivo = "dados_completos.json"

try:
    with open(caminho_do_arquivo, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    # Pegamos a lista de registros (garantindo que se for um dict, pegamos a chave 'records')
    registros = dados.get("records", []) if isinstance(dados, dict) else dados

    # Se 'records' não for uma lista, mas o JSON inteiro já for a lista:
    if not isinstance(registros, list):
        registros = [registros]

    nomes = []

    for reg in registros:
        # Extrai o nome do participante
        nome = reg.get("participant_name")

        if nome:  # Se o campo não estiver vazio/nulo
            # .strip() remove espaços extras nas pontas, .lower() normaliza para minúsculo
            nomes.append(str(nome).strip().lower())

    # O Counter faz a contagem automática de cada incidência
    contagem = Counter(nomes)

    print("--- INCIDÊNCIA DE PARTICIPANTES (NORMALIZADO) ---")
    # Exibe do mais comum para o menos comum
    for participante, total in contagem.most_common():
        # .title() deixa a primeira letra maiúscula apenas para exibição ficar bonita
        print(f"👤 {participante.title()}: {total} vez(es)")

except FileNotFoundError:
    print("Erro: Arquivo não encontrado.")
except json.JSONDecodeError:
    print("Erro: JSON inválido.")