import socket
import threading
import sys
import time

from protocol import (
    CMD_QUIT,
    RESP_WELCOME, RESP_BID_OK, RESP_BID_REJECTED,
    RESP_STATUS, RESP_NOTIFICATION, RESP_OK, RESP_ERROR,
    DEFAULT_PORT, BUFFER_SIZE, ENCODING,
)

CLIENT_HOST = "127.0.0.1"


class ClienteTransportadora:

    def __init__(self, host: str, porta: int):
        self.host = host
        self.porta = porta
        # UDP socket com pseudo-conexão: filtra datagrams para receber só do servidor
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((host, porta))
        self.ativo = False

    def _thread_escuta(self):
        while self.ativo:
            try:
                dados = self.socket.recv(BUFFER_SIZE)
                if not dados:
                    break
                mensagem = dados.decode(ENCODING).strip()
                if mensagem:
                    self._exibir_mensagem(mensagem)
            except OSError:
                if self.ativo:
                    print("\n[ERRO] Falha ao receber dados do servidor.")
                break

    def _exibir_mensagem(self, mensagem: str):
        if mensagem.startswith(RESP_WELCOME):
            conteudo = mensagem[len(RESP_WELCOME) + 1:]
            print(f"\n{'='*50}")
            print(f"  {conteudo}")
            print(f"{'='*50}")

        elif mensagem.startswith(RESP_NOTIFICATION):
            conteudo = mensagem[len(RESP_NOTIFICATION) + 1:]
            print(f"\n  📢 {conteudo}")
            print("  > ", end="", flush=True)

        elif mensagem.startswith(RESP_BID_OK):
            conteudo = mensagem[len(RESP_BID_OK) + 1:]
            print(f"\n  ✅ {conteudo}")

        elif mensagem.startswith(RESP_BID_REJECTED):
            conteudo = mensagem[len(RESP_BID_REJECTED) + 1:]
            print(f"\n  ❌ {conteudo}")

        elif mensagem.startswith(RESP_STATUS):
            conteudo = mensagem[len(RESP_STATUS):].strip()
            print(f"\n{conteudo}")

        elif mensagem.startswith(RESP_OK):
            conteudo = mensagem[len(RESP_OK) + 1:]
            print(f"\n  ℹ️  {conteudo}")

        elif mensagem.startswith(RESP_ERROR):
            conteudo = mensagem[len(RESP_ERROR) + 1:]
            print(f"\n  ⚠️  {conteudo}")

        else:
            print(f"\n  [SERVIDOR] {mensagem}")

    def _enviar(self, mensagem: str):
        try:
            self.socket.send((mensagem + "\n").encode(ENCODING))
        except OSError:
            print("[ERRO] Falha ao enviar mensagem.")
            self.ativo = False

    def executar(self):
        nome = input("  > Nome da transportadora: ").strip()
        if not nome:
            nome = "Transportadora Anônima"

        self.ativo = True
        escuta = threading.Thread(target=self._thread_escuta, daemon=True)
        escuta.start()

        # Primeiro envio = registro: o servidor usa esta mensagem como nome
        self._enviar(nome)
        print(f"[CONEXÃO] Conectado ao servidor UDP {self.host}:{self.porta}")

        time.sleep(0.5)

        print("\nDigite seus comandos (BID <valor>, STATUS, QUIT):")
        while self.ativo:
            try:
                comando = input("  > ").strip()
                if not comando:
                    continue

                self._enviar(comando)

                if comando.upper() == CMD_QUIT:
                    time.sleep(0.3)
                    self.ativo = False
                    break

            except (KeyboardInterrupt, EOFError):
                print("\n[CLIENTE] Encerrando...")
                self._enviar(CMD_QUIT)
                self.ativo = False
                break

        self.socket.close()
        print("Conexão encerrada. Até mais!")


def main():
    host = CLIENT_HOST
    porta = DEFAULT_PORT

    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            porta = int(sys.argv[2])
        except ValueError:
            print("Uso: python3 client.py [host] [porta]")
            sys.exit(1)

    cliente = ClienteTransportadora(host, porta)
    cliente.executar()


if __name__ == "__main__":
    main()
