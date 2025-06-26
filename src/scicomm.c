/*
 * scicomm.c
 *
 *  Created on: 13 de jun de 2025
 *      Author: Guilherme Márcio Soares
 */
#include "board.h"
#include "device.h"
#include "scicomm.h"

/*
int protocolReceiveInt(unsigned int sci_base)
{
    uint16_t buffer[INT_SIZE];
    SCI_readCharArray(sci_base, buffer, INT_SIZE);
    return (buffer[0] | (buffer[1] << 8U));
}

void protocolSendInt(unsigned int sci_base,int data)
{
    uint16_t txBuf[INT_SIZE];
    txBuf[0] = (uint16_t)(data & 0x00FF);
    txBuf[1] = (uint16_t)((data >> 8U) & 0x00FF);

    SCI_writeCharArray(sci_base, txBuf, INT_SIZE);
}
*/

void protocolReceiveVector(uint32_t base, int16_t *dest, uint16_t qtd)
{
    uint16_t i;
    for (i = 0; i < qtd; i++)
    {
        uint16_t lsb = SCI_readCharBlockingFIFO(base);
        uint16_t msb = SCI_readCharBlockingFIFO(base);
        dest[i] = (int16_t)((msb << 8) | lsb);
    }
}

void protocolSendVector(uint32_t base, int16_t *data, uint16_t qtd)
{
    for (uint16_t i = 0; i < qtd; i++)
    {
        SCI_writeCharBlockingFIFO(base, data[i] & 0xFF);       // LSB
        SCI_writeCharBlockingFIFO(base, (data[i] >> 8) & 0xFF); // MSB
    }
}

