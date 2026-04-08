#ifndef __CH376_H
#define __CH376_H
#include "stdint.h"
#include "CH376INC.H"

#define ERR_USB_UNKNOWN  0xFA
uint8_t file_writeData(char* buf);
uint8_t CH376_TestConnection(void);
void CH376_Init(void);
void xWriteCH376Cmd( unsigned char cmd );
void xWriteCH376Data( unsigned char dat );
unsigned char xReadCH376Data(void);
void xEndCH376Cmd(void);
unsigned char	Query376Interrupt( void );		/* 查询CH376中断(INT#引脚为低电平) */
void ch376_init();
void ch376_writetest();
#endif
