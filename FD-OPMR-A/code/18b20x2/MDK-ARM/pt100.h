#ifndef __PT100_H
#define __PT100_H
#include "main.h"
float pt100_getTemperature();
void Start_ADC_Conversion(void);
float Convert_To_Voltage();
extern uint16_t pt100_adc;
extern float pt100_voltage,pt100_temp,pt100_res;
#endif
