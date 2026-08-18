//启动单路AD,通道0～3对应P2.3~P2.6

#ifndef ADCX_H
#define ADCX_H

#include "C8051F410X.H"

#define ADCXBUSY AD0BUSY

extern void adcxRst();
extern void adcxSt(unsigned char i);  //通道0~3
extern void adcxCopy(unsigned int * datapc);

#endif
