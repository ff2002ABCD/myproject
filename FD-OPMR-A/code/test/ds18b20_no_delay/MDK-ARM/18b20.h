#ifndef __18B20_H
#define __18B20_H

#include "main.h"
#include "stdio.h"
#define DS18B20_CMD_SKIP_ROM        0xCC
#define DS18B20_CMD_CONVERT_T       0x44
#define DS18B20_CMD_READ_SCRATCH    0xBE

extern float current_temperature;
typedef enum {
    DS18B20_STATE_INIT,
    DS18B20_STATE_ROM_CMD,
    DS18B20_STATE_CONVERT,
    DS18B20_STATE_WAIT_CONVERSION,
    DS18B20_STATE_READ_SCRATCH,
    DS18B20_STATE_DONE,
    DS18B20_STATE_ERROR
} DS18B20_State;

typedef struct {
    GPIO_TypeDef* GPIOx;
    uint16_t GPIO_Pin;
    DS18B20_State state;
    uint32_t conversion_start_time;
    uint8_t retry_count;
    float temperature;
} DS18B20_HandleTypeDef;

void _18B20_Init(DS18B20_HandleTypeDef* hds, GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin);
void DS18B20_StateMachine(DS18B20_HandleTypeDef* hds);
float DS18B20_GetTemperature(DS18B20_HandleTypeDef* hds);

#endif
