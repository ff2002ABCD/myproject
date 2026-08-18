#ifndef _adc_H
#define _adc_H

#include "system.h"

void ADCx_Init(void);
u16 Get_ADC_Value(u8 ch,u8 times);
u16 Get_ADC_Once(u8 ch);//单次采集

#endif
