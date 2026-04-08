#include "18b20.h"
#include "delay.h"

static void set_bus_output(DS18B20_HandleTypeDef* hds) {
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Pin = hds->GPIO_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_OD;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(hds->GPIOx, &GPIO_InitStruct);
}

static void set_bus_input(DS18B20_HandleTypeDef* hds) {
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Pin = hds->GPIO_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(hds->GPIOx, &GPIO_InitStruct);
}

static uint8_t onewire_reset(DS18B20_HandleTypeDef* hds) {
    uint8_t presence = 0;
    set_bus_output(hds);
    
    // ????480us
    HAL_GPIO_WritePin(hds->GPIOx, hds->GPIO_Pin, GPIO_PIN_RESET);
    delay_us(480);
    
    set_bus_input(hds);
    delay_us(70);    // ??15-60us???????
    
    if (!HAL_GPIO_ReadPin(hds->GPIOx, hds->GPIO_Pin)) {
        presence = 1;
    }
    
    delay_us(410);   // ??480us + 70 + 410 = 960us
    return presence;
}

static void onewire_write_bit(DS18B20_HandleTypeDef* hds, uint8_t bit) {
    set_bus_output(hds);
    HAL_GPIO_WritePin(hds->GPIOx, hds->GPIO_Pin, GPIO_PIN_RESET);
    delay_us(bit ? 1 : 60);
    set_bus_input(hds);
    if(bit) delay_us(60);
}

static uint8_t onewire_read_bit(DS18B20_HandleTypeDef* hds) {
    uint8_t bit = 0;
    set_bus_output(hds);
    HAL_GPIO_WritePin(hds->GPIOx, hds->GPIO_Pin, GPIO_PIN_RESET);
    delay_us(1);
    set_bus_input(hds);
    delay_us(14);
    bit = HAL_GPIO_ReadPin(hds->GPIOx, hds->GPIO_Pin);
    delay_us(45);
    return bit;
}
void _18B20_Init(DS18B20_HandleTypeDef* hds, GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin) {
    hds->GPIOx = GPIOx;
    hds->GPIO_Pin = GPIO_Pin;
    hds->state = DS18B20_STATE_INIT;
    hds->retry_count = 0;
}

// ??????
void DS18B20_StateMachine(DS18B20_HandleTypeDef* hds) {
    static uint8_t data[9];
    
    switch(hds->state) {
        case DS18B20_STATE_INIT:
            if(onewire_reset(hds)) {
                hds->state = DS18B20_STATE_ROM_CMD;
                hds->retry_count = 0;
            } else {
                if(++hds->retry_count > 3) {
                    hds->state = DS18B20_STATE_ERROR;
                }
            }
            break;
            
        case DS18B20_STATE_ROM_CMD:
            onewire_write_bit(hds, DS18B20_CMD_SKIP_ROM);
            hds->state = DS18B20_STATE_CONVERT;
            break;
            
        case DS18B20_STATE_CONVERT:
            onewire_write_bit(hds, DS18B20_CMD_CONVERT_T);
            hds->conversion_start_time = HAL_GetTick();
            hds->state = DS18B20_STATE_WAIT_CONVERSION;
            break;
            
        case DS18B20_STATE_WAIT_CONVERSION:
//            if(HAL_GetTick() - hds->conversion_start_time >= 750) { // 750ms for 12-bit
							delay_us(750);
                hds->state = DS18B20_STATE_READ_SCRATCH;
//            }
            break;
            
        case DS18B20_STATE_READ_SCRATCH:
            onewire_reset(hds);
            onewire_write_bit(hds, DS18B20_CMD_READ_SCRATCH);
            for(int i=0; i<9; i++) {
                data[i] = 0;
                for(int j=0; j<8; j++) {
                    data[i] |= (onewire_read_bit(hds) << j);
                }
            }
            // CRC??(??,?????CRC8??)
            if(data[8] == 0) { // ???CRC??
                int16_t raw = (data[1] << 8) | data[0];
                hds->temperature = raw * 0.0625f;
                hds->state = DS18B20_STATE_DONE;
            } else {
                hds->state = DS18B20_STATE_ERROR;
            }
            break;
            
        case DS18B20_STATE_DONE:
            // ????
            break;
            
        case DS18B20_STATE_ERROR:
            // ????
            delay_ms(100);
            hds->state = DS18B20_STATE_INIT;
            break;
    }
}

float DS18B20_GetTemperature(DS18B20_HandleTypeDef* hds) {
    return hds->temperature;
}