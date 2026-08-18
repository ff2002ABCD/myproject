#ifndef __DS18B20_1_H
#define __DS18B20_1_H

#include "main.h"
#include "stdio.h"


uint8_t DS18B20_Init_1(void);
short DS18B20_Get_Temperature_1(void);
uint8_t DS18B20_Init_2(void);
short DS18B20_Get_Temperature_2(void);
uint8_t DS18B20_Init_3(void);
short DS18B20_Get_Temperature_3(void);
uint8_t DS18B20_Init_4(void);
short DS18B20_Get_Temperature_4(void);
extern void delay_us(uint32_t time);

#endif
