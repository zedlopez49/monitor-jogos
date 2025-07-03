import requests
import time
from datetime import datetime
import logging
import sys

# ========= CONFIGURAÇÕES =========
API_KEY = '0b671451eedf48c69929eb752fb15928'
TELEGRAM_TOKEN = '7525855107:AAFEL4KRpSDS_9899udJYhcz-dQ02H6-wQ4'
TELEGRAM_CHAT_ID = '949822874'
CHECK_INTERVAL = 60  # Intervalo em produção (segundos)
HEARTBEAT_INTERVAL = 3600  # Intervalo para alertas de operação (1 hora em segundos)

# Modo operacional
MODO_TESTE = False  # True para teste, False para produção
INTERVALO_TESTE = 10  # Intervalo entre verificações em modo teste (segundos)

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

def gerar_dados_teste(ciclo=0):
    """Gera dados simulados variados para teste"""
    cenarios = [
        {  # Cenário 1: Dois jogos com alerta
            'jogos': [
                {
                    'homeTeam': {'name': 'Flamengo', 'shortName': 'FLM'},
                    'awayTeam': {'name': 'Vasco da Gama', 'shortName': 'VAS'},
                    'score': {'fullTime': {'home': 1, 'away': 1}},
                    'minute': 73,
                    'status': 'IN_PLAY',
                    'competition': {'name': 'Brasileirão Série A'}
                },
                {
                    'homeTeam': {'name': 'São Paulo', 'shortName': 'SAO'},
                    'awayTeam': {'name': 'Palmeiras', 'shortName': 'PAL'},
                    'score': {'fullTime': {'home': 2, 'away': 1}},
                    'minute': 73,
                    'status': 'IN_PLAY',
                    'competition': {'name': 'Brasileirão Série A'}
                }
            ],
            'descricao': "✅ Dois jogos devem gerar alerta (1-1 e 2-1 no 73')"
        },
        {  # Cenário 2: Apenas um jogo com alerta
            'jogos': [
                {
                    'homeTeam': {'name': 'Corinthians', 'shortName': 'COR'},
                    'awayTeam': {'name': 'Santos', 'shortName': 'SAN'},
                    'score': {'fullTime': {'home': 0, 'away': 0}},
                    'minute': 73,
                    'status': 'IN_PLAY',
                    'competition': {'name': 'Brasileirão Série A'}
                }
            ],
            'descricao': "✅ Um jogo deve gerar alerta (0-0 no 73')"
        },
        {  # Cenário 3: Nenhum jogo para alertar
            'jogos': [
                {
                    'homeTeam': {'name': 'Grêmio', 'shortName': 'GRE'},
                    'awayTeam': {'name': 'Internacional', 'shortName': 'INT'},
                    'score': {'fullTime': {'home': 1, 'away': 0}},
                    'minute': 50,
                    'status': 'IN_PLAY',
                    'competition': {'name': 'Brasileirão Série A'}
                }
            ],
            'descricao': "⏭️ Nenhum jogo deve gerar alerta (1-0 no 50')"
        }
    ]
    
    cenario = ciclo % len(cenarios)
    logging.info(f"\n🔁 Modo Teste - Ciclo {ciclo+1}: {cenarios[cenario]['descricao']}")
    return cenarios[cenario]['jogos']

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

def buscar_jogos(ciclo=0):
    """Seleciona fonte de dados conforme modo"""
    if MODO_TESTE:
        return gerar_dados_teste(ciclo)
    else:
        return buscar_jogos_reais()

def monitorar():
    """Função principal de monitoramento"""
    logging.info(f"⚽ Iniciando monitoramento (Modo {'TESTE' if MODO_TESTE else 'PRODUÇÃO'})")
    enviar_telegram(f"🟢 Monitor Iniciado\nModo: {'TESTE' if MODO_TESTE else 'PRODUÇÃO'}")

    ciclo = 0
    ultimo_heartbeat = time.time()
    
    try:
        while True:
            agora = time.time()
            
            # Verifica se é hora de enviar o alerta de operação
            if agora - ultimo_heartbeat >= HEARTBEAT_INTERVAL:
                mensagem_status = (
                    f"🟢 <b>Status do Monitor</b>\n"
                    f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                    f"⚙️ Operando normalmente\n"
                    f"🔄 Ciclos completados: {ciclo}\n"
                    f"📡 Modo: {'TESTE' if MODO_TESTE else 'PRODUÇÃO'}"
                )
                enviar_telegram(mensagem_status)
                ultimo_heartbeat = agora
            
            jogos = buscar_jogos(ciclo)
            
            if not jogos:
                logging.info("Nenhum jogo encontrado nesta verificação")
                time.sleep(INTERVALO_TESTE if MODO_TESTE else CHECK_INTERVAL)
                ciclo += 1
                continue

            alertas_enviados = 0
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
                            f"#AlertaApostas\n"
                            f"🔹 Modo Teste - Ciclo {ciclo+1}"
                        )
                        logging.info(mensagem)
                        enviar_telegram(mensagem)
                        alertas_enviados += 1

                except KeyError as e:
                    logging.warning(f"Dados incompletos do jogo: {e}")
                    continue

            if MODO_TESTE and alertas_enviados == 0:
                logging.info("ℹ️ Nenhum alerta gerado neste ciclo de teste")

            ciclo += 1
            intervalo = INTERVALO_TESTE if MODO_TESTE else CHECK_INTERVAL
            logging.info(f"\n⏳ Próxima verificação em {intervalo}s...")
            time.sleep(intervalo)

    except KeyboardInterrupt:
        logging.info("Monitoramento encerrado pelo usuário")
        enviar_telegram("🔴 Monitor Desativado")
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

    print(f"\n{'='*50}")
    print(f"⚙️ Configurações Carregadas")
    print(f"Modo: {'TESTE' if MODO_TESTE else 'PRODUÇÃO'}")
    print(f"Intervalo: {INTERVALO_TESTE if MODO_TESTE else CHECK_INTERVAL}s")
    print(f"Placar Alvo: {', '.join(TARGET_SCORES)}")
    print(f"Intervalo Heartbeat: {HEARTBEAT_INTERVAL//3600}h")
    print(f"{'='*50}\n")

    monitorar()
