#include "encoder.h"
#include "main.h"
#include "tim.h"
#include "menu.h"
#include "stdio.h"

extern int fputc(int ch, FILE* file);

uint16_t Count=10000,last_Count=10000;
uint16_t Diretion=0;

void encoder_init()
{
	HAL_TIM_Encoder_Start(&htim_encoder,TIM_CHANNEL_ALL);
	__HAL_TIM_SetCounter(&htim_encoder,30000);
}

void get_encoder()
{
	Diretion =  __HAL_TIM_IS_TIM_COUNTING_DOWN(&htim_encoder);     
	Count = __HAL_TIM_GET_COUNTER(&htim_encoder);
	
//		printf("转动方向:%d  脉冲数:%d \r\n",Diretion,Count);
	
//		if(Count-30000>=6)
//		{
//			for(int i=0;i<50;i++)
//			clockwise();
//			renew_menu();
//		}
	if(Count-30000>=3)
	{
		for(int i=0;i<10;i++)
		clockwise();
		renew_menu();
	}
	else if(Count-30000>=1) 
	{
//		printf("正转\r\n");
		clockwise();
		renew_menu();
	}
//		else if(Count+6<=30000)
//		{
//			for(int i=0;i<50;i++)
//			counter_clockwise();
//			renew_menu();
//		}
	else if(Count+3<=30000)
	{
		for(int i=0;i<10;i++)
		counter_clockwise();
		renew_menu();
	}
	else if(Count+1<=30000)
	{
//		printf("反转\r\n");
		counter_clockwise();
		renew_menu();
	}
	TIM_ENCODER->CNT=30000;
}

void clockwise()
{
	right_button();
}

void counter_clockwise()
{
	left_button();
}
