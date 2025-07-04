import math
import datetime
import serial
import struct
import time
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
import matplotlib.ticker as ticker

SERIAL_PORT = 'COM6'
BAUD_RATE = 115200

#CMD_RECEIVE_INT = 1
#CMD_SEND_INT = 2
CMD_RECEIVE_VECTOR = 1
CMD_SEND_VECTOR = 2

def gerar_vetor_dac_parametrizado(frequencia_onda, amostras_por_ciclo, dac_bits, amplitude_normalizada,porcentagem_quinta,porcentagem_14,porcentagem_32):
    if amostras_por_ciclo <= 0:
        raise ValueError("O número de amostras por ciclo deve ser maior que zero.")
    if dac_bits <= 0:
        raise ValueError("A resolução do DAC em bits deve ser maior que zero.")
    if frequencia_onda <= 0:
        raise ValueError("A frequência da onda deve ser maior que zero.")
    if porcentagem_quinta < 0:
        raise ValueError("A porcentagem da frequência de 5º ordem deve ser positiva.")
    if porcentagem_14 < 0:
        raise ValueError("A porcentagem da frequência de 15º ordem deve ser positiva.")
    if porcentagem_32 < 0:
        raise ValueError("A porcentagem da frequência de 32º ordem deve ser positiva.")
    if not (0 <= amplitude_normalizada <= 1):
        raise ValueError("A amplitude normalizada deve estar entre 0 e 1.")

    max_dac_val = (2**dac_bits) - 1
    offset = max_dac_val / 2.0
    amplitude_dac = amplitude_normalizada * (max_dac_val / 2.0)
    amplitude_dac_quinta = (porcentagem_quinta/100) * amplitude_dac
    amplitude_dac_14 = (porcentagem_14/100) * amplitude_dac
    amplitude_dac_32 = (porcentagem_32/100) * amplitude_dac
    dac_valores = [
        int(round(max(0, min(offset + 
                             amplitude_dac * math.sin(2* math.pi * i / amostras_por_ciclo)+
                             amplitude_dac_quinta * math.sin(9 * 2 * math.pi * i / amostras_por_ciclo) +
                             amplitude_dac_14 * math.sin(12 * 2 * math.pi * i / amostras_por_ciclo)+
                             amplitude_dac_32 * math.sin(14 * 2 * math.pi * i / amostras_por_ciclo),
                             max_dac_val))))
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

def plotar_dac_adc_comparativo(dac_valores, adc_valores):
    if not dac_valores or not adc_valores:
        print("⚠️  DAC ou ADC vazio, impossível plotar.")
        return

    plt.figure(figsize=(10, 4))
    plt.plot(dac_valores, label='DAC Enviado', marker='o', linestyle='-', color='blue')
    plt.plot(adc_valores, label='ADC Recebido', marker='x', linestyle='-', color='red')
    plt.title("Comparação DAC vs ADC")
    plt.xlabel("Amostra")
    plt.ylabel("Valor")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def salvar_vetor_em_arquivo_c(filename, vetor_dac, freq_onda, num_amostras, res_dac, amp_norm, porc_amplitude_quinta, porc_amplitude_14, porc_amplitude_32, freq_amostragem, prd_timer_val):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, "w") as f_c:
        f_c.write(f"/*\n * Arquivo gerado por script Python em {current_time}\n")
        f_c.write(f" * Frequência da Onda: {freq_onda} Hz\n")
        f_c.write(f" * Amostras por Ciclo: {num_amostras}\n")
        f_c.write(f" * Resolução do DAC: {res_dac} bits\n")
        f_c.write(f" * Amplitude Normalizada: {amp_norm}\n")
        f_c.write(f" * Porcentagem 5º: {porc_amplitude_quinta}\n")
        f_c.write(f" * Porcentagem 14º: {porc_amplitude_14}\n")
        f_c.write(f" * Porcentagem 32º: {porc_amplitude_32}\n")
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
        porc_amplitude_quinta = float(input("Porcentagem da 5ª Harmônica: "))
        porc_amplitude_14 = float(input("Porcentagem da 14ª Harmônica: "))
        porc_amplitude_32 = float(input("Porcentagem da 32ª Harmônica: "))
        vetor_dac, freq_amostragem = gerar_vetor_dac_parametrizado(freq_onda, num_amostras, res_dac, amplitude_norm, porc_amplitude_quinta, porc_amplitude_14, porc_amplitude_32)

        clock_timer = 200_000_000 
        prd_timer = (clock_timer / freq_amostragem) - 1


        print("\n--- Resultados ---")
        print(f"Frequência da onda: {freq_onda} Hz")
        print(f"Amostras por ciclo: {num_amostras}")
        print(f"Resolução DAC: {res_dac} bits")
        print(f"Amplitude normalizada: {amplitude_norm}")
        print(f"Porcentagem 5º: {porc_amplitude_quinta}")
        print(f"Porcentagem 14º: {porc_amplitude_14}")
        print(f"Porcentagem 32º: {porc_amplitude_32}")
        print(f"Frequência de amostragem: {freq_amostragem:.2f} Hz")
        print(f"Valor PRD timer: {int(round(prd_timer))}")
        print(f"Mínimo valor DAC: {min(vetor_dac)}")
        print(f"Máximo valor DAC: {max(vetor_dac)}")

        salvar_vetor_em_arquivo_c("dac_buffer_values.c", vetor_dac, freq_onda, num_amostras, res_dac, amplitude_norm, porc_amplitude_quinta, porc_amplitude_14, porc_amplitude_32, freq_amostragem, prd_timer)
        plotar_senoide(vetor_dac)

        return vetor_dac, freq_amostragem

    except ValueError as e:
        print(f"Erro de entrada: {e}")
        return [], 0
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return [], 0

def calcular_freq_amostragem_adc(f_timer_clk_ADC, prd):
    return f_timer_clk_ADC / (prd + 1)

def comparar_fft_dac_adc(dac_valores, adc_valores, freq_amostragem_dac, freq_amostragem_adc):
    if not dac_valores or not adc_valores:
        print("⚠️ DAC ou ADC vazio, impossível comparar FFT.")
        return

    # Preparar arrays
    n_dac = len(dac_valores)
    n_adc = len(adc_valores)

    dac_arr = np.array(dac_valores) - np.mean(dac_valores)
    adc_arr = np.array(adc_valores) - np.mean(adc_valores)

    # FFT
    fft_dac = np.fft.fft(dac_arr)
    fft_adc = np.fft.fft(adc_arr)

    # Frequências
    freq_dac = np.fft.fftfreq(n_dac, d=1/freq_amostragem_dac)
    freq_adc = np.fft.fftfreq(n_adc, d=1/freq_amostragem_adc)

    # Metades positivas
    metade_dac = n_dac // 2
    metade_adc = n_adc // 2

    freq_dac_pos = freq_dac[:metade_dac]
    freq_adc_pos = freq_adc[:metade_adc]

    mag_dac = np.abs(fft_dac)[:metade_dac] * 2 / n_dac
    mag_adc = np.abs(fft_adc)[:metade_adc] * 2 / n_adc

    # Detectar picos nas FFTs

    limitar_adc = 0.05* np.max(mag_adc)
    peaks_adc, _ = find_peaks(mag_adc, height=limitar_adc)

    limitar_dac = 0.01*np.max(mag_dac)
    peaks_dac, _ = find_peaks(mag_dac, height=limitar_dac)

    peak_freqs_dac = freq_dac_pos[peaks_dac]
    peak_mags_dac = mag_dac[peaks_dac]

    peak_freqs_adc = freq_adc_pos[peaks_adc]
    peak_mags_adc = mag_adc[peaks_adc]

    # Plotagem lado a lado
    plt.figure(figsize=(14,6))

    # FFT DAC
    plt.subplot(1, 3, 1)
    plt.plot(freq_dac_pos, mag_dac, color='blue')
    plt.ylim(-10, 1300)
    plt.scatter(peak_freqs_dac, peak_mags_dac, color='black', zorder=5, label='Picos detectados')
  #  plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(50)) #espaçar em 50 em 50
    for f, m in zip(peak_freqs_dac, peak_mags_dac):
        plt.text(f, m + 0.02, f"{f:.1f} Hz", ha='center', va='bottom', fontsize=8, rotation=45)
    plt.title("FFT DAC (com picos)")
    plt.xlabel("Frequência (Hz)")
    plt.ylabel("Magnitude")
    plt.grid(True)
    plt.legend()

    # FFT ADC
    plt.subplot(1, 3, 2)
    plt.plot(freq_adc_pos, mag_adc, color='red')
    plt.ylim(-10, 1300)
    plt.scatter(peak_freqs_adc, peak_mags_adc, color='black', zorder=5, label='Picos detectados')
    for f, m in zip(peak_freqs_adc, peak_mags_adc):
        plt.text(f, m + 0.02, f"{f:.1f} Hz", ha='center', va='bottom', fontsize=8, rotation=45)
    plt.title("FFT ADC (com picos)")
    plt.xlabel("Frequência (Hz)")
    plt.ylabel("Magnitude")
    plt.grid(True)
    plt.legend()

    # FFT Comparada
    plt.subplot(1, 3, 3)
    plt.plot(freq_dac_pos, mag_dac, color='blue', label='DAC')
    plt.plot(freq_adc_pos, mag_adc, color='red', label='ADC')
    plt.ylim(-10, 1300)
    plt.scatter(peak_freqs_dac, peak_mags_dac, color='blue', s=20, zorder=5)
    plt.scatter(peak_freqs_adc, peak_mags_adc, color='red', s=20, zorder=5)
    plt.title("FFT DAC x ADC")
    plt.xlabel("Frequência (Hz)")
    plt.ylabel("Magnitude")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()

    # Impressão dos picos
    print("🔷 Picos na FFT do DAC:")
    for f, m in zip(peak_freqs_dac, peak_mags_dac):
        print(f"   → {f:.2f} Hz com magnitude {m:.3f}")

    print("\n🔴 Picos na FFT do ADC:")
    for f, m in zip(peak_freqs_adc, peak_mags_adc):
        print(f"   → {f:.2f} Hz com magnitude {m:.3f}")

    print(f"\nTamanho do vetor DAC: {n_dac} amostras")
    print(f"Tamanho do vetor ADC: {n_adc} amostras")
    
def plot_fft_dac(dac_valores, freq_amostragem):
    if not dac_valores:
        print("⚠️ Vetor DAC vazio, impossível plotar FFT.")
        return
    
    n = len(dac_valores)
    dac_arr = np.array(dac_valores)
    dac_arr = dac_arr- np.mean(dac_arr)  # remove DC
    fft_dac = np.fft.fft(dac_arr)
    freq = np.fft.fftfreq(n, d=1/freq_amostragem)
    metade = n // 2
    magnitude = np.abs(fft_dac)[:metade] * 2 / n


    plt.figure(figsize=(10, 5))
    plt.plot(freq[:metade], magnitude, color='blue')
    plt.title("Espectro de Frequência - FFT do DAC")
    plt.xlabel("Frequência (Hz)")
    plt.ylabel("Magnitude")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

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
       # print(list(vetor))
        return vetor
    
    except Exception as e:
        print(f"Erro ao receber vetor: {e}")
 

def main():

    f_timer_clk_ADC = 100_000_000  # 50 MHz
    freq_amostragem_dac = 0
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
                print("4. Plotar DAC + ADC")
                print("5. Plotar FFT do DAC")
                print("6. Comparar FFT DAC vs ADC")
                print("0. Sair")
                opcao = input("Escolha: ")

                if opcao == '1':
                    vetor_dac, freq_amostragem = senoide()
                elif opcao == '2':
                    if not vetor_dac:
                        print("⚠️  Primeiro gere a senoide antes de enviar o vetor.")
                    else:
                        send_vector(ser, vetor_dac)
                elif opcao == '3':
                    receive_vector(ser)
                elif opcao == '4':
                    if not vetor_dac:
                         print("⚠️  Gere o vetor DAC primeiro.")
                    else:
                        adc_valores = receive_vector(ser)
                        if adc_valores:
                            plotar_dac_adc_comparativo(vetor_dac, adc_valores)   
                elif opcao == '5':
                         if not vetor_dac:
                             print("⚠️  Gere o vetor DAC primeiro.")
                         else:
                             plot_fft_dac(vetor_dac, freq_amostragem)

                elif opcao == '6':
                          if not vetor_dac:
                                print("⚠️ Gere o vetor DAC primeiro.")
                          else:
                                prd_adc_input = input("Digite o valor do PRD do timer do ADC para calcular a frequência de amostragem: ")
                                try:
                                    prd_adc = int(prd_adc_input)
                                    freq_amostragem_adc = calcular_freq_amostragem_adc(f_timer_clk_ADC, prd_adc)
                                    print(f"Frequência de amostragem ADC calculada: {freq_amostragem_adc:.2f} Hz")
                                    adc_valores = receive_vector(ser)
                                    if adc_valores:
                                        comparar_fft_dac_adc(vetor_dac, adc_valores, freq_amostragem, freq_amostragem_adc)
                                except ValueError:
                                     print("Valor inválido para PRD.")
                elif opcao == '0':
                    print("Saindo.")
                    break
                else:
                    print("Opção inválida.")
    except serial.SerialException as e:
        print(f"Erro ao abrir porta serial '{SERIAL_PORT}': {e}")

if __name__ == "__main__":
    main()