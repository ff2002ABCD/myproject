//启动双路AD,启动时间1~2S,稳态时间32S

#ifndef ADCX2_H
#define ADCX2_H

#include "C8051F410X.H"
#include "ADCX.h"

extern unsigned int data adcx2Rs[4]; //4通道ADC结果

extern void adcx2Rst();
extern void adcx2St();
extern void adcx2End();
extern void adcx2();				//10ms

#endif
