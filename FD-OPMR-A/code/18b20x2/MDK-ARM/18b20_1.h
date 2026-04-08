#ifndef __18B20_1_H
#define __18B20_1_H

#include "main.h"
#include "stdio.h"


uint8_t DS18B20_Init_1(void);
float DS18B20_Get_Temperature_1(void);
void DS18B20_SetLowResolution_1();
//void DS18B20_AsyncUpdate();
extern float current_temperature_1;
#endif