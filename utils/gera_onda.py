import math
import datetime
import serial
import struct
import time
import matplotlib.pyplot as plt

SERIAL_PORT = 'COM6'
BAUD_RATE = 115200

#CMD_RECEIVE_INT = 1
#CMD_SEND_INT = 2
CMD_RECEIVE_VECTOR = 1
CMD_SEND_VECTOR = 2

def gerar_vetor_dac_parametrizado(frequencia_onda, amostras_por_ciclo, dac_bits, amplitude_normalizada):
    if amostras_por_ciclo <= 0:
        raise ValueError("O número de amostras por ciclo deve ser maior que zero.")
    if dac_bits <= 0:
        raise ValueError("A resolução do DAC em bits deve ser maior que zero.")
    if frequencia_onda <= 0:
        raise ValueError("A frequência da onda deve ser maior que zero.")
    if not (0 <= amplitude_normalizada <= 1):
        raise ValueError("A amplitude normalizada deve estar entre 0 e 1.")

    max_dac_val = (2**dac_bits) - 1
    offset = max_dac_val / 2.0
    amplitude_dac = amplitude_normalizada * (max_dac_val / 2.0)

    dac_valores = [
        int(round(max(0, min(offset + amplitude_dac * math.sin(2 * math.pi * i / amostras_por_ciclo), max_dac_val))))
        for i in range(amostras_por_ciclo)
    ]

    frequencia_amostragem = frequencia_onda * amostras_por_ciclo
    return dac_valores, frequencia_amostragem

def plotar_senoide(dac_valores):
    plt.figure(figsize=(10, 4))
    plt.plot(dac_valores, marker='o', linestyle='-', color='blue')
    plt.title("Forma de Onda Gerada")
    plt.xlabel("Amostra")
    plt.ylabel("Valor DAC")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def salvar_vetor_em_arquivo_c(filename, vetor_dac, freq_onda, num_amostras, res_dac, amp_norm, freq_amostragem, prd_timer_val):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, "w") as f_c:
        f_c.write(f"/*\n * Arquivo gerado por script Python em {current_time}\n")
        f_c.write(f" * Frequência da Onda: {freq_onda} Hz\n")
        f_c.write(f" * Amostras por Ciclo: {num_amostras}\n")
        f_c.write(f" * Resolução do DAC: {res_dac} bits\n")
        f_c.write(f" * Amplitude Normalizada: {amp_norm}\n")
        f_c.write(f" * Frequência de Amostragem: {freq_amostragem:.2f} Hz\n")
        f_c.write(f" * PRD Timer: {int(round(prd_timer_val))}\n */\n\n")
        f_c.write(f"#include <stdint.h>\n\nconst uint16_t dac_buffer[{len(vetor_dac)}] = {{\n")
        for i, val in enumerate(vetor_dac):
            f_c.write(f"    {val},")
            if (i + 1) % 10 == 0:
                f_c.write("\n")
            else:
                f_c.write(" ")
        f_c.write("\n};\n")
    print(f"\n✅ Resultados salvos em '{filename}'")

def senoide():
    print("--- Gerador de Vetor DAC para Senoide ---")
    try:
        freq_onda = float(input("Frequência da onda (Hz): "))
        num_amostras = int(input("Amostras por ciclo: "))
        res_dac = int(input("Resolução do DAC (bits): "))
        amplitude_norm = float(input("Amplitude normalizada (0.0 a 1.0): "))

        vetor_dac, freq_amostragem = gerar_vetor_dac_parametrizado(freq_onda, num_amostras, res_dac, amplitude_norm)

        clock_timer = 200_000_000
        prd_timer = (clock_timer / freq_amostragem) - 1

        print("\n--- Resultados ---")
        print(f"Frequência da onda: {freq_onda} Hz")
        print(f"Amostras por ciclo: {num_amostras}")
        print(f"Resolução DAC: {res_dac} bits")
        print(f"Amplitude normalizada: {amplitude_norm}")
        print(f"Frequência de amostragem: {freq_amostragem:.2f} Hz")
        print(f"Valor PRD timer: {int(round(prd_timer))}")
        print(f"Mínimo valor DAC: {min(vetor_dac)}")
        print(f"Máximo valor DAC: {max(vetor_dac)}")

        salvar_vetor_em_arquivo_c("dac_buffer_values.c", vetor_dac, freq_onda, num_amostras, res_dac, amplitude_norm, freq_amostragem, prd_timer)
        plotar_senoide(vetor_dac)

        return vetor_dac, freq_amostragem

    except ValueError as e:
        print(f"Erro de entrada: {e}")
        return [], 0
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return [], 0


def send_vector(ser_connection, vetor):
    try:
        if not vetor:
            print("Vetor vazio.")
            return
        for val in vetor:
            if not -32768 <= val <= 32767:
                print(f"Valor fora do intervalo permitido: {val}")
                return
        tamanho_bytes = len(vetor) * 2
        #packet = struct.pack('<BH', CMD_RECEIVE_VECTOR, tamanho_bytes)
        packet = struct.pack('<B', CMD_RECEIVE_VECTOR)
        packet += struct.pack('<H', tamanho_bytes)
        for val in vetor:
            packet += struct.pack('<h', val)
        ser_connection.write(packet)
        print("✅ Vetor enviado com sucesso.")
    except Exception as e:
        print(f"Erro: {e}")

def receive_vector(ser_connection):
    try:
          # Envia apenas o comando CMD_SEND_VECTOR com comprimento 0
        request_packet = struct.pack('<BH', CMD_SEND_VECTOR, 0)  # comando + data_len = 0
        ser_connection.write(request_packet)

        time.sleep(0.1)  # espera o DSP responder

        # Lê todos os dados recebidos
        dados_recebidos = ser_connection.read_all()

        if not dados_recebidos:
            print("⚠️ Nenhum dado recebido.")
            return

        # Verifica se tem número par de bytes (uint16 = 2 bytes) ara converter em inteiro
        if len(dados_recebidos) % 2 != 0:
            print("❌ Dados incompletos.")
            return
        
         # Converte os bytes para vetor de inteiros sem sinal (uint16)
        qtd = len(dados_recebidos) // 2
        vetor = struct.unpack('<' + 'H' * qtd, dados_recebidos)

        plotar_senoide(vetor)

        print(f"\n✅ Vetor recebido ({qtd} valores):")
        print(list(vetor))

    except Exception as e:
        print(f"Erro ao receber vetor: {e}")
 

def main():
    vetor_dac = []
    print("\n--- Terminal SCI para F28379D ---")
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
            print(f"Porta serial {SERIAL_PORT} aberta.")

            while True:
                print("\n----- MENU -----")
                print("1. Gerar vetor senoide")
                print("2. Enviar vetor DAC")
                print("3. Receber vetor")
                print("0. Sair")
                opcao = input("Escolha: ")

                if opcao == '1':
                    vetor_dac, _ = senoide()
                elif opcao == '2':
                    if not vetor_dac:
                        print("⚠️  Primeiro gere a senoide antes de enviar o vetor.")
                    else:
                        send_vector(ser, vetor_dac)
                elif opcao == '3':
                    receive_vector(ser)
                elif opcao == '0':
                    print("Saindo.")
                    break
                else:
                    print("Opção inválida.")
    except serial.SerialException as e:
        print(f"Erro ao abrir porta serial '{SERIAL_PORT}': {e}")

if __name__ == "__main__":
    main()