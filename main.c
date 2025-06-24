//
// Included Files
//
#include "driverlib.h"
#include "device.h"
#include "board.h"
#include "math.h"
#include "scicomm.h"
//
// Main
//
#define TAM_BUFFER_DAC 200
#define TAM_BUFFER_ADC 100
extern uint16_t dac_buffer[];
volatile uint16_t adc_buffer[TAM_BUFFER_ADC];
volatile float gain = 1.0f;


//DADOS PARA CONEXÃO SERIAL PYTHON COM CCS
volatile Protocol_Header_t g_prot_header = {CMD_NONE,0};
volatile int g_dado;
#define VETOR_TAM_MAX 4
int16_t g_vetor[VETOR_TAM_MAX];



void main(void)
{
    // Device Initialization
    Device_init();


    //
    // Initializes PIE and clears PIE registers. Disables CPU interrupts.
    //
    Interrupt_initModule();
    //
    // Initializes the PIE vector table with pointers to the shell Interrupt
    // Service Routines (ISR).
    //
    Interrupt_initVectorTable();

    Board_init();

    //
    // Enable Global Interrupt (INTM) and realtime interrupt (DBGM)
    //
    EINT;
    ERTM;

    while(1)
    {
        if (g_prot_header.cmd != CMD_NONE)
               {
                   switch (g_prot_header.cmd)
                   {
                       case CMD_RECEIVE_INT:
                           g_dado = protocolReceiveInt(SCI0_BASE);
                           break;

                       case CMD_SEND_INT:
                           protocolSendInt(SCI0_BASE, g_dado);
                           break;

                       case CMD_RECEIVE_VECTOR:
                       {
                           uint16_t num_elem = g_prot_header.data_len / 2;
                           if (num_elem > VETOR_TAM_MAX)
                               num_elem = VETOR_TAM_MAX;

                           protocolReceiveVector(SCI0_BASE, g_vetor, num_elem);
                           break;
                       }
                       case CMD_SEND_VECTOR:
                       {
                           uint16_t qtd;
                           qtd = protocolReceiveInt(SCI0_BASE); // Recebe a quantidade desejada

                           if (qtd > VETOR_TAM_MAX)
                               qtd = VETOR_TAM_MAX;

                           protocolSendVector(SCI0_BASE, g_vetor, qtd); // Envia vetor
                           break;
                       }
                   }

                   // Limpa status de interrupção e reseta comando
                   SCI_clearInterruptStatus(SCI0_BASE, SCI_INT_RXFF);
                   g_prot_header.cmd = CMD_NONE;
               }
    }

}

__interrupt void INT_ADC0_1_ISR(void)
{
    static uint16_t cnt_adc =0;
    cnt_adc = (cnt_adc+1)%TAM_BUFFER_ADC;
    adc_buffer[cnt_adc] = ADC_readResult(ADC0_RESULT_BASE, ADC0_SOC0);
    ADC_clearInterruptStatus(ADC0_BASE, ADC_INT_NUMBER1);
    Interrupt_clearACKGroup(INT_ADC0_1_INTERRUPT_ACK_GROUP);
//cada vez que amostrar coloca um valor novo no adc_buffer
    //tem que limpar porque vai na py
}

//varrer o vetor do python
__interrupt void INT_myCPUTIMER1_ISR(void)
{
    static uint16_t cnt_dac = 0;
    DAC_setShadowValue(DAC0_BASE, (uint16_t) (gain*dac_buffer[cnt_dac]));
    cnt_dac = (cnt_dac+1)%TAM_BUFFER_DAC;

    // 0+10%200 o resto da diviao ate chegar em 1999+1 %200 o resto torna zero
}

// Rotina de Interrupção da SCI (Recepção)
//
__interrupt void INT_SCI0_RX_ISR(void)
{
    uint16_t header[PROTOCOL_HEADER_SIZE];
    uint16_t cmd;

    SCI_readCharArray(SCI0_BASE, header, PROTOCOL_HEADER_SIZE);
    cmd = header[0];
    g_prot_header.data_len = header[1] | (header[2] << 8);
    g_prot_header.cmd = (cmd < CMD_COUNT)? (SCI_Command_e)cmd : CMD_NONE;

    Interrupt_clearACKGroup(INT_SCI0_RX_INTERRUPT_ACK_GROUP);
}
