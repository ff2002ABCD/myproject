#include "function.h"
#include "string.h"
#include "stdio.h"
#include "usart.h"

#define COORDINATE_BUFFER_SIZE 256 

uint8_t dma_tx_buffer[COORDINATE_BUFFER_SIZE];
volatile uint8_t dma_busy = 0;
uint16_t count[MAX_NUM];
uint16_t voltage[MAX_NUM];
uint32_t index_send,index_save;

void save_data()
{	

	count[index_save]=current_count;
	voltage[index_save]=adc_value;
	index_save++;
	if(index_save==MAX_NUM) index_save=0;
}	

void Send_Coordinate_U16(uint16_t x, uint16_t y)
{
    uint8_t buffer[4];
    if(x==0&&y==0) return;

    buffer[0] = x & 0xFF;        
    buffer[1] = (x >> 8) & 0xFF; 
    buffer[2] = y & 0xFF;        
    buffer[3] = (y >> 8) & 0xFF; 
    
    HAL_UART_Transmit(&huart1, buffer, 4, HAL_MAX_DELAY);
}

void Send_Coordinates_U16(uint16_t *x_values, uint16_t *y_values, int count)
{
    for(int i = 0; i < count; i++) {
        Send_Coordinate_U16(x_values[index_send], y_values[index_send]);
			index_send++;
				if(index_send==MAX_NUM) index_send=0;
        HAL_Delay(1); 
    }
}