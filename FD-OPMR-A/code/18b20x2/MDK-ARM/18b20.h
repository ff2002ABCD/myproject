#ifndef __18B20_H
#define __18B20_H

#include "main.h"
#include "stdio.h"


uint8_t DS18B20_Init(void);
float DS18B20_Get_Temperature(void);
void DS18B20_SetLowResolution();
//void DS18B20_AsyncUpdate();
extern float current_temperature;
#endif
