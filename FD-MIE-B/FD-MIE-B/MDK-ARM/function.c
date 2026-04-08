#include "function.h"
#include "string.h"
#include "stdio.h"
#include "usart.h"
#include "string.h"
#include "tim.h"
#include "gui.h"
#include "menu.h"

#define COORDINATE_BUFFER_SIZE 256 


uint8_t dma_tx_buffer[COORDINATE_BUFFER_SIZE];
volatile uint8_t dma_busy = 0;
_Bool renew_screen_flag=0;//刷新曲线


//动镜行程
int32_t count[MAX_NUM_JOURNEY];
int16_t voltage[MAX_NUM_JOURNEY];
uint32_t index_send,index_save;
int32_t round_now;
char *xgrid_txt_journey[]={"10μm","5μm","2μm","1μm","500nm","250nm"};
char *ygrid_txt_journey[]={"1mW","500μW","200μW","100μW","50μW","20μW"};
uint16_t xgrid_multiple_journey[]={40,20,8,4,2,1};
uint8_t xgrid_multiple_journey_index;
uint16_t ygrid_multiple_journey[]={1,2,5,10,20,50};
uint8_t ygrid_multiple_journey_index;
int32_t x_offset_journey=0;
_Bool measure_journey_state=0;
int32_t count_max,count_min;

//角度
int32_t angle[MAX_NUM_ANGLE];
int16_t voltage_angle[MAX_NUM_ANGLE];
uint32_t index_send_angle,index_save_angle;
int32_t round_now_angle;
char *xgrid_txt_angle[]={"360°","180°","90°","45°","18°","9°","4.5°","2.25°"};
char *ygrid_txt_angle[]={"1mW","500μW","200μW","100μW","50μW","20μW"};
uint16_t xgrid_multiple_angle[]={160,80,40,16,8,4,2,1};
uint8_t xgrid_multiple_angle_index=7;
uint16_t ygrid_multiple_angle[]={1,2,5,10,20,50};
uint8_t ygrid_multiple_angle_index;
int32_t x_offset_angle;
_Bool measure_angle_state=0;
int32_t angle_max,angle_min;

//时间
uint16_t sample_interval=10;
int32_t time[MAX_NUM_TIME];
int16_t voltage_time[MAX_NUM_TIME];
uint32_t index_send_time,index_save_time;
//char *xgrid_txt_time[]={"1000s","500s","200s","100s","50s","20s","10s","5s"};
char *ygrid_txt_time[]={"1mW","500μW","200μW","100μW","50μW","20μW"};
uint16_t xgrid_multiple_time[]={100,40,20,10,4,2,1};
uint8_t xgrid_multiple_time_index=6;
uint16_t ygrid_multiple_time[]={1,2,5,10,20,50};
uint8_t ygrid_multiple_time_index;
int32_t x_offset_time=0;
_Bool measure_time_state=0;

void save_data()
{	

	count[index_save]=current_count-30000+2000*round_now;
	voltage[index_save]=adc_value-adc_value_setzero-32768;
	if(index_save<MAX_NUM_JOURNEY-1)
	index_save++;
//	if(index_save==MAX_NUM_JOURNEY) index_save=0;
}	

void save_angle()
{	

	angle[index_save_angle]=current_angle-30000+2000*round_now_angle;
	voltage_angle[index_save_angle]=adc_value-adc_value_setzero-32768;	
	if(index_save_angle<MAX_NUM_ANGLE-1) 
		index_save_angle++;
	//if(index_save_angle==MAX_NUM_ANGLE) index_save_angle=0;
}	

void save_time()
{
	time[index_save_time]=current_time;
	voltage_time[index_save_time]=adc_value-adc_value_setzero-32768;
	if(index_save_time<MAX_NUM_TIME-1)
	index_save_time++;
//	if(index_save_time==MAX_NUM_TIME) index_save_time=0;
}

void Send_Coordinate_I32_I16(int32_t x, int16_t y)
{
    uint8_t buffer[7];  
    
    buffer[0] = x & 0xFF;         
    buffer[1] = (x >> 8) & 0xFF;  
    buffer[2] = (x >> 16) & 0xFF; 
    buffer[3] = (x >> 24) & 0xFF; 
    buffer[4] = y & 0xFF;        
    buffer[5] = (y >> 8) & 0xFF;
	
		switch(page)
		{
			default:break;
			case MEA_JOURNEY:buffer[6] = 0x0A; break;
			case MEA_ANGLE:buffer[6] = 0x0B;break;
			case MEA_TIME:buffer[6]=0x0C;break;				
		}
		
		
    
    HAL_UART_Transmit(&huart1, buffer, 7, HAL_MAX_DELAY);
}


void Send_Coordinates_I32_I16(int32_t *x_values, int16_t *y_values, uint16_t count)
{
		switch(page)
		{
			default:break;
			case MEA_JOURNEY:
			{
				for(uint16_t i = 0; i < count; i++) 
				{
					Send_Coordinate_I32_I16(x_values[index_send], y_values[index_send]);
					index_send++;
					if(index_send==MAX_NUM_JOURNEY) index_send--;
					HAL_Delay(1); 
				}
			}break;			
			case MEA_ANGLE:
			{
				for(uint16_t i = 0; i < count; i++) 
				{
					Send_Coordinate_I32_I16(x_values[index_send_angle], y_values[index_send_angle]);
					index_send_angle++;
					if(index_send_angle==MAX_NUM_ANGLE) index_send_angle--;
					HAL_Delay(1); 
				}
			}break;
			case MEA_TIME:
			{
				for(uint16_t i = 0; i < count; i++) 
				{
					Send_Coordinate_I32_I16(x_values[index_send_time], y_values[index_send_time]);
					index_send_time++;
					if(index_send_time==MAX_NUM_TIME) index_send_time--;
					HAL_Delay(1); 
				}
			}break;			
		} 
}

void journey_data_clear()
{
	HAL_TIM_Base_Stop(&htim_journey_process);
	HAL_TIM_Base_Stop(&htim_journey_encoder);
	current_count=30000;
	last_count=30000;
	TIM_JOURNEY_ENCODER->CNT=30000;
	memset(count,0,sizeof(count));
	memset(voltage,0,sizeof(voltage));
	index_send=0,index_save=0;
	round_now=0;
	mea_state=MEA_STOP;
	printf("start.txt=\"开始\"\xff\xff\xff");
}

void time_data_clear()
{
	HAL_TIM_Base_Stop(&htim_time_process);
	TIM_TIME_PROCESS->CNT=0;
	current_time=0;
	memset(time,0,sizeof(time));
	memset(voltage_time,0,sizeof(voltage_time));
	index_save_time=0;
	index_send_time=0;
	mea_state=MEA_STOP;
	printf("start.txt=\"开始\"\xff\xff\xff");
	printf("cle 1,0\xff\xff\xff");
}

void measure_journey_start()
{
	current_count=30000;
	last_count=30000;
	TIM_JOURNEY_ENCODER->CNT=30000;
	memset(count,0,sizeof(count));
	memset(voltage,0,sizeof(voltage));
	index_send=0,index_save=0;
	round_now=0;
	mea_state=MEA_START;
	HAL_TIM_Base_Start_IT(&htim_journey_process);
	HAL_TIM_Base_Start(&htim_journey_encoder);
	printf("start.txt=\"暂停\"\xff\xff\xff");
}

void measure_journey_pause()
{
	HAL_TIM_Base_Stop(&htim_journey_process);
	HAL_TIM_Base_Stop(&htim_journey_encoder);
	mea_state=MEA_PAUSE;
	printf("start.txt=\"继续\"\xff\xff\xff");
}

void measure_journey_continue()
{
	HAL_TIM_Base_Start_IT(&htim_journey_process);
	HAL_TIM_Base_Start(&htim_journey_encoder);
	mea_state=MEA_START;
	printf("start.txt=\"暂停\"\xff\xff\xff");
}

void angle_data_clear()
{
	HAL_TIM_Base_Stop(&htim_angle_process);
	HAL_TIM_Base_Stop(&htim_angle_encoder);
	current_angle=30000;
	last_angle=30000;
	TIM_ANGLE_ENCODER->CNT=30000;
	memset(angle,0,sizeof(angle));
	memset(voltage_angle,0,sizeof(voltage_angle));
	index_send_angle=0,index_save_angle=0;
	round_now_angle=0;
	mea_state=MEA_STOP;
	printf("start.txt=\"开始\"\xff\xff\xff");
}

void measure_angle_start()
{
	current_angle=30000;
	last_angle=30000;
	TIM_ANGLE_ENCODER->CNT=30000;
	memset(angle,0,sizeof(angle));
	memset(voltage_angle,0,sizeof(voltage_angle));
	index_send_angle=0,index_save_angle=0;
	round_now_angle=0;
	mea_state=MEA_START;
	HAL_TIM_Base_Start_IT(&htim_angle_process);
	HAL_TIM_Base_Start(&htim_angle_encoder);
	printf("start.txt=\"暂停\"\xff\xff\xff");
}

void measure_angle_pause()
{
	HAL_TIM_Base_Stop_IT(&htim_angle_process);
	HAL_TIM_Base_Stop(&htim_angle_encoder);
	measure_angle_state=MEA_PAUSE;
	printf("start.txt=\"继续\"\xff\xff\xff");
}

void measure_angle_continue()
{
	HAL_TIM_Base_Start_IT(&htim_angle_process);
	HAL_TIM_Base_Start(&htim_angle_encoder);
	mea_state=MEA_START;
	printf("start.txt=\"暂停\"\xff\xff\xff");
}

void measure_time_start()
{
	current_time=0;
	memset(time,0,sizeof(time));
	memset(voltage_time,0,sizeof(voltage_time));
	index_save_time=0;
	index_send_time=0;
	TIM_TIME_PROCESS->CNT=0;
	HAL_TIM_Base_Start_IT(&htim_time_process);
	mea_state=MEA_START;
	printf("start.txt=\"暂停\"\xff\xff\xff");
}

void measure_time_pause()
{
	HAL_TIM_Base_Stop_IT(&htim_time_process);
	mea_state=MEA_PAUSE;
	printf("start.txt=\"继续\"\xff\xff\xff");
}

void measure_time_continue()
{
	HAL_TIM_Base_Start_IT(&htim_time_process);
	mea_state=MEA_START;
	printf("start.txt=\"暂停\"\xff\xff\xff");
}

void find_min_max(int32_t arr[], size_t size, int32_t *min, int32_t *max) {
    if (size == 0) {
        *min = 0;
        *max = 0;
        return;
    }
    
    if (size == 1) {
        *min = arr[0];
        *max = arr[0];
        return;
    }
    
    if (arr[0] > arr[1]) {
        *max = arr[0];
        *min = arr[1];
    } else {
        *max = arr[1];
        *min = arr[0];
    }
    
    for (size_t i = 2; i < size - 1; i += 2) {
        if (arr[i] > arr[i + 1]) {
            if (arr[i] > *max) *max = arr[i];
            if (arr[i + 1] < *min) *min = arr[i + 1];
        } else {
            if (arr[i + 1] > *max) *max = arr[i + 1];
            if (arr[i] < *min) *min = arr[i];
        }
    }
    
    if (size % 2 == 1) {
        if (arr[size - 1] > *max) *max = arr[size - 1];
        if (arr[size - 1] < *min) *min = arr[size - 1];
    }
}
//void CH376_SetBaudRate(uint32_t new_baudrate) {
//    uint8_t cmd[4];
//    huart1.Init.BaudRate = 9600;
//    if (HAL_UART_Init(&huart1) != HAL_OK) {
//        Error_Handler();
//    }
//    cmd[0] = 0x02;
//    cmd[1] = 0x03;  
//    cmd[2] = 0xCC;   
//    cmd[3] = 0x00;  
//  
//    HAL_UART_Transmit(&huart2, cmd, sizeof(cmd), HAL_MAX_DELAY);
//    
//    HAL_Delay(10);
//    
//    huart2.Init.BaudRate = new_baudrate;
//    if (HAL_UART_Init(&huart2) != HAL_OK) {
//        Error_Handler();
//    }
//}

