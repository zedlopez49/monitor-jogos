import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

print("=== INICIANDO VERIFICAÇÃO ===")
print(f"Python version: {sys.version}")
print(f"Requests version: {requests.__version__}")

import requests
import time
from datetime import datetime
import os

# Configurações (substitua com seus dados)
API_KEY = '0b671451eedf48c69929eb752fb15928'  # Sua chave da Football-Data
TELEGRAM_TOKEN = '7525855107:AAFEL4KRpSDS_9899udJYhcz-dQ02H6-wQ4'
TELEGRAM_CHAT_ID = '949822874'
CHECK_INTERVAL = 300  # 5 minutos (evita bloqueio da API)
TARGET_SCORES = ['0-0', '1-0', '0-1', '1-1', '2-1', '1-2', '2-2', '3-2', '2-3', '3-3']

# Configuração para GitHub Actions
os.environ['PYTHONUNBUFFERED'] = '1'  # Logs instantâneos

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
        print(f"[ERRO] Telegram: {e}")
        return False

def buscar_jogos():
    """Busca jogos com tratamento robusto de erros"""
    try:
        resposta = requests.get(
            "https://api.football-data.org/v4/matches",
            headers={'X-Auth-Token': API_KEY},
            timeout=15
        )
        
        if resposta.status_code == 200:
            return resposta.json().get('matches', [])
        else:
            print(f"[ERRO] API: {resposta.status_code} - {resposta.text}")
            enviar_telegram(f"⚠️ Erro na API: {resposta.status_code}")
    except Exception as e:
        print(f"[ERRO] Conexão: {e}")
        enviar_telegram(f"🔴 Falha na conexão: {e}")
    return None

def monitorar():
    """Função principal de monitoramento"""
    print(f"\n⚽ Iniciando monitoramento em {datetime.now().strftime('%d/%m %H:%M')}")
    enviar_telegram("🟢 <b>Monitor Ativado</b>\nIniciando verificação...")

    try:
        jogos = buscar_jogos()
        
        if not jogos:
            print("Nenhum jogo encontrado nesta verificação")
            return

        for jogo in jogos:
            try:
                # Extrai dados com fallback para nomes curtos
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
                    print(mensagem)
                    enviar_telegram(mensagem)

            except KeyError as e:
                continue  # Ignora jogos com dados incompletos

    except Exception as e:
        print(f"[ERRO CRÍTICO] {e}")
        enviar_telegram(f"🔴 <b>Falha crítica:</b>\n{str(e)}")
        raise  # Para aparecer nos logs do GitHub
- name: Notificar falha
  if: failure()
  run: |
    curl -X POST "https://api.telegram.org/bot${{ secrets.TELEGRAM_TOKEN }}/sendMessage" \
    -d "chat_id=${{ secrets.CHAT_ID }}" \
    -d "text=❌ Monitor falhou! Verifique GitHub Actions"
if __name__ == "__main__":
    # Configuração especial para GitHub Actions
    try:
        enviar_telegram("🔔 <b>Sistema Iniciado no GitHub</b>")
        monitorar()
    except Exception as e:
        print(f"[ERRO] {e}")
        exit(1)  # Marca a execução como falha no GitHub
