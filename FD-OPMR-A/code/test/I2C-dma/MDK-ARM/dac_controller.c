#include "dac_controller.h"
#include "waveform_generator.h"
#include "i2c.h"

extern I2C_HandleTypeDef hi2c1;

uint16_t dac_buffer[2][WAVE_POINTS];
uint8_t active_buffer = 0;
uint8_t transfer_complete = 1;
uint32_t update_interval_us;

void dac_controller_init(void) {
    update_waveform_buffer(dac_buffer[0]);
    update_waveform_buffer(dac_buffer[1]);
    update_frequency(current_wave.frequency);
    
    transfer_complete = 1;
}

void update_frequency(uint16_t freq) {
    current_wave.frequency = freq;
    update_interval_us = 1000000 / (freq * WAVE_POINTS);
}


void dac_update_handler(void) {
	if(transfer_complete) {
		transfer_complete = 0;
		uint8_t next_buffer = !active_buffer;
		update_waveform_buffer(dac_buffer[next_buffer]);
		
		uint8_t data[3];
  uint16_t dac_value0 = 4047;  // 12-bit value (0-4095)
//	data[0]=0x40;
  data[0] = (dac_value0 >> 4); // Upper 4 bits
  data[1] = (dac_value0&0xF)<<4;         // Lower 8 bits
//		SCB_CleanDCache_by_Addr((uint32_t*)data, sizeof(data));
		HAL_I2C_Mem_Write_IT(&hi2c4, 0xC0, 0x40, I2C_MEMADD_SIZE_8BIT, data, 2);
//		HAL_I2C_Mem_Write(&hi2c4, 0x60<<1, 0x40, I2C_MEMADD_SIZE_8BIT, data, 2,HAL_MAX_DELAY);
//		HAL_I2C_Mem_Write_DMA(&hi2c4, 0x60<<1, 0x40, I2C_MEMADD_SIZE_8BIT, data, 2);
//		HAL_I2C_Master_Transmit(&hi2c4, 0x60 << 1, data,3,HAL_MAX_DELAY);
//		HAL_I2C_Master_Transmit_DMA(&hi2c4, 0x60 << 1, data,3);
	//	HAL_I2C_Mem_Write_DMA(&hi2c4, MCP4725_ADDR, CMD_WRITE_DAC,I2C_MEMADD_SIZE_8BIT, (uint8_t*)&dac_buffer[next_buffer][0], 2);
		active_buffer = next_buffer;
    }
}

//void HAL_I2C_MemTxCpltCallback(I2C_HandleTypeDef *hi2c) {
// 
//}

void HAL_I2C_MasterTxCpltCallback(I2C_HandleTypeDef *hi2c)
{
   if(hi2c == &hi2c4) {
        transfer_complete = 1;
    }
}

void HAL_I2C_MemTxCpltCallback(I2C_HandleTypeDef *hi2c) {
    if(hi2c->Instance == I2C4) {
   //    transfer_complete = 1;
//        HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);  // ?????
//        printf("DMA Transfer Complete!\n");
    }
}