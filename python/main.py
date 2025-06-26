import serial
import struct
import time

# --- CONFIGURACOES ---
# Altere esta para a porta COM correta do seu microcontrolador
SERIAL_PORT = 'COM6'
BAUD_RATE = 115200

# --- DEFINICOES DO PROTOCOLO (devem ser identicas as do C) ---
# Comandos (do enum SCI_Command_e)
CMD_RECEIVE_INT = 1 # Comando para o PC enviar um int para o 28379D
CMD_SEND_INT    = 2 # Comando para o PC pedir um int para o 28379D
CMD_RECEIVE_VECTOR = 3 # Comando para o PC enviar um vetor para o 28379D
CMD_SEND_VECTOR = 4 # Comando para o PC pedir um vetor para o 28379D



def main():
    """Funcao principal que gerencia a conexao e o menu do usuario."""
    print("--- Terminal de Teste SCI para 28379D ---")
    
    try:
        # Abre a porta serial usando um bloco 'with' para garantir que ela seja fechada
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
            print(f"Porta serial {SERIAL_PORT} aberta com sucesso a {BAUD_RATE} bps.")
            time.sleep(1) # Um pequeno tempo para a serial estabilizar

            while True:
                print("\n----- MENU -----")
                print("1. Enviar um numero inteiro para o 28379D")
                print("2. Receber um numero inteiro do 28379D")
                print("3. Enviar um vetor de inteiros para o 28379D")
                print("4. Receber um vetor do 28379D")
                print("0. Sair")
                
                choice = input("Escolha uma opcao: ")

                if choice == '1':
                    send_int(ser)
                elif choice == '2':
                    receive_int(ser)
                elif choice == '3':
                    send_vector(ser)
                elif choice == '4':
                    receive_vector(ser)
                elif choice == '0':
                    print("Encerrando o programa.")
                    break
                else:
                    print("Opcao invalida. Tente novamente.")

    except serial.SerialException as e:
        print(f"\nERRO: Nao foi possivel abrir a porta serial '{SERIAL_PORT}'.")
        print(f"Detalhe: {e}")
        print("Verifique se a porta esta correta e se nenhum outro programa a esta usando.")


def send_int(ser_connection):
    """
    Pede um numero ao usuario, o empacota e envia para o microcontrolador.
    """
    try:
        num_str = input("Digite um numero inteiro para ENVIAR (entre -32768 e 32767): ")
        number_to_send = int(num_str)

        if not -32768 <= number_to_send <= 32767:
            print("ERRO: O numero esta fora do range permitido para um int16_t.")
            return

        # Empacota o COMANDO e o DADO em uma sequencia de bytes.
        # Formato: '<' (Little-endian), 'B' (byte, para o comando), 'h' (short, para o int16), 'h' para o tamanho do dado.
        packet_to_send = struct.pack('<Bhh', CMD_RECEIVE_INT, 2, number_to_send)
        
        print(f"\nEnviando pacote de {len(packet_to_send)} bytes: {packet_to_send.hex(' ')}")
        ser_connection.write(packet_to_send)
        print("Pacote enviado com sucesso.")

    except ValueError:
        print("ERRO: Entrada invalida. Por favor, digite um numero inteiro.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

def receive_int(ser_connection):
    """
    Envia um comando para o microcontrolador solicitando um dado e depois o recebe.
    """
    try:
        # 1. Envia apenas o COMANDO para solicitar o dado.
        #    O pacote tera 3 bytes.
        request_packet = struct.pack('<Bh', CMD_SEND_INT, 0)

        print(f"\nEnviando comando de solicitacao (1 byte): {request_packet.hex(' ')}")
        ser_connection.write(request_packet)

        # 2. Aguarda a resposta do microcontrolador.
        #    O 28379D deve responder enviando apenas o dado (int16_t = 2 bytes).
        print("Aguardando resposta do 28379D...")
        response_data = ser_connection.read(2)
        ser_connection.flushInput()  # Limpa o buffer de entrada

        if not response_data or len(response_data) < 2:
            print("ERRO: Nao houve resposta do microcontrolador (timeout).")
            return

        # 3. Desempacota os bytes recebidos para um inteiro.
        #    Formato: '<' (Little-endian), 'h' (short, para o int16)
        received_number = struct.unpack('<h', response_data)[0]

        print(f"  -> Numero recebido do 28379D: {received_number}")

    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")


#envio de vetor

def send_vector(ser_connection):
    """
    Envia um vetor de int16_t para o microcontrolador.
    """
    try:
        entrada = input("Digite os inteiros separados por espaço (ex: 10 -20 300 0): ")
        elementos = entrada.strip().split()
        vetor = [int(x) for x in elementos]

        if not vetor:
            print("Vetor vazio. Nada a enviar.")
            return

        for val in vetor:
            if not -32768 <= val <= 32767:
                print(f"ERRO: Valor {val} fora do intervalo permitido (int16_t).")
                return

        # Tamanho em bytes do vetor (cada int16 = 2 bytes)
        tamanho_bytes = len(vetor) * 2

        # Cabeçalho: comando (1 byte) + tamanho (2 bytes)
        packet = struct.pack('<Bh', CMD_RECEIVE_VECTOR, tamanho_bytes)
        # Dados do vetor
        for val in vetor:
            packet += struct.pack('<h', val)

        print(f"\nEnviando pacote de {len(packet)} bytes: {packet.hex(' ')}")
        ser_connection.write(packet)
        print("Vetor enviado com sucesso.")

    except ValueError:
        print("ERRO: Entrada invalida. Certifique-se de digitar apenas inteiros.")
    except Exception as e:
        print(f"Erro inesperado: {e}")

def receive_vector(ser_connection):
    """
    Solicita ao microcontrolador o envio de um vetor de int16_t e o imprime.
    """
    try:
        qtd = input("Quantos inteiros deseja receber do F28379D? ")
        qtd = int(qtd)

        if qtd <= 0 or qtd > 100:
            print("ERRO: Número inválido de elementos (limite: 1 a 100).")
            return

        # 1. Monta o pacote de requisição: comando + payload com quantidade desejada
        # Comando = CMD_SEND_VECTOR, Dado = qtd (int16_t)
        request_packet = struct.pack('<Bhh', CMD_SEND_VECTOR, 2, qtd)

        print(f"\nEnviando comando de requisicao de vetor ({qtd} inteiros)...")
        ser_connection.write(request_packet)

        # 2. Espera os dados: cada int16 = 2 bytes
        expected_bytes = qtd * 2
        print(f"Aguardando {expected_bytes} bytes...")

        response = ser_connection.read(expected_bytes)

        if len(response) < expected_bytes:
            print("ERRO: Resposta incompleta recebida.")
            print(f"Recebido: {response.hex(' ')}")
            return

        # 3. Converte os dados recebidos para vetor de int16
        vetor = list(struct.unpack('<' + 'h' * qtd, response))

        print(f"\n✅ Vetor recebido com {qtd} elementos:")
        print(vetor)

    except ValueError:
        print("ERRO: Entrada inválida.")
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    main()