CMD_BID = "BID"          # BID <valor> - enviar lance
CMD_STATUS = "STATUS"    # STATUS - solicitar estado do leilão
CMD_QUIT = "QUIT"        # QUIT - desconectar

# ── Respostas do Servidor → Cliente ──
RESP_WELCOME = "WELCOME"           # Boas-vindas ao conectar
RESP_BID_OK = "BID_OK"             # Lance aceito
RESP_BID_REJECTED = "BID_REJECTED" # Lance rejeitado
RESP_STATUS = "STATUS_RESP"        # Resposta ao STATUS
RESP_NOTIFICATION = "NOTIFICATION" # Broadcast para todos
RESP_OK = "OK"                     # Mensagem informativa
RESP_ERROR = "ERRO"                # Comando desconhecido

# ── Configurações de Rede ──
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
BUFFER_SIZE = 4096
ENCODING = "utf-8"