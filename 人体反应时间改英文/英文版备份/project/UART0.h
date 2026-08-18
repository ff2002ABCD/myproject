#ifndef UART0_H
#define UART0_H

#include "C8051F410X.H"

extern void uart0Rst();
extern void uart0Proc(); //1ms
extern void uart0TranSt(unsigned char *tdatap,unsigned char len);	//trans tdata[len]
extern void uart0RcvSt(unsigned char *rdatap,unsigned char len);	//receive tdata[len]

extern bit uart0TBusy,uart0RBusy;

#endif