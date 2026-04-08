#include "encoder.h"
#include "main.h"
#include "tim.h"
#include "menu.h"
#include "stdio.h"
#include "function.h"

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
//	
//		printf("转动方向:%d  脉冲数:%d \r\n",Diretion,Count);
	
//		if(Count-30000>=6)
//		{
//			for(int i=0;i<50;i++)
//			clockwise();
//			renew_menu();
//		}
//	if(Count-30000>=3)
//	{
//		for(int i=0;i<10;i++)
//		clockwise();
//		renew_menu();
//		TIM_ENCODER->CNT=30000;
//		Count=30000;
//	}
	if(Count-30000>=1) 
	{
//		printf("正转\r\n");
		clockwise();
	//	renew_menu();
		TIM_ENCODER->CNT=30000;
		Count=30000;
	}
//		else if(Count+6<=30000)
//		{
//			for(int i=0;i<50;i++)
//			counter_clockwise();
//			renew_menu();
//		}
//	if(Count+3<=30000)
//	{
//		for(int i=0;i<10;i++)
//		counter_clockwise();
//	//	renew_menu();
//		TIM_ENCODER->CNT=30000;
//		Count=30000;
//	}
	if(Count+1<=30000)
	{
//		printf("反转\r\n");
		counter_clockwise();
	//	renew_menu();
		TIM_ENCODER->CNT=30000;
		Count=30000;
	}
	
}

void clockwise()
{
	//right_button();
	switch(page)
	{
		default:break;
		case QUERY_JOURNEY:
		{	
			if(count[index_save-1]>0)
			{
				if(x_offset_journey+x_offset_move>=0) x_offset_journey=0;
				else 
					x_offset_journey+=x_offset_move;
				
			}
			else
			{
				if((x_offset_journey+x_offset_move)>=-count[index_save-1]/xgrid_multiple_journey[xgrid_multiple_journey_index])
					x_offset_journey=-count[index_save-1]/xgrid_multiple_journey[xgrid_multiple_journey_index];
				else 
				{
					x_offset_journey+=x_offset_move;
				}
			}
			
			renew_screen_flag=1;
		}break;
		case QUERY_ANGLE:
		{
			x_offset_angle+=x_offset_move;
			renew_screen_flag=1;
		}break;
		case QUERY_TIME:
		{
			if(index_save_time<query_grid) return;
			if(x_offset_time+x_offset_move<index_save_time-query_grid-1)
			x_offset_time+=x_offset_move;
			else x_offset_time=index_save_time-query_grid-1;
			renew_screen_flag=1;
		}break;
	}
}

void counter_clockwise()
{
	//left_button();
	switch(page)
	{
		default:break;
		case QUERY_JOURNEY:
		{	
			if(count[index_save-1]>0)
			{
				if((x_offset_journey-x_offset_move)<=-count[index_save-1]/xgrid_multiple_journey[xgrid_multiple_journey_index])
					x_offset_journey=-count[index_save-1]/xgrid_multiple_journey[xgrid_multiple_journey_index];
				else 
				{
					x_offset_journey-=x_offset_move;
				}
			}
			else
			{
				if(x_offset_journey-x_offset_move<=0) x_offset_journey=0;
				else 
					x_offset_journey-=x_offset_move;
			}
			renew_screen_flag=1;
		}break;
		
		case QUERY_ANGLE:
		{
			x_offset_angle-=x_offset_move;
			renew_screen_flag=1;
			
		}break;
		case QUERY_TIME:
		{
			if(x_offset_time>=x_offset_move)
			x_offset_time-=x_offset_move;
			else x_offset_time=0;
			renew_screen_flag=1;
		}break;
	}
}
