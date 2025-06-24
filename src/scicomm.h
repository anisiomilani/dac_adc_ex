/*
 * scicomm.h
 *
 *  Created on: 13 de jun de 2025
 *      Author: Guilherme Márcio Soares
 */

#ifndef SRC_SCICOMM_H_
#define SRC_SCICOMM_H_


#define INT_SIZE 2U
#define PROTOCOL_HEADER_SIZE 3U

typedef enum
{
    CMD_NONE = 0,
    CMD_RECEIVE_INT,
    CMD_SEND_INT,
    CMD_RECEIVE_VECTOR = 3,
    CMD_SEND_VECTOR = 4,
    CMD_COUNT

} SCI_Command_e;

typedef struct
{
    SCI_Command_e cmd;
    uint16_t data_len;

} Protocol_Header_t;


int protocolReceiveInt(unsigned int sci_base);
void protocolSendInt(unsigned int sci_base,int data);
void protocolReceiveVector(uint32_t base, int16_t *dest, uint16_t qtd);
void protocolSendVector(uint32_t base, int16_t *data, uint16_t qtd);


#endif /* SRC_SCICOMM_H_ */
