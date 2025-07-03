import requests
import time
from datetime import datetime
import logging
import sys

# ========= CONFIGURAÇÕES =========
API_KEY = '0b671451eedf48c69929eb752fb15928'
TELEGRAM_TOKEN = '7525855107:AAFEL4KRpSDS_9899udJYhcz-dQ02H6-wQ4'
TELEGRAM_CHAT_ID = '949822874'
CHECK_INTERVAL = 60  # Em segundos

# Modo operacional (True para teste, False para produção)
MODO_TESTE = True

# Placar alvo no minuto 73
TARGET_SCORES = ['0-0', '1-0', '0-1', '1-1', '2-1', '1-2', '2-2', '3-2', '2-3', '3-3']

# ========= FUNÇÕES PRINCIPAIS =========
def enviar_telegram(mensagem):
    """Envia mensagem para o Telegram com tratamento de erros"""
    try:
        resposta = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': mensagem,
                'parse_mode': 'HTML'
            },
            timeout=10
        )
        return resposta.status_code == 200
    except Exception as e:
        logging.error(f"Erro no Telegram: {e}")
        return False

def gerar_dados_teste():
    """Gera dados simulados para teste"""
    return [
        {  # Jogo que deve gerar alerta (1-1 no minuto 73)
            'homeTeam': {'name': 'Flamengo', 'shortName': 'FLM'},
            'awayTeam': {'name': 'Vasco da Gama', 'shortName': 'VAS'},
            'score': {'fullTime': {'home': 1, 'away': 1}},
            'minute': 73,
            'status': 'IN_PLAY',
            'competition': {'name': 'Campeonato Brasileiro Série A'}
        },
        {  # Jogo que NÃO deve gerar alerta (0-0 no minuto 50)
            'homeTeam': {'name': 'Palmeiras', 'shortName': 'PAL'},
            'awayTeam': {'name': 'Corinthians', 'shortName': 'COR'},
            'score': {'fullTime': {'home': 0, 'away': 0}},
            'minute': 50,
            'status': 'IN_PLAY',
            'competition': {'name': 'Campeonato Brasileiro Série A'}
        }
    ]

def buscar_jogos_reais():
    """Busca jogos ao vivo na API Football-Data"""
    try:
        resposta = requests.get(
            "https://api.football-data.org/v4/matches",
            headers={'X-Auth-Token': API_KEY},
            timeout=15
        )
        if resposta.status_code == 200:
            return resposta.json().get('matches', [])
        logging.error(f"Erro API: {resposta.status_code}")
        return None
    except Exception as e:
        logging.error(f"Falha na conexão: {e}")
        return None

def buscar_jogos():
    """Seleciona fonte de dados conforme modo"""
    if MODO_TESTE:
        logging.info("⚠️ MODO TESTE ATIVADO - Dados simulados")
        return gerar_dados_teste()
    else:
        return buscar_jogos_reais()

def monitorar():
    """Função principal de monitoramento"""
    logging.info(f"⚽ Iniciando monitoramento (Modo {'TESTE' if MODO_TESTE else 'PRODUÇÃO'})")
    enviar_telegram(f"🟢 Monitor Iniciado\nModo: {'TESTE' if MODO_TESTE else 'PRODUÇÃO'}")

    try:
        while True:
            jogos = buscar_jogos()
            
            if not jogos:
                logging.info("Nenhum jogo encontrado nesta verificação")
                time.sleep(CHECK_INTERVAL)
                continue

            for jogo in jogos:
                try:
                    casa = jogo['homeTeam'].get('name', jogo['homeTeam']['shortName'])
                    fora = jogo['awayTeam'].get('name', jogo['awayTeam']['shortName'])
                    placar = f"{jogo['score']['fullTime']['home']}-{jogo['score']['fullTime']['away']}"
                    minuto = jogo.get('minute', 0)
                    liga = jogo.get('competition', {}).get('name', 'Sem info')

                    if minuto == 73 and placar in TARGET_SCORES:
                        mensagem = (
                            f"⚽ <b>ALERTA DE JOGO!</b> ⚔️\n"
                            f"🏆 <b>{liga}</b>\n"
                            f"🔸 {casa} {placar} {fora}\n"
                            f"⏱️ <b>Minuto 73'</b>\n"
                            f"#AlertaApostas"
                        )
                        logging.info(mensagem)
                        enviar_telegram(mensagem)

                except KeyError as e:
                    logging.warning(f"Dados incompletos do jogo: {e}")
                    continue

            if MODO_TESTE:
                break  # Encerra após 1 ciclo em modo teste
                
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logging.info("Monitoramento encerrado pelo usuário")
    except Exception as e:
        logging.critical(f"ERRO GRAVE: {e}")
        enviar_telegram(f"🔴 <b>Falha crítica:</b>\n{str(e)}")

# ========= EXECUÇÃO =========
if __name__ == "__main__":
    # Configuração de logs
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Verificação inicial
    print(f"\n{'='*40}")
    print(f"⚙️ Configurações Carregadas")
    print(f"Modo: {'TESTE' if MODO_TESTE else 'PRODUÇÃO'}")
    print(f"Intervalo: {CHECK_INTERVAL}s")
    print(f"Placar Alvo: {', '.join(TARGET_SCORES)}")
    print(f"{'='*40}\n")

    monitorar()
