#include "AC.h"
#include "tim.h"
#include "dac.h"
#include "math.h"
#include "stdio.h"
#define M_PI 3.1415926

AC_TYPE AC_type;
CURRENT_DIRECTION current_direction;
uint16_t dac_value;
float DC_value,AC_value;
uint8_t duty=50;
uint16_t dac_forward_max;
uint16_t dac_forward_min;
uint16_t dac_reverse_max;
uint16_t dac_reverse_min;
uint16_t VPP;
uint16_t direction_counter;
uint16_t sine_table[200];
uint16_t index;
uint16_t num=100;//²¨ÐÎ·Ö±æÂÊ

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
	if(htim->Instance==htim2.Instance)
	{
		switch(AC_type)
		{
			case sine:
				sin_handle();
				break;
			case triangle:
				triangle_handle();
				break;
			case square:
				square_handle();
				break;
		}
		HAL_DAC_SetValue(&hdac,DAC_CHANNEL_1,DAC_ALIGN_12B_R,dac_value);
	}
}

void GenerateSineTable(void) {
    for (int i = 0; i < num; i++) {
        sine_table[i] = (int16_t)(VPP/2*sin(2*M_PI*i/num));
    }
}

void sin_handle()
{
	if(current_direction==forward)
	{
		dac_value=(dac_forward_max+dac_forward_min)/2+sine_table[index];
		index = (index + 1) %num;
	}
	if(current_direction==reverse)
	{
		dac_value=(dac_reverse_max+dac_reverse_min)/2+sine_table[index];
		index = (index + 1) %num;
	}
}

void triangle_handle()
{
	if(current_direction==forward)
	{
		if(direction_counter<num/2) dac_value+=VPP/(num/2);
		else dac_value-=VPP/(num/2);
		direction_counter++;
		if(direction_counter==num) direction_counter=0;
	}
	if(current_direction==reverse)
	{
		if(direction_counter<num/2) dac_value+=VPP/(num/2);
		else dac_value-=VPP/(num/2);
		direction_counter++;
		if(direction_counter==num) direction_counter=0;
	}
}

void square_handle()
{
	if(current_direction==forward)
	{
		if(direction_counter<num*duty/100) dac_value=dac_forward_max;
		else dac_value=dac_forward_min;
		direction_counter++;
		if(direction_counter==num) direction_counter=0;
	}
	else if(current_direction==reverse)
	{
		if(direction_counter<num*duty/100) dac_value=dac_reverse_max;
		else dac_value=dac_reverse_min;
		direction_counter++;
		if(direction_counter==num) direction_counter=0;
	}
}

