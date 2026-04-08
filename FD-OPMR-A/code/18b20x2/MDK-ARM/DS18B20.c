#include "delay.h"
#include "DS18B20.h"

//void DS18B20_Init(void) {
//    GPIO_InitTypeDef GPIO_InitStruct = {0};
//    
//    __HAL_RCC_GPIOA_CLK_ENABLE();
//			
//    GPIO_InitStruct.Pin = DS18B20_PIN;
//    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_OD;
//    GPIO_InitStruct.Pull = GPIO_PULLUP;
//    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
//    HAL_GPIO_Init(DS18B20_PORT, &GPIO_InitStruct);
//    
//    HAL_GPIO_WritePin(DS18B20_PORT, DS18B20_PIN, GPIO_PIN_SET);
//}

//uint8_t DS18B20_Reset(void) {
//    uint8_t presence = 0;
//    
//    // ??480-960µs
//    HAL_GPIO_WritePin(DS18B20_PORT, DS18B20_PIN, GPIO_PIN_RESET);
//    delay_us(480);
//    
//    // ????
//    HAL_GPIO_WritePin(DS18B20_PORT, DS18B20_PIN, GPIO_PIN_SET);
//    delay_us(60);
//    
//    // ??????
//    if (!HAL_GPIO_ReadPin(DS18B20_PORT, DS18B20_PIN)) {
//        presence = 1;  // ????
//    }
//    
//    delay_us(420);
//    return presence;
//}

//// ???bit
//void DS18B20_WriteBit(uint8_t bit) {
//    if (bit) {
//        // ?1
//        HAL_GPIO_WritePin(DS18B20_PORT, DS18B20_PIN, GPIO_PIN_RESET);
//        delay_us(6);
//        HAL_GPIO_WritePin(DS18B20_PORT, DS18B20_PIN, GPIO_PIN_SET);
//        delay_us(64);
//    } else {
//        // ?0
//        HAL_GPIO_WritePin(DS18B20_PORT, DS18B20_PIN, GPIO_PIN_RESET);
//        delay_us(60);
//        HAL_GPIO_WritePin(DS18B20_PORT, DS18B20_PIN, GPIO_PIN_SET);
//        delay_us(10);
//    }
//}

//// ?????
//void DS18B20_WriteByte(uint8_t byte) {
//    for (uint8_t i = 0; i < 8; i++) {
//        DS18B20_WriteBit(byte & 0x01);
//        byte >>= 1;
//    }
//}

//// ???bit
//uint8_t DS18B20_ReadBit(void) {
//    uint8_t bit = 0;
//    
//    HAL_GPIO_WritePin(DS18B20_PORT, DS18B20_PIN, GPIO_PIN_RESET);
//    delay_us(6);
//    HAL_GPIO_WritePin(DS18B20_PORT, DS18B20_PIN, GPIO_PIN_SET);
//    delay_us(9);
//    
//    if (HAL_GPIO_ReadPin(DS18B20_PORT, DS18B20_PIN)) {
//        bit = 1;
//    }
//    
//    delay_us(55);
//    return bit;
//}

//// ?????
//uint8_t DS18B20_ReadByte(void) {
//    uint8_t byte = 0;
//    
//    for (uint8_t i = 0; i < 8; i++) {
//        byte >>= 1;
//        if (DS18B20_ReadBit()) {
//            byte |= 0x80;
//        }
//    }
//    
//    return byte;
//}

//float DS18B20_ReadTemp(void) {
//    uint8_t temp_l, temp_h;
//    int16_t temp;
//    float temperature;
//    
//    DS18B20_Reset();
//    DS18B20_WriteByte(0xCC);  // ??ROM
//    DS18B20_WriteByte(0x44);  // ??????
//    
//    delay_ms(750);  // ??????
//    
//    DS18B20_Reset();
//    DS18B20_WriteByte(0xCC);  // ??ROM
//    DS18B20_WriteByte(0xBE);  // ?????
//    
//    temp_l = DS18B20_ReadByte();  // ?????
//    temp_h = DS18B20_ReadByte();  // ?????
//    
//    temp = (temp_h << 8) | temp_l;
//    temperature = temp * 0.0625;  // ???????
//    
//    return temperature;
//}

