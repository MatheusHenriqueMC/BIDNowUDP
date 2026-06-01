import threading
from datetime import datetime


class LeilaoReverso:

    def __init__(self, descricao_carga: str, valor_inicial: float):
        self.descricao_carga = descricao_carga
        self.valor_inicial = valor_inicial
        self.lance_atual = valor_inicial
        self.lider_atual = None
        self.historico = []
        self.lock = threading.Lock()

    def registrar_lance(self, nome_cliente: str, valor: float) -> tuple[bool, str]:
        """
        Tenta registrar um lance. Usa lock para garantir atomicidade.
        
        Retorna (sucesso, mensagem).
        """
        with self.lock:
            if valor <= 0:
                return False, "O valor do lance deve ser positivo."

            if valor >= self.lance_atual:
                return False, (
                    f"Lance de R${valor:.2f} rejeitado. "
                    f"O lance atual é R${self.lance_atual:.2f}. "
                    f"Seu lance deve ser MENOR que o atual."
                )

            self.lance_atual = valor
            self.lider_atual = nome_cliente
            self.historico.append({
                "cliente": nome_cliente,
                "valor": valor,
                "horario": datetime.now().strftime("%H:%M:%S"),
            })
            return True, f"Lance de R${valor:.2f} registrado com sucesso!"

    def obter_status(self) -> str:
        """Retorna estado atual do leilão de forma thread-safe."""
        with self.lock:
            linhas = [
                "=== STATUS DO LEILÃO ===",
                f"Carga: {self.descricao_carga}",
                f"Valor inicial: R${self.valor_inicial:.2f}",
                f"Lance atual (menor): R${self.lance_atual:.2f}",
                f"Líder atual: {self.lider_atual or 'Nenhum lance ainda'}",
                f"Total de lances: {len(self.historico)}",
            ]
            if self.historico:
                linhas.append("--- Últimos 5 lances ---")
                for lance in self.historico[-5:]:
                    linhas.append(
                        f"  {lance['horario']} | {lance['cliente']}: "
                        f"R${lance['valor']:.2f}"
                    )
            linhas.append("========================")
            return "\n".join(linhas)