import socket
import threading
import sys

from protocol import (
    CMD_BID, CMD_STATUS, CMD_QUIT,
    RESP_WELCOME, RESP_BID_OK, RESP_BID_REJECTED,
    RESP_STATUS, RESP_NOTIFICATION, RESP_OK, RESP_ERROR,
    DEFAULT_HOST, DEFAULT_PORT, BUFFER_SIZE, ENCODING,
)
from auction import LeilaoReverso


class ServidorLeilao:

    def __init__(self, host: str, porta: int, leilao: LeilaoReverso):
        self.host = host
        self.porta = porta
        self.leilao = leilao

        # Clientes registrados: {(host, port): nome}
        self.clientes: dict[tuple, str] = {}
        self.clientes_lock = threading.Lock()

        # Socket UDP (AF_INET = IPv4, SOCK_DGRAM = UDP)
        self.servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def iniciar(self):
        self.servidor_socket.bind((self.host, self.porta))

        print(f"{'='*55}")
        print(f"  SERVIDOR DE LEILÃO DE FRETES (UDP)")
        print(f"  Carga: {self.leilao.descricao_carga}")
        print(f"  Valor inicial: R${self.leilao.valor_inicial:.2f}")
        print(f"  Escutando em {self.host}:{self.porta}")
        print(f"{'='*55}")

        try:
            while True:
                dados, endereco = self.servidor_socket.recvfrom(BUFFER_SIZE)
                mensagem = dados.decode(ENCODING).strip()
                if mensagem:
                    threading.Thread(
                        target=self._tratar_mensagem,
                        args=(endereco, mensagem),
                        daemon=True,
                    ).start()
        except KeyboardInterrupt:
            print("\n[SERVIDOR] Encerrando...")
        finally:
            self.servidor_socket.close()

    def _tratar_mensagem(self, endereco: tuple, mensagem: str):
        with self.clientes_lock:
            nome = self.clientes.get(endereco)

        if nome is None:
            # Primeiro datagrama do endereço: mensagem é o nome da transportadora
            nome = mensagem.strip()
            with self.clientes_lock:
                self.clientes[endereco] = nome

            self._enviar(endereco,
                f"{RESP_WELCOME} Bem-vindo à Plataforma de Negociação de Fretes!\n"
                f"Olá, {nome}! Você está participando do leilão.\n"
                f"Comandos disponíveis:\n"
                f"  BID <valor>  - Enviar um lance (ex: BID 1500.00)\n"
                f"  STATUS       - Ver estado do leilão\n"
                f"  QUIT         - Sair"
            )
            print(f"[REGISTRO] Transportadora '{nome}' registrada ({endereco})")
            self._broadcast(
                f"{RESP_NOTIFICATION} A transportadora '{nome}' entrou no leilão.",
                excluir=endereco,
            )
            return

        self._processar_comando(endereco, nome, mensagem)

    def _processar_comando(self, endereco: tuple, nome: str, mensagem: str):
        partes = mensagem.split(maxsplit=1)
        comando = partes[0].upper()

        if comando == CMD_BID:
            self._cmd_bid(endereco, nome, partes)
        elif comando == CMD_STATUS:
            self._cmd_status(endereco)
        elif comando == CMD_QUIT:
            self._enviar(endereco, f"{RESP_OK} Até mais! Obrigado por participar.")
            with self.clientes_lock:
                self.clientes.pop(endereco, None)
            print(f"[DESCONEXÃO] '{nome}' saiu")
            self._broadcast(f"{RESP_NOTIFICATION} A transportadora '{nome}' saiu do leilão.")
        else:
            self._enviar(endereco,
                f"{RESP_ERROR} Comando '{comando}' desconhecido. "
                f"Use: BID <valor>, STATUS ou QUIT"
            )

    def _cmd_bid(self, endereco: tuple, nome: str, partes: list):
        if len(partes) < 2:
            self._enviar(endereco,
                f"{RESP_BID_REJECTED} Uso correto: BID <valor> (ex: BID 1500.00)")
            return

        try:
            valor = float(partes[1].replace(",", "."))
        except ValueError:
            self._enviar(endereco,
                f"{RESP_BID_REJECTED} Valor inválido. Use formato numérico (ex: BID 1500.00)")
            return

        sucesso, msg = self.leilao.registrar_lance(nome, valor)

        if sucesso:
            self._enviar(endereco, f"{RESP_BID_OK} {msg}")
            print(f"[LANCE] {nome} -> R${valor:.2f} ✓")
            self._broadcast(
                f"{RESP_NOTIFICATION} Novo menor lance! {nome} ofereceu R${valor:.2f}"
            )
        else:
            self._enviar(endereco, f"{RESP_BID_REJECTED} {msg}")
            print(f"[LANCE] {nome} -> R${valor:.2f} ✗")

    def _cmd_status(self, endereco: tuple):
        status = self.leilao.obter_status()
        self._enviar(endereco, f"{RESP_STATUS}\n{status}")

    def _enviar(self, endereco: tuple, mensagem: str):
        try:
            self.servidor_socket.sendto((mensagem + "\n").encode(ENCODING), endereco)
        except OSError:
            pass

    def _broadcast(self, mensagem: str, excluir: tuple = None):
        with self.clientes_lock:
            destinatarios = [addr for addr in self.clientes if addr != excluir]
        for addr in destinatarios:
            self._enviar(addr, mensagem)


def main():
    porta = DEFAULT_PORT

    if len(sys.argv) >= 2:
        try:
            porta = int(sys.argv[1])
        except ValueError:
            print("Uso: python3 server.py [porta]")
            sys.exit(1)

    leilao = LeilaoReverso(
        descricao_carga="20 toneladas de soja — São Paulo/SP → Recife/PE",
        valor_inicial=5000.00,
    )

    servidor = ServidorLeilao(DEFAULT_HOST, porta, leilao)
    servidor.iniciar()


if __name__ == "__main__":
    main()
