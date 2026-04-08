#include "main.h"
#include "dac.h"
#include "adc.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"
#include "stdio.h"
#include "osc.h"
#include "stdlib.h"
#include "control.h"
#include "measure.h"
#include "menu.h"
#include "flash.h"

int button_counter;
void right_button()
{
	switch(caliboration_mode)
	{
		case 0:break;
		case 1:
		{
//			if(calibo_ch==1)
//			{
//				calibo_ch=2;
//				printf("t24.txt=\"选通道：2\"\xFF\xFF\xFF");
//				printf("vis t29,0\xFF\xFF\xFF");
//				printf("vis t30,1\xFF\xFF\xFF");
//				CH1_enable=0;
//				CH2_enable=1;
//				printf("cle 1,255\xFF\xFF\xFF");
//			}	
//			
//			else
//			{
//				calibo_ch=1;
//				printf("t24.txt=\"选通道：1\"\xFF\xFF\xFF");
//				printf("vis t29,1\xFF\xFF\xFF");
//				printf("vis t30,0\xFF\xFF\xFF");
//				CH1_enable=1;
//				CH2_enable=0;
//				printf("cle 1,255\xFF\xFF\xFF");
//			}
		}break;
		case 2:
		{
			if(calibo_ch==1)
			{
				del_zero_ch1+=calibo_step_zero;
			}
			else
			{
				del_zero_ch2+=calibo_step_zero;
			}
		}break;
		case 3:
		{
			if(calibo_ch==1)
			{
				del_k_ch1+=calibo_step_k;
			}
			else
			{
				del_k_ch2+=calibo_step_k;
			}
		}break;
		case 4:
		{
			if(calibo_ch==1)
			{
				del_k_ch1-=calibo_step_k;
			}
			else
			{
				del_k_ch2-=calibo_step_k;
			}
		}break;
	}
	if(caliboration_mode!=0) return;
	if(cursor_status==1)
	{
		switch(cursor_mode)
		{
			case 1:
			{
				if(cursor_num==0)
				{
					cursor_num=1;
					
					printf("t24.txt=\"电压：2\"\xFF\xFF\xFF");
				}
				else
				{
					cursor_num=0;
					printf("t24.txt=\"电压：1\"\xFF\xFF\xFF");
				}
			}break;
//			case 2:
//			{
//				if(xy_enable==1)
//				{
//					if(cursor_num==0&&x1<650)
//					{
//						//printf("t24.txt=\"选中：纵1\"\xFF\xFF\xFF");
//						printf("move t16,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1+step);
//						printf("move t22,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1+step);
//						x1+=step;
//					}
//					else if(cursor_num==1&&x2<650)
//					{
//						//printf("t24.txt=\"选中：纵2\"\xFF\xFF\xFF");
//						printf("move t17,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2+step);
//						printf("move t23,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2+step);
//						x2+=step;
//					}
//					break;
//				}
//				if(cursor_num==0)
//				{
//					cursor_num=1;
//					printf("t24.txt=\"CH2电压：2\"\xFF\xFF\xFF");
//				}
//				else
//				{
//					cursor_num=0;
//					printf("t24.txt=\"CH2电压：1\"\xFF\xFF\xFF");
//				}
//			}break;
			case 3:
			{
				if(cursor_num==0&&x1<650)
				{
					//printf("t24.txt=\"选中：纵1\"\xFF\xFF\xFF");
					printf("move t16,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1+step);
					printf("move t22,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1+step);
					x1+=step;
				}
				else if(cursor_num==1&&x2<650)
				{
					//printf("t24.txt=\"选中：纵2\"\xFF\xFF\xFF");
					printf("move t17,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2+step);
					printf("move t23,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2+step);
					x2+=step;
				}
			}break;
		}
		return;
	}
	switch(menu2_status)
	{
		case 1:
		{
			if(cursor_switch==1)
			{
				printf("vis t16,0\xFF\xFF\xFF");
				printf("vis t17,0\xFF\xFF\xFF");
				printf("vis t18,0\xFF\xFF\xFF");
				printf("vis t19,0\xFF\xFF\xFF");
				printf("vis t20,0\xFF\xFF\xFF");
				printf("vis t21,0\xFF\xFF\xFF");
				printf("vis t22,0\xFF\xFF\xFF");
				printf("vis t23,0\xFF\xFF\xFF");
				
				//printf("vis t24,0\xFF\xFF\xFF");
				printf("t58.txt=\"->光标关\"\xff\xff\xff");
				cursor_switch=0;
				
			}
			else if(cursor_switch==0)
			{
				cursor_switch=1;
				printf("t58.txt=\"->光标开\"\xff\xff\xff");
				switch(cursor_mode)
				{
					case 1:
					{
						printf("vis t18,1\xFF\xFF\xFF");
						printf("vis t19,1\xFF\xFF\xFF");
						printf("vis t20,1\xFF\xFF\xFF");
						printf("vis t21,1\xFF\xFF\xFF");
					}break;
					case 2:
					{
						printf("vis t18,1\xFF\xFF\xFF");
						printf("vis t19,1\xFF\xFF\xFF");
						printf("vis t20,1\xFF\xFF\xFF");
						printf("vis t21,1\xFF\xFF\xFF");
					}break;
					case 3:
					{
						printf("vis t16,1\xFF\xFF\xFF");
						printf("vis t17,1\xFF\xFF\xFF");
						printf("vis t22,1\xFF\xFF\xFF");
						printf("vis t23,1\xFF\xFF\xFF");
					}break;
				}
			}
		}break;
		//光标模式
		case 2:
		{
			printf("vis t45,0\xFF\xFF\xFF");
			printf("vis t46,0\xFF\xFF\xFF");
			printf("vis t49,0\xFF\xFF\xFF");
			printf("vis t57,0\xFF\xFF\xFF");
			printf("vis t24,1\xFF\xFF\xFF");
			cursor_switch=1;
			cursor_status=1;//光标模式开标志
			printf("t58.txt=\"光标开\"\xff\xff\xff");
			printf("vis t18,0\xFF\xFF\xFF");
			printf("vis t19,0\xFF\xFF\xFF");
			printf("vis t20,0\xFF\xFF\xFF");
			printf("vis t21,0\xFF\xFF\xFF");
			printf("vis t16,0\xFF\xFF\xFF");
			printf("vis t17,0\xFF\xFF\xFF");
			printf("vis t22,0\xFF\xFF\xFF");
			printf("vis t23,0\xFF\xFF\xFF");
			if(xy_enable==1)
			{
				if(cursor_mode==3) cursor_mode=1;
			}
			
			//刷新左上角菜单
			switch(cursor_mode)
			{
				case 0:break;
				case 1:
				{
					if(cursor_num==0) printf("t24.txt=\"电压：1\"\xff\xff\xff");
					else printf("t24.txt=\"电压：2\"\xff\xff\xff");
				}break;
//				case 2:
//				{
//					if(cursor_num==0) printf("t24.txt=\"CH2电压：1\"\xff\xff\xff");
//					else printf("t24.txt=\"CH2电压：2\"\xff\xff\xff");
//				}break;
				case 3:
				{
					if(fft_enable==0)
					{
						if(cursor_num==0) printf("t24.txt=\"时间：1\"\xff\xff\xff");
						else printf("t24.txt=\"时间：2\"\xff\xff\xff");
					}
					else
					{
						if(cursor_num==0) printf("t24.txt=\"频率：1\"\xff\xff\xff");
						else printf("t24.txt=\"频率：2\"\xff\xff\xff");
					}
				}break;
			}
			//修改下方参数
			switch(cursor_mode)
			{
				case 1:
				{
					printf("vis t18,1\xFF\xFF\xFF");
					printf("vis t19,1\xFF\xFF\xFF");
					printf("vis t20,1\xFF\xFF\xFF");
					printf("vis t21,1\xFF\xFF\xFF");
				}break;
				case 2:
				{
					printf("vis t18,1\xFF\7\xFF");
					printf("vis t19,1\xFF\xFF\xFF");
					printf("vis t20,1\xFF\xFF\xFF");
					printf("vis t21,1\xFF\xFF\xFF");
				}break;
				case 3:
				{
					printf("vis t16,1\xFF\xFF\xFF");
					printf("vis t17,1\xFF\xFF\xFF");
					printf("vis t22,1\xFF\xFF\xFF");
					printf("vis t23,1\xFF\xFF\xFF");
				}break;
			}
			switch_parament(0);
		}break;
						
		case 3:
		{
			caliboration_mode=2;
			printf("vis t45,0\xFF\xFF\xFF");
			printf("vis t46,0\xFF\xFF\xFF");
			printf("vis t49,0\xFF\xFF\xFF");
			printf("vis t57,0\xFF\xFF\xFF");
			printf("vis t24,1\xFF\xFF\xFF");
			printf("t24.txt=\"CH1校准\"\xff\xff\xff");
			fft_enable=0;
			xy_enable=0;
			//caliboration(&caliboration_ch1,&caliboration_ch2);
		}break;
//		case 4:
//		{
//			if(xy_enable==0)
//			{
//				xy_enable=1;
//				fft_enable=0;
//				printf("t49.txt=\"FFT关\"\xff\xff\xff");
//				CH1_enable=0;
//				CH2_enable=0;
//				printf("cle 1,255\xff\xff\xff");
//				printf("t45.txt=\"->X-Y\"\xff\xff\xff");
//			}
//			else
//			{
//				xy_enable=0;
//				CH1_enable=1;
//				CH2_enable=1;
//				HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S);
//				printf("t45.txt=\"->Y-T\"\xff\xff\xff");
//			}
//		}break;
//		case 5:
//		{	
//			single_flag_1=0;
//			single_flag_2=0;
//			switch(Trigger_ANS)
//			{
//				case 0:
//				{
//					Trigger_ANS++;
//					printf("t46.txt=\"->NORMAL\"\xff\xff\xff");
//				}break;
//				case 1:
//				{
//					Trigger_ANS++;
//					single_flag=1;
//					printf("t46.txt=\"->SINGLE\"\xff\xff\xff");
//				}break;
//				case 2:
//				{
//					Trigger_ANS=0;
//					printf("t46.txt=\"->AUTO\"\xff\xff\xff");
//				}break;
//			}
//		}break;
//		//fft
//		case 6:
//		{
//			if(fft_enable==1)
//			{	
//				if(parament_flag==0&&cursor_mode==3)
//				{
//					printf("t52.txt=\"时间1：\"\xff\xff\xff");
//					printf("t51.txt=\"时间2：\"\xff\xff\xff");
//				}
//				printf("t2.txt=\"时间档位\"\xff\xff\xff");
//				
//				fft_enable=0;
//				renew_timeorfreq();
//				CH1_enable=1;
//				CH2_enable=1;
//				HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S);
//				printf("t49.txt=\"->FFT关\"\xff\xff\xff");
//			}
//			else
//			{	
//				if(parament_flag==0&&cursor_mode==3)
//				{
//					printf("t52.txt=\"频率1：\"\xff\xff\xff");
//					printf("t51.txt=\"频率2：\"\xff\xff\xff");
//				}
//				
//				fft_enable=1;
//				CH1_enable=1;
//				CH2_enable=1;
//				xy_enable=0;
//				printf("t45.txt=\"Y-T\"\xff\xff\xff");
//				printf("t49.txt=\"->FFT开\"\xff\xff\xff");
//				printf("t2.txt=\"频率档位\"\xff\xff\xff");
//				renew_timeorfreq();
//				printf("cle 1,255\xff\xff\xff");
//			}
//		}break;
//		case 1:
//		{
//			if(parament_flag==0)
//			{
//				parament_flag=1;
//				switch_parament(1);
//			}
//			else
//			{
//				parament_flag=0;
//				switch_parament(0);
//			}
//		}break;
		
	}
	if(menu2_status!=0)return;
	switch(menu_status)
	{
		case 9:
		{
				TIM4->CCR3++;
//			if(Channel==0)
//			{
//				Channel=1;
//				printf("t1.txt=\"CH2\"\xFF\xFF\xFF");
//				switch(voltage_per_grid_1)
//				{
//					case 1:
//					{
//						printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
//					}break;
//					case 2:
//					{					
//						printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
//					}break;
//					case 3:
//					{
//						printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
//					}break;
//					case 4:
//					{
//						printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
//					}break;
//					case 5:
//					{	
//						printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
//					}break;
//					case 6:
//					{	
//						printf("t5.txt=\"1V\"\xFF\xFF\xFF");
//					}break;
//					case 7:
//					{	
//						printf("t5.txt=\"2V\"\xFF\xFF\xFF");
//					}break;
//					case 8:
//					{
//						printf("t5.txt=\"5V\"\xFF\xFF\xFF");
//					}break;
//					case 9:
//					{
//						printf("t5.txt=\"10V\"\xFF\xFF\xFF");
//					}break;
//				}
//				switch(Ouhe1)
//				{
//					case 0:
//					{
//						printf("t13.txt=\"DC\"\xFF\xFF\xFF");
//					}break;
//					case 1:
//					{
//						printf("t13.txt=\"AC\"\xFF\xFF\xFF");
//					}
//				}
//			}
//			else if(Channel==1)
//			{
//				Channel=0;
//				printf("t1.txt=\"CH1\"\xFF\xFF\xFF");
//				switch(voltage_per_grid)
//				{
//					case 1:
//					{
//						printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
//					}break;
//					case 2:
//					{					
//						printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
//					}break;
//					case 3:
//					{
//						printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
//					}break;
//					case 4:
//					{
//						printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
//					}break;
//					case 5:
//					{	
//						printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
//					}break;
//					case 6:
//					{	
//						printf("t5.txt=\"1V\"\xFF\xFF\xFF");
//					}break;
////					case 7:
////					{	
////						printf("t5.txt=\"2V\"\xFF\xFF\xFF");
////					}break;
////					case 8:
////					{
////						printf("t5.txt=\"5V\"\xFF\xFF\xFF");
////					}break;
////					case 9:
////					{
////						printf("t5.txt=\"10V\"\xFF\xFF\xFF");
////					}break;
//				}
//				switch(Ouhe)
//				{
//					case 0:
//					{
//						printf("t13.txt=\"DC\"\xFF\xFF\xFF");
//					}break;
//					case 1:
//					{
//						printf("t13.txt=\"AC\"\xFF\xFF\xFF");
//					}
//				}
			
//			}
		}break;
		case 10:
		{
			switch(time_per_grid)
			{
//						case 4:
//						{	
//							//sample_100Mhz();
//							time_per_grid--;
//							printf("t3.txt=\"5us\"\xFF\xFF\xFF");
//						}break;
//						case 5:
//						{	
//							//sample_50Mhz();
//							time_per_grid--;
//							printf("t3.txt=\"10us\"\xFF\xFF\xFF");
//							if(fft_enable==1) printf("t3.txt=\"250KHz\"\xFF\xFF\xFF");
//						}break;
				case 6:
				{	
					TIM2->PSC=2-1;
					TIM2->ARR=4-1;
					time_per_grid--;
					printf("t3.txt=\"2us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"125KHz\"\xFF\xFF\xFF");
				}break;
				case 7:
				{	
					TIM2->PSC=2-1;
					TIM2->ARR=10-1;
					time_per_grid--;
					printf("t3.txt=\"5us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"50KHz\"\xFF\xFF\xFF");
				}break;
				case 8:
				{
					TIM2->PSC=2-1;
					TIM2->ARR=20-1;
					time_per_grid--;
					printf("t3.txt=\"10us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"25KHz\"\xFF\xFF\xFF");
				}break;
				case 9:
				{	
					TIM2->PSC=2-1;
					TIM2->ARR=40-1;
					time_per_grid--;
					printf("t3.txt=\"20us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"12.5KHz\"\xFF\xFF\xFF");
				}break;
				case 10:
				{
					TIM2->PSC=2-1;
					TIM2->ARR=100-1;
					time_per_grid--;
					printf("t3.txt=\"50us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"5KHz\"\xFF\xFF\xFF");
				}break;
				case 11:
				{
					TIM2->PSC=2-1;
					TIM2->ARR=200-1;
					time_per_grid--;
					printf("t3.txt=\"100us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"2.5KHz\"\xFF\xFF\xFF");
				}break;
//				case 12:
//				{
//					TIM2->PSC=2-1;
//					TIM2->ARR=400-1;
//					time_per_grid--;
//					printf("t3.txt=\"200us\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"1.25KHz\"\xFF\xFF\xFF");
//				}break;
//				case 13:
//				{
//					TIM2->PSC=2-1;
//					TIM2->ARR=1000-1;
//					time_per_grid--;
//					printf("t3.txt=\"500us\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"500Hz\"\xFF\xFF\xFF");
//				}break;
//				case 14:
//				{
//					TIM2->PSC=500-1;
//					TIM2->ARR=8-1;
//					time_per_grid--;
//					printf("t3.txt=\"1ms\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"250Hz\"\xFF\xFF\xFF");
//				}break;
//				case 15:
//				{
//					TIM2->PSC=500-1;
//					TIM2->ARR=16-1;
//					time_per_grid--;
//					printf("t3.txt=\"2ms\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"125Hz\"\xFF\xFF\xFF");
//				}break;
//				case 16:
//				{
//					TIM2->PSC=500-1;
//					TIM2->ARR=40-1;
//					time_per_grid--;
//					printf("t3.txt=\"5ms\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"50Hz\"\xFF\xFF\xFF");
//				}break;
//				case 17:
//				{
//					TIM2->PSC=500-1;
//					TIM2->ARR=80-1;
//					time_per_grid--;
//					printf("t3.txt=\"10ms\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"25Hz\"\xFF\xFF\xFF");
//				}break;
//				case 18:
//				{
//					TIM2->PSC=500-1;
//					TIM2->ARR=160-1;
//					time_per_grid--;
//					printf("t3.txt=\"20ms\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"12.5Hz\"\xFF\xFF\xFF");
//				}break;
//						case 19:
//						{
//							TIM2->PSC=500;
//							TIM2->ARR=400;
//							time_per_grid--;
//							printf("t3.txt=\"500ms\"\xFF\xFF\xFF");
//							if(fft_enable==1) printf("t3.txt=\"50Hz\"\xFF\xFF\xFF");
//						}break;
//						case 20:
//						{
//							TIM2->PSC=500;
//							TIM2->ARR=800;
//							time_per_grid--;
//							printf("t3.txt=\"100ms\"\xFF\xFF\xFF");
//							if(fft_enable==1) printf("t3.txt=\"25Hz\"\xFF\xFF\xFF");
//						}break;
//						case 0:
//						{
//							time_per_grid=20;
//							printf("t3.txt=\"200ms\"\xFF\xFF\xFF");
//						}break;
			}
		}break;
		case 11:
		{
			if(Channel==0)
			{
				switch(voltage_per_grid)
				{	
					case 1:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid--;
						printf("t5.txt=\"10mV\"\xFF\xFF\xFF");
					}break;
					case 2:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid--;
						printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
					}break;
					case 3:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
						voltage_per_grid--;
						printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
					}break;
					case 4:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
						voltage_per_grid--;
						printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
					}break;
					case 5:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid--;
						printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
						TIM4->CCR3=520;
					}break;
					case 6:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid--;
						printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
						TIM4->CCR3=520;
					}break;
					case 7:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid--;
						printf("t5.txt=\"1V\"\xFF\xFF\xFF");
						TIM4->CCR3=520;
					}break;
//					case 8:
//					{	
//						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
//						voltage_per_grid--;
//						printf("t5.txt=\"2V\"\xFF\xFF\xFF");
//					}break;
//					case 9:
//					{
//						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
//						voltage_per_grid--;
//						printf("t5.txt=\"5V\"\xFF\xFF\xFF");
//					}break;
//						case 0:
//						{
//							voltage_per_grid=9;
//							printf("t5.txt=\"10V\"\xFF\xFF\xFF");
//						}break;
				}
			
			}
//			else if(Channel==1)
//			{
//				switch(voltage_per_grid_1)
//				{	
//					case 1:
//					{
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1--;
//						printf("t5.txt=\"10mV\"\xFF\xFF\xFF");
//					}break;
//					case 2:
//					{
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1--;
//						printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
//					}break;
//					case 3:
//					{
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
//						voltage_per_grid_1--;
//						printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
//					}break;
//					case 4:
//					{
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1--;
//						printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
//					}break;
//					case 5:
//					{
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
//						voltage_per_grid_1--;
//						printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
//					}break;
//					case 6:
//					{
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1--;
//						printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
//					}break;
//					case 7:
//					{
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1--;
//						printf("t5.txt=\"1V\"\xFF\xFF\xFF");
//					}break;
//					case 8:
//					{	
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1--;
//						printf("t5.txt=\"2V\"\xFF\xFF\xFF");
//					}break;
//					case 9:
//					{
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET); 
//						voltage_per_grid_1--;
//						printf("t5.txt=\"5V\"\xFF\xFF\xFF");
//					}break;
////						case 0:
////						{
////							voltage_per_grid=9;
////							printf("t5.txt=\"10V\"\xFF\xFF\xFF");
////						}break;
//				}
//			}
		}break;
		//水平偏移
		case 12:
		{	
			if(offset<320)
			offset+=step;
			
			printf("move t26,%d,0,%d,0,0,30\xFF\xFF\xFF",325-step+offset,325+offset);
			if(measure_time_us(offset)>1000) printf("t7.txt=\"+%.2fms\"\xff\xff\xff",measure_time_ms(offset));
			else if (measure_time_us(offset)>=0) printf("t7.txt=\"+%.2fus\"\xff\xff\xff",measure_time_us(offset));
			else if (measure_time_us(offset)<-1000) printf("t7.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(offset));
			else if (measure_time_us(offset)<0) printf("t7.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(offset));
		}break;
		//垂直偏移
		case 13:
		{
			if(Channel==0)
			{
				offset_ch1+=1;
				if(measure_voltage_V(offset_ch1+128,1)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
				else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
				if(Trigger_state==1|Trigger_state==2)
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1-step)),(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1)));
				printf("move t29,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*(offset_ch1-step)),(int)(181-1.5*(offset_ch1)));
			}
			else
			{	
				offset_ch2+=1;
				if(measure_voltage_V(offset_ch2+128,2)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
				else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
				if(Trigger_state==3|Trigger_state==4)
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2-step)),(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2)));
				printf("move t30,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*(offset_ch2-step)),(int)(181-1.5*(offset_ch2)));
			}
		}break;
		case 14:
		{
			if(Trigger_state==1|Trigger_state==2)
			{
				Trigger_set_offset_ch1+=step;
				if(Trigger_set_offset_ch1>127) Trigger_set_offset_ch1=127;
				if(measure_voltage_V(Trigger_set_offset_ch1+128,1)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch1+128,1));
				else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch1+128,1));
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1-step)),(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1)));

				
			}
			else if (Trigger_state==3|Trigger_state==4)
			{
				Trigger_set_offset_ch2+=step;
				if(Trigger_set_offset_ch2>127) Trigger_set_offset_ch2=127;
				if(measure_voltage_V(Trigger_set_offset_ch2+128,2)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch2+128,2));
				else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch2+128,2));
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2-step)),(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2)));
			}
			
		}break;
		case 15:
		{
			if(Channel==0)
			{
				if(Ouhe==0)
				{
					Ouhe=1;
					printf("t13.txt=\"AC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_RESET);
				}
				else
				{
					Ouhe=0;
					printf("t13.txt=\"DC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_SET);
				}
			}
			else if(Channel==1)
			{
				if(Ouhe1==0)
				{
					Ouhe1=1;
					printf("t13.txt=\"AC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_RESET);
				}
				else
				{
					Ouhe1=0;
					printf("t13.txt=\"DC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_SET);
				}
			}
		}break;
		case 16:
			{
				switch(Trigger_state)
				{
					case 1:
					{
						Trigger_state=2;
						printf("t15.txt=\"CH1上\"\xFF\xFF\xFF");
					//	printf("t10.pco=\"yellow\"\xFF\xFF\xFF");
					}break;
					case 2:
					{
						Trigger_state=3;
						printf("t15.txt=\"CH2下\"\xFF\xFF\xFF");
				//		printf("t10.pco=\"blue\"\xFF\xFF\xFF");
					}break;
					case 3:
					{
						Trigger_state=4;
						printf("t15.txt=\"CH2上\"\xFF\xFF\xFF");
					//	printf("t10.pco=\"blue\"\xFF\xFF\xFF");
					}break;
					case 4:
					{
						Trigger_state=1;
						printf("t15.txt=\"CH1下\"\xFF\xFF\xFF");
					//	printf("t10.pco=\"yellow\"\xFF\xFF\xFF");
					}break;
				}
		}break;
	}
}

void left_button()
{	
	switch(caliboration_mode)
	{
		case 0:break;
		case 1:
		{
//			if(calibo_ch==1)
//			{
//				calibo_ch=2;
//				printf("vis t29,0\xFF\xFF\xFF");
//				printf("vis t30,1\xFF\xFF\xFF");
//				CH1_enable=0;
//				CH2_enable=1;
//				printf("cle 1,255\xFF\xFF\xFF");
//				printf("t24.txt=\"选通道：2\"\xFF\xFF\xFF");
//			}	
//			else
//			{
//				calibo_ch=1;
//				printf("vis t29,1\xFF\xFF\xFF");
//				printf("vis t30,0\xFF\xFF\xFF");
//				CH1_enable=1;
//				CH2_enable=0;
//				printf("cle 1,255\xFF\xFF\xFF");
//				printf("t24.txt=\"选通道：1\"\xFF\xFF\xFF");
//			}
		}break;
		case 2:
		{
			if(calibo_ch==1)
			{
				del_zero_ch1-=calibo_step_zero;
			}
			else
			{
				del_zero_ch2-=calibo_step_zero;
			}
		}break;
		case 3:
		{
			if(calibo_ch==1)
			{
				del_k_ch1-=calibo_step_k;
			}
			else
			{
				del_k_ch2-=calibo_step_k;
			}
		}break;
		case 4:
		{
			if(calibo_ch==1)
			{
				del_k_ch1+=calibo_step_k;
			}
			else
			{
				del_k_ch2+=calibo_step_k;
			}
		}break;
	}
	if(caliboration_mode!=0) return;
	if(cursor_status==1)
	{
		switch(cursor_mode)
		{
			case 1:
			{
				if(cursor_num==0)
				{
					cursor_num=1;
					
					printf("t24.txt=\"电压：2\"\xFF\xFF\xFF");
				}
				else
				{
					cursor_num=0;
					printf("t24.txt=\"电压：1\"\xFF\xFF\xFF");
				}
			}break;
			case 2:
			{
				if(xy_enable==1)
				{
					
					if(cursor_num==0&&x1>0)
					{
						//printf("t24.txt=\"选中：纵1\"\xFF\xFF\xFF");
						printf("move t16,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1-step);
						printf("move t22,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1-step);
						x1-=step;
					}
					else if(cursor_num==1&&x2>0)
					{
						//printf("t24.txt=\"选中：纵2\"\xFF\xFF\xFF");
						printf("move t17,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2-step);
						printf("move t23,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2-step);
						x2-=step;
					}
					break;
				}
				if(cursor_num==0)
				{
					cursor_num=1;
					printf("t24.txt=\"CH2电压：2\"\xFF\xFF\xFF");
				}
				else
				{
					cursor_num=0;
					printf("t24.txt=\"CH2电压：1\"\xFF\xFF\xFF");
				}
			}break;
			case 3:
			{
				if(cursor_num==0&&x1>0)
				{
					//printf("t24.txt=\"选中：纵1\"\xFF\xFF\xFF");
					printf("move t16,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1-step);
					printf("move t22,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1-step);
					x1-=step;
				}
				else if(cursor_num==1&&x2>0)
				{
					//printf("t24.txt=\"选中：纵2\"\xFF\xFF\xFF");
					printf("move t17,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2-step);
					printf("move t23,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2-step);
					x2-=step;
				}
			}break;
		}
		return;
	}
	switch(menu2_status)
	{
		case 1:
		{
			if(cursor_switch==1)
			{
				printf("vis t16,0\xFF\xFF\xFF");
				printf("vis t17,0\xFF\xFF\xFF");
				printf("vis t18,0\xFF\xFF\xFF");
				printf("vis t19,0\xFF\xFF\xFF");
				printf("vis t20,0\xFF\xFF\xFF");
				printf("vis t21,0\xFF\xFF\xFF");
				printf("vis t22,0\xFF\xFF\xFF");
				printf("vis t23,0\xFF\xFF\xFF");
				
				//printf("vis t24,0\xFF\xFF\xFF");
				printf("t58.txt=\"->光标关\"\xff\xff\xff");
				cursor_switch=0;
				
			}
			else if(cursor_switch==0)
			{
				cursor_switch=1;
				printf("t58.txt=\"->光标开\"\xff\xff\xff");
				printf("vis t31,0\xFF\xFF\xFF");
	
				switch(cursor_mode)
				{
					case 1:
					{
						printf("vis t18,1\xFF\xFF\xFF");
						printf("vis t19,1\xFF\xFF\xFF");
						printf("vis t20,1\xFF\xFF\xFF");
						printf("vis t21,1\xFF\xFF\xFF");
					}break;
					case 2:
					{
						printf("vis t18,1\xFF\xFF\xFF");
						printf("vis t19,1\xFF\xFF\xFF");
						printf("vis t20,1\xFF\xFF\xFF");
						printf("vis t21,1\xFF\xFF\xFF");
					}break;
					case 3:
					{
						printf("vis t16,1\xFF\xFF\xFF");
						printf("vis t17,1\xFF\xFF\xFF");
						printf("vis t22,1\xFF\xFF\xFF");
						printf("vis t23,1\xFF\xFF\xFF");
					}break;
				}
			}
		}break;
		//光标模式
		case 2:
		{
			
			
			printf("vis t45,0\xFF\xFF\xFF");
			printf("vis t46,0\xFF\xFF\xFF");
			printf("vis t49,0\xFF\xFF\xFF");
			printf("vis t57,0\xFF\xFF\xFF");
			printf("vis t24,1\xFF\xFF\xFF");
			cursor_switch=1;
			cursor_status=1;//光标模式开标志
			printf("t58.txt=\"光标开\"\xff\xff\xff");
			printf("vis t18,0\xFF\xFF\xFF");
			printf("vis t19,0\xFF\xFF\xFF");
			printf("vis t20,0\xFF\xFF\xFF");
			printf("vis t21,0\xFF\xFF\xFF");
			printf("vis t16,0\xFF\xFF\xFF");
			printf("vis t17,0\xFF\xFF\xFF");
			printf("vis t22,0\xFF\xFF\xFF");
			printf("vis t23,0\xFF\xFF\xFF");
			if(xy_enable==1)
			{
				if(cursor_mode==3) cursor_mode=1;
			}
			
			//刷新左上角菜单
			switch(cursor_mode)
			{
				case 0:break;
				case 1:
				{
					if(cursor_num==0) printf("t24.txt=\"电压：1\"\xff\xff\xff");
					else printf("t24.txt=\"电压：2\"\xff\xff\xff");
				}break;
//				case 2:
//				{
//					if(cursor_num==0) printf("t24.txt=\"CH2电压：1\"\xff\xff\xff");
//					else printf("t24.txt=\"CH2电压：2\"\xff\xff\xff");
//				}break;
				case 3:
				{
					if(fft_enable==0)
					{
						if(cursor_num==0) printf("t24.txt=\"时间：1\"\xff\xff\xff");
						else printf("t24.txt=\"时间：2\"\xff\xff\xff");
					}
					else
					{
						if(cursor_num==0) printf("t24.txt=\"频率：1\"\xff\xff\xff");
						else printf("t24.txt=\"频率：2\"\xff\xff\xff");
					}
				}break;
			}
			//修改下方参数
			switch(cursor_mode)
			{
				case 1:
				{
					printf("vis t18,1\xFF\xFF\xFF");
					printf("vis t19,1\xFF\xFF\xFF");
					printf("vis t20,1\xFF\xFF\xFF");
					printf("vis t21,1\xFF\xFF\xFF");
				}break;
				case 2:
				{
					printf("vis t18,1\xFF\7\xFF");
					printf("vis t19,1\xFF\xFF\xFF");
					printf("vis t20,1\xFF\xFF\xFF");
					printf("vis t21,1\xFF\xFF\xFF");
				}break;
				case 3:
				{
					printf("vis t16,1\xFF\xFF\xFF");
					printf("vis t17,1\xFF\xFF\xFF");
					printf("vis t22,1\xFF\xFF\xFF");
					printf("vis t23,1\xFF\xFF\xFF");
				}break;
			}
			switch_parament(0);
		}break;
						
		case 3:
		{	
			caliboration_mode=2;
			printf("vis t45,0\xFF\xFF\xFF");
			printf("vis t46,0\xFF\xFF\xFF");
			printf("vis t49,0\xFF\xFF\xFF");
			printf("vis t57,0\xFF\xFF\xFF");
			printf("vis t24,1\xFF\xFF\xFF");
			fft_enable=0;
			xy_enable=0;
			printf("t24.txt=\"CH1校准\"\xff\xff\xff");
		}break;
//		case 4:
//		{
//			if(xy_enable==0)
//			{
//				xy_enable=1;
//				fft_enable=0;
//				printf("t49.txt=\"FFT关\"\xff\xff\xff");
//				CH1_enable=0;
//				CH2_enable=0;
//				printf("cle 1,255\xff\xff\xff");
//				printf("t45.txt=\"->X-Y\"\xff\xff\xff");
//			}
//			else
//			{
//				xy_enable=0;
//				CH1_enable=1;
//				CH2_enable=1;
//				HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S);
//				printf("t45.txt=\"->Y-T\"\xff\xff\xff");
//			}
//		}break;
//		case 5:
//		{	
//			single_flag_1=0;
//			single_flag_2=0;
//			switch(Trigger_ANS)
//			{
//				case 0:
//				{
//					Trigger_ANS++;
//					printf("t46.txt=\"->NORMAL\"\xff\xff\xff");
//				}break;
//				case 1:
//				{
//					Trigger_ANS++;
//					single_flag=1;
//					printf("t46.txt=\"->SINGLE\"\xff\xff\xff");
//				}break;
//				case 2:
//				{
//					Trigger_ANS=0;
//					printf("t46.txt=\"->AUTO\"\xff\xff\xff");
//				}break;
//			}
//		}break;
//		//fft
//		case 6:
//		{
//			if(fft_enable==1)
//			{	
//				if(parament_flag==0&&cursor_mode==3)
//				{
//					printf("t52.txt=\"时间1：\"\xff\xff\xff");
//					printf("t51.txt=\"时间2：\"\xff\xff\xff");
//				}
//				printf("t2.txt=\"时间档位\"\xff\xff\xff");
//				
//				fft_enable=0;
//				renew_timeorfreq();
//				CH1_enable=1;
//				CH2_enable=1;
//				HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S);
//				printf("t49.txt=\"->FFT关\"\xff\xff\xff");
//			}
//			else
//			{	
//				if(parament_flag==0&&cursor_mode==3)
//				{
//					printf("t52.txt=\"频率1：\"\xff\xff\xff");
//					printf("t51.txt=\"频率2：\"\xff\xff\xff");
//				}
//				
//				fft_enable=1;
//				CH1_enable=1;
//				CH2_enable=1;
//				xy_enable=0;
//				printf("t45.txt=\"Y-T\"\xff\xff\xff");
//				printf("t49.txt=\"->FFT开\"\xff\xff\xff");
//				printf("t2.txt=\"频率档位\"\xff\xff\xff");
//				renew_timeorfreq();
//				printf("cle 1,255\xff\xff\xff");
//			}
//		}break;
//		case 1:
//		{
//			if(parament_flag==0)
//			{
//				parament_flag=1;
//				switch_parament(1);
//			}
//			else
//			{
//				parament_flag=0;
//				switch_parament(0);
//			}
//		}break;
//		
	}
	if(menu2_status!=0) return;
	switch(menu_status)
	{
		case 9:
		{
//			if(Channel==0)
//			{
//				Channel=1;
//				printf("t1.txt=\"CH2\"\xFF\xFF\xFF");
//				switch(voltage_per_grid_1)
//				{
//					case 1:
//					{
//						printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
//					}break;
//					case 2:
//					{					
//						printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
//					}break;
//					case 3:
//					{
//						printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
//					}break;
//					case 4:
//					{
//						printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
//					}break;
//					case 5:
//					{	
//						printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
//					}break;
//					case 6:
//					{	
//						printf("t5.txt=\"1V\"\xFF\xFF\xFF");
//					}break;
//					case 7:
//					{	
//						printf("t5.txt=\"2V\"\xFF\xFF\xFF");
//					}break;
//					case 8:
//					{
//						printf("t5.txt=\"5V\"\xFF\xFF\xFF");
//					}break;
//					case 9:
//					{
//						printf("t5.txt=\"10V\"\xFF\xFF\xFF");
//					}break;
//				}
//				switch(Ouhe1)
//				{
//					case 0:
//					{
//						printf("t13.txt=\"DC\"\xFF\xFF\xFF");
//					}break;
//					case 1:
//					{
//						printf("t13.txt=\"AC\"\xFF\xFF\xFF");
//					}
//				}
//			}
//			else if(Channel==1)
//			{
//				Channel=0;
//				printf("t1.txt=\"CH1\"\xFF\xFF\xFF");
//				switch(voltage_per_grid)
//				{
//					case 1:
//					{
//						printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
//					}break;
//					case 2:
//					{					
//						printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
//					}break;
//					case 3:
//					{
//						printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
//					}break;
//					case 4:
//					{
//						printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
//					}break;
//					case 5:
//					{	
//						printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
//					}break;
//					case 6:
//					{	
//						printf("t5.txt=\"1V\"\xFF\xFF\xFF");
//					}break;
////					case 7:
////					{	
////						printf("t5.txt=\"2V\"\xFF\xFF\xFF");
////					}break;
////					case 8:
////					{
////						printf("t5.txt=\"5V\"\xFF\xFF\xFF");
////					}break;
////					case 9:
////					{
////						printf("t5.txt=\"10V\"\xFF\xFF\xFF");
////					}break;
//				}
//				switch(Ouhe)
//				{
//					case 0:
//					{
//						printf("t13.txt=\"DC\"\xFF\xFF\xFF");
//					}break;
//					case 1:
//					{
//						printf("t13.txt=\"AC\"\xFF\xFF\xFF");
//					}
//				}
//			}
//	TIM4->CCR3--;
		}break;
		case 10:
		{
			switch(time_per_grid)
			{
				
				case 4:
				{	
					TIM2->PSC=2-1;
					TIM2->ARR=4-1;
					time_per_grid++;
					printf("t3.txt=\"2us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"100Hz\"\xFF\xFF\xFF");
					HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S);
				}break;
				case 5:
				{
					TIM2->PSC=2-1;
					TIM2->ARR=10-1;
					time_per_grid++;
					printf("t3.txt=\"5us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"50KMHz\"\xFF\xFF\xFF");
				}break;
				case 6:
				{
					TIM2->PSC=2-1;
					TIM2->ARR=20-1;
					time_per_grid++;
					printf("t3.txt=\"10us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"25KHz\"\xFF\xFF\xFF");
				}break;
				case 7:
				{
					TIM2->PSC=2-1;
					TIM2->ARR=40-1;
					time_per_grid++;
					printf("t3.txt=\"20us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"12.5KHz\"\xFF\xFF\xFF");
				}break;
				case 8:
				{
					TIM2->PSC=2-1;
					TIM2->ARR=100-1;
					time_per_grid++;
					printf("t3.txt=\"50us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"5KHz\"\xFF\xFF\xFF");
				}break;
				case 9:
				{
					TIM2->PSC=2-1;
					TIM2->ARR=200-1;
					time_per_grid++;
					printf("t3.txt=\"100us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"2.5KHz\"\xFF\xFF\xFF");
				}break;
//				case 10:
//				{
//					TIM2->PSC=2-1;
//					TIM2->ARR=400-1;
//					time_per_grid++;
//					printf("t3.txt=\"200us\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"1.25KHz\"\xFF\xFF\xFF");
//				}break;
//				case 11:
//				{
//					TIM2->PSC=2-1;
//					TIM2->ARR=1000-1;
//					time_per_grid++;
//					printf("t3.txt=\"500us\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"500Hz\"\xFF\xFF\xFF");
//				}break;
//				case 12:
//				{
//					TIM2->PSC=500-1;
//					TIM2->ARR=8-1;
//					time_per_grid++;
//					printf("t3.txt=\"1ms\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"250Hz\"\xFF\xFF\xFF");
//				}break;
//				case 13:
//				{	
//					TIM2->PSC=500-1;
//					TIM2->ARR=16-1;
//					time_per_grid++;
//					printf("t3.txt=\"2ms\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"125Hz\"\xFF\xFF\xFF");
//				}break;
//				case 14:
//				{
//					TIM2->PSC=500-1;
//					TIM2->ARR=40-1;
//					time_per_grid++;
//					printf("t3.txt=\"5ms\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"50Hz\"\xFF\xFF\xFF");
//				}break;
//				case 15:
//				{	
//					TIM2->PSC=500-1;
//					TIM2->ARR=80-1;
//					time_per_grid++;
//					printf("t3.txt=\"10ms\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"25Hz\"\xFF\xFF\xFF");
//				}break;
//				case 16:
//				{	
//					TIM2->PSC=500-1;
//					TIM2->ARR=160-1;
//					time_per_grid++;
//					printf("t3.txt=\"20ms\"\xFF\xFF\xFF");
//					if(fft_enable==1) printf("t3.txt=\"12.5Hz\"\xFF\xFF\xFF");
//				}break;
//						case 17:
//						{
//							TIM2->PSC=500;
//							TIM2->ARR=400-1;
//							time_per_grid++;
//							printf("t3.txt=\"500ms\"\xFF\xFF\xFF");
//							if(fft_enable==1) printf("t3.txt=\"50Hz\"\xFF\xFF\xFF");
//						}break;
//						case 18:
//						{
//							TIM2->PSC=500;
//							TIM2->ARR=800;
//							time_per_grid++;
//							printf("t3.txt=\"100ms\"\xFF\xFF\xFF");
//							if(fft_enable==1) printf("t3.txt=\"25Hz\"\xFF\xFF\xFF");
//						}break;
//						case 19:
//						{
//							TIM2->PSC=500;
//							TIM2->ARR=1600;
//							time_per_grid++;
//							printf("t3.txt=\"200ms\"\xFF\xFF\xFF");
//							if(fft_enable==1) printf("t3.txt=\"12.5Hz\"\xFF\xFF\xFF");
//						}break;
//						case 20:
//						{
//							time_per_grid=0;
//							printf("t3.txt=\"50ns\"\xFF\xFF\xFF");
//						}break;
			}
		}break;
		case 11:
		{
			if(Channel==0)
			{
				switch(voltage_per_grid)
				{
					case 0:
					{
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						voltage_per_grid++;
						printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
					}break;
					case 1:
					{
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						voltage_per_grid++;
						printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
					}break;
					case 2:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
						voltage_per_grid++;
						printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
					}break;
					case 3:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid++;
						printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
						TIM4->CCR3=520;
					}break;
					case 4:
					{	
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid++;
						printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
						TIM4->CCR3=520;
					}break;
					case 5:
					{	
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid++;
						printf("t5.txt=\"1V\"\xFF\xFF\xFF");
						TIM4->CCR3=520;
					}break;
//					case 6:
//					{	
//						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
//						voltage_per_grid++;
//						printf("t5.txt=\"2V\"\xFF\xFF\xFF");
//					}break;
//					case 7:
//					{
//						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
//						voltage_per_grid++;
//						printf("t5.txt=\"5V\"\xFF\xFF\xFF");
//					}break;
//					case 8:
//					{
//						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
//						voltage_per_grid++;
//						printf("t5.txt=\"10V\"\xFF\xFF\xFF");
//					}break;
//						case 9:
//						{
//							voltage_per_grid=0;
//							printf("t5.txt=\"10mV\"\xFF\xFF\xFF");
//						}break;
				}

			}
//			if(Channel==1)
//			{
//				switch(voltage_per_grid_1)
//				{
//					case 0:
//					{
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1++;
//						printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
//					}break;
//					case 1:
//					{
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
//						voltage_per_grid_1++;
//						printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
//					}break;
//					case 2:
//					{
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1++;
//						printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
//					}break;
//					case 3:
//					{
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
//						voltage_per_grid_1++;
//						printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
//					}break;
//					case 4:
//					{	
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1++;
//						printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
//					}break;
//					case 5:
//					{	
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1++;
//						printf("t5.txt=\"1V\"\xFF\xFF\xFF");
//					}break;
//					case 6:
//					{	
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1++;
//						printf("t5.txt=\"2V\"\xFF\xFF\xFF");
//					}break;
//					case 7:
//					{
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
//						voltage_per_grid_1++;
//						printf("t5.txt=\"5V\"\xFF\xFF\xFF");
//					}break;
//					case 8:
//					{
//						HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
//						voltage_per_grid_1++;
//						printf("t5.txt=\"10V\"\xFF\xFF\xFF");
//					}break;
////						case 9:
////						{
////							voltage_per_grid=0;
////							printf("t5.txt=\"10mV\"\xFF\xFF\xFF");
////						}break;
//				}
//			}
		}break;
		
		case 12:
		{	
			if(offset>-320)
			offset-=step;
			
			printf("move t26,%d,0,%d,0,0,30\xFF\xFF\xFF",325+step+offset,325+offset);
			if(measure_time_us(offset)>1000) printf("t7.txt=\"+%.2fms\"\xff\xff\xff",measure_time_ms(offset));
			else if (measure_time_us(offset)>=0) printf("t7.txt=\"+%.2fus\"\xff\xff\xff",measure_time_us(offset));
			else if (measure_time_us(offset)<-1000) printf("t7.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(offset));
			else if (measure_time_us(offset)<0) printf("t7.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(offset));
		}break;
		//垂直偏移
		case 13:
		{	
			if(Channel==0)
			{
				offset_ch1-=1;
				if(measure_voltage_V(offset_ch1+128,1)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
				else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
				if(Trigger_state==1|Trigger_state==2)
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1+step)),(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1)));
				printf("move t29,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*(offset_ch1+step)),(int)(181-1.5*(offset_ch1)));
			}
			else
			{	
				offset_ch2-=1;
				if(measure_voltage_V(offset_ch2+128,2)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
				else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
				if(Trigger_state==3|Trigger_state==4)
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2+step)),(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2)));
				printf("move t30,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*(offset_ch2+step)),(int)(181-1.5*(offset_ch2)));
			}
		}break;
		//触发阈值
		case 14:
		{
			
			if(Trigger_state==1|Trigger_state==2)
			{
				Trigger_set_offset_ch1-=step;
				if(Trigger_set_offset_ch1<-128) Trigger_set_offset_ch1=-128;
				if(measure_voltage_V(Trigger_set_offset_ch1+128,1)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch1+128,1));
				else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch1+128,1));
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1+step)),(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1)));
			}
			else if(Trigger_state==3|Trigger_state==4)
			{
				Trigger_set_offset_ch2-=step;
				if(Trigger_set_offset_ch2+offset_ch2<-128) Trigger_set_offset_ch2=-128;
				if(measure_voltage_V(Trigger_set_offset_ch2+128,1)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch2+128,1));
				else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch2+128,1));
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2+step)),(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2)));
			}
			
		}break;
		case 15:
		{
			if(Channel==0)
			{
				if(Ouhe==0)
				{
					Ouhe=1;
					printf("t13.txt=\"AC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_RESET);
				}
				else
				{
					Ouhe=0;
					printf("t13.txt=\"DC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_SET);
				}
			}
			else if(Channel==1)
			{
				if(Ouhe1==0)
				{
					Ouhe1=1;
					printf("t13.txt=\"AC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_RESET);
				}
				else
				{
					Ouhe1=0;
					printf("t13.txt=\"DC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_SET);
				}
			}
		}break;
		case 16:
			{
				switch(Trigger_state)
				{
					case 3:
					{
						Trigger_state=2;
						printf("t15.txt=\"CH1上\"\xFF\xFF\xFF");
					//	printf("t10.pco=\"yellow\"\xFF\xFF\xFF");
					}break;
					case 4:
					{
						Trigger_state=3;
						printf("t15.txt=\"CH2下\"\xFF\xFF\xFF");
				//		printf("t10.pco=\"blue\"\xFF\xFF\xFF");
					}break;
					case 1:
					{
						Trigger_state=4;
						printf("t15.txt=\"CH2上\"\xFF\xFF\xFF");
					//	printf("t10.pco=\"blue\"\xFF\xFF\xFF");
					}break;
					case 2:
					{
						Trigger_state=1;
						printf("t15.txt=\"CH1下\"\xFF\xFF\xFF");
					//	printf("t10.pco=\"yellow\"\xFF\xFF\xFF");
					}break;
				}
		}break;
	}
}

void up_button()
{
	
	switch(caliboration_mode)
	{
		case 0:break;
		case 1:
		{
//			if(calibo_ch==1)
//			{
//				calibo_ch=2;
//				printf("t24.txt=\"选通道：2\"\xFF\xFF\xFF");
//				printf("vis t29,0\xFF\xFF\xFF");
//				printf("vis t30,1\xFF\xFF\xFF");
//				CH1_enable=0;
//				CH2_enable=1;
//				printf("cle 1,255\xFF\xFF\xFF");
//			}	
//			else
//			{
//				calibo_ch=1;
//				printf("t24.txt=\"选通道：1\"\xFF\xFF\xFF");
//				printf("vis t29,1\xFF\xFF\xFF");
//				printf("vis t30,0\xFF\xFF\xFF");
//				CH1_enable=1;
//				CH2_enable=0;
//				printf("cle 1,255\xFF\xFF\xFF");
//			}
		}break;
		case 2:
		{
			if(calibo_ch==1)
			{
				del_zero_ch1+=calibo_step_zero;
			}
			else
			{
				del_zero_ch2+=calibo_step_zero;
			}
		}break;
		case 3:
		{
			if(calibo_ch==1)
			{
				del_k_ch1+=calibo_step_k;
			}
			else
			{
				del_k_ch2+=calibo_step_k;
			}
		}break;
		case 4:
		{
			if(calibo_ch==1)
			{
				del_k_ch1-=calibo_step_k;
			}
			else
			{
				del_k_ch2-=calibo_step_k;
			}
		}break;
	}
	if(caliboration_mode!=0) return;
	if(cursor_status==1)
	{
		switch(cursor_mode)
		{
			case 1:
			{
				if(cursor_num==0&&y1>0)
				{
					//printf("t24.txt=\"选中：横1\"\xFF\xFF\xFF");
				
					printf("move t18,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1-step);
					printf("move t20,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1-step);
					y1-=step;
				}
				else if(cursor_num==1&&y2>0)
				{
					//printf("t24.txt=\"选中：横2\"\xFF\xFF\xFF");
					printf("move t19,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2-step);
					printf("move t21,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2-step);
					y2-=step;
				}
			}break;
			case 2:
			{
				if(xy_enable==1)
				{
					if(cursor_num==0)
					{
						cursor_num=1;
						printf("t24.txt=\"CH2电压：2\"\xFF\xFF\xFF");
					}
					else
					{
						cursor_num=0;
						printf("t24.txt=\"CH2电压：1\"\xFF\xFF\xFF");
					}
					break;
				}
				if(cursor_num==0&&y1>0)
				{
					//printf("t24.txt=\"选中：横1\"\xFF\xFF\xFF");
				
					printf("move t18,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1-step);
					printf("move t20,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1-step);
					y1-=step;
				}
				else if(cursor_num==1&&y2>0)
				{
					//printf("t24.txt=\"选中：横2\"\xFF\xFF\xFF");
					printf("move t19,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2-step);
					printf("move t21,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2-step);
					y2-=step;
				}
			}break;
			case 3:
			{
				if(cursor_num==0)
				{
					cursor_num=1;
					if(fft_enable==0) printf("t24.txt=\"时间：2\"\xFF\xFF\xFF");
					else printf("t24.txt=\"频率：2\"\xFF\xFF\xFF");
				}
				else
				{
					cursor_num=0;
					if(fft_enable==0) printf("t24.txt=\"时间：1\"\xFF\xFF\xFF");
					else printf("t24.txt=\"频率：1\"\xFF\xFF\xFF");
				}
			}break;
		}
			
		return;
	}
	if(menu2_status!=0)
	{
		menu2_status--;
		if(menu2_status==0) menu_status=12;
		if(menu2_status==3)
		{
			if(*(__IO uint32_t*)0x08019000!=0xffffffff) menu2_status=2;//正常模式
		}
		renew_menu2();renew_menu1();
		return;
	}
	
	menu_status--;
	if(menu_status==9)
	{
		menu2_status=3;
		if(menu2_status==3)
		{
			if(*(__IO uint32_t*)0x08019000!=0xffffffff) menu2_status=2;//正常模式
		}
		renew_menu2();
	}
	renew_menu1();
}



void down_button()
{	
	switch(caliboration_mode)
	{
		case 0:break;
		case 1:
		{
//			if(calibo_ch==1)
//			{
//				calibo_ch=2;
//				printf("t24.txt=\"选通道：2\"\xFF\xFF\xFF");
//				printf("vis t29,0\xFF\xFF\xFF");
//				printf("vis t30,1\xFF\xFF\xFF");
//				CH1_enable=0;
//				CH2_enable=1;
//				printf("cle 1,255\xFF\xFF\xFF");
//			}	
//			else
//			{
//				calibo_ch=1;
//				printf("t24.txt=\"选通道：1\"\xFF\xFF\xFF");
//				printf("vis t29,1\xFF\xFF\xFF");
//				printf("vis t30,0\xFF\xFF\xFF");
//				CH1_enable=1;
//				CH2_enable=0;
//				printf("cle 1,255\xFF\xFF\xFF");
//			}
		}break;
		case 2:
		{
			if(calibo_ch==1)
			{
				del_zero_ch1-=calibo_step_zero;
			}
			else
			{
				del_zero_ch2-=calibo_step_zero;
			}
		}break;
		case 3:
		{
			if(calibo_ch==1)
			{
				del_k_ch1-=calibo_step_k;
			}
			else
			{
				del_k_ch2-=calibo_step_k;
			}
		}break;
		case 4:
		{
			if(calibo_ch==1)
			{
				del_k_ch1+=calibo_step_k;
			}
			else
			{
				del_k_ch2+=calibo_step_k;
			}
		}break;
	}
	if(caliboration_mode!=0) return;
	if(cursor_status==1)
	{
		switch(cursor_mode)
		{
			case 1:
			{
				if(cursor_num==0&&y1<380)
				{
					//printf("t24.txt=\"选中：横1\"\xFF\xFF\xFF");
				
					printf("move t18,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1+step);
					printf("move t20,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1+step);
					y1+=step;
				}
				else if(cursor_num==1&&y2<380)
				{
					//printf("t24.txt=\"选中：横2\"\xFF\xFF\xFF");
					printf("move t19,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2+step);
					printf("move t21,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2+step);
					y2+=step;
				}
			}break;
			case 2:
			{
				if(xy_enable==1)
				{
					if(cursor_num==0)
					{
						cursor_num=1;
						printf("t24.txt=\"CH2电压：2\"\xFF\xFF\xFF");
					}
					else
					{
						cursor_num=0;
						printf("t24.txt=\"CH2电压：1\"\xFF\xFF\xFF");
					}
					break;
				}
				if(cursor_num==0&&y1<380)
				{
					//printf("t24.txt=\"选中：横1\"\xFF\xFF\xFF");
				
					printf("move t18,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1+step);
					printf("move t20,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1+step);
					y1+=step;
				}
				else if(cursor_num==1&&y2<380)
				{
					//printf("t24.txt=\"选中：横2\"\xFF\xFF\xFF");
					printf("move t19,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2+step);
					printf("move t21,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2+step);
					y2+=step;
				}
			}break;
			case 3:
			{
				if(cursor_num==0)
				{
					cursor_num=1;
					if(fft_enable==0) printf("t24.txt=\"时间：2\"\xFF\xFF\xFF");
					else printf("t24.txt=\"频率：2\"\xFF\xFF\xFF");
				}
				else
				{
					cursor_num=0;
					if(fft_enable==0) printf("t24.txt=\"时间：1\"\xFF\xFF\xFF");
					else printf("t24.txt=\"频率：1\"\xFF\xFF\xFF");
				}
			}break;
		}
			
		return;
	}
	if(menu2_status!=0)
	{
		menu2_status++;
		if(*(__IO uint32_t*)0x08019000!=0xffffffff)
		{
			if(menu2_status==3) {menu2_status=0;menu_status=10;};
		}
		if(menu2_status==4) {menu2_status=0;menu_status=10;};
		renew_menu2();renew_menu1();
		return;
	}
	
	menu_status++;
	if(menu_status==13)
	{
		menu2_status=1;
		renew_menu2();
	}
	renew_menu1();
		
		
}

void cursor_button()
{
	switch(cursor_status)
	{
		case 0:
		{
			cursor_status=1;
			printf("vis t16,1\xFF\xFF\xFF");
			printf("vis t17,1\xFF\xFF\xFF");
			printf("vis t18,1\xFF\xFF\xFF");
			printf("vis t19,1\xFF\xFF\xFF");
			printf("vis t20,1\xFF\xFF\xFF");
			printf("vis t21,1\xFF\xFF\xFF");
			printf("vis t22,1\xFF\xFF\xFF");
			printf("vis t23,1\xFF\xFF\xFF");
		}break;	
		case 1:
		{
			cursor_status=0;
			printf("vis t16,0\xFF\xFF\xFF");
			printf("vis t17,0\xFF\xFF\xFF");
			printf("vis t18,0\xFF\xFF\xFF");
			printf("vis t19,0\xFF\xFF\xFF");
			printf("vis t20,0\xFF\xFF\xFF");
			printf("vis t21,0\xFF\xFF\xFF");
			printf("vis t22,0\xFF\xFF\xFF");
			printf("vis t23,0\xFF\xFF\xFF");
		}break;	
	}
}
//菜单键
void menu2_button()
{	
	switch(caliboration_mode)
	{
		case 0:break;
		case 5:
		{
			caliboration_mode=2;
			printf("t24.txt=\"CH1校准\"\xFF\xFF\xFF");
			
		}break;
		case 3:
		{
			caliboration_mode=2;
			
			if(calibo_ch==1)
			{
				offset_ch1=0;
				printf("move t29,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch1),(int)(181-1.5*(offset_ch1)));
				printf("t24.txt=\"CH1校准1/3\"\xFF\xFF\xFF");
				
			}
			else
			{
				offset_ch2=0;
				printf("move t30,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch2),(int)(181-1.5*(offset_ch2)));
				printf("t24.txt=\"CH2校准1/3\"\xFF\xFF\xFF");
			}
		}break;
		case 4:
		{
			caliboration_mode=3;
			if(calibo_ch==1)
			{
				offset_ch1=96;
				printf("move t29,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch1),(int)(181-1.5*(offset_ch1)));
				printf("t24.txt=\"CH1校准2/3\"\xFF\xFF\xFF");
				
			}
			else
			{
				offset_ch2=96;
				printf("move t30,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch2),(int)(181-1.5*(offset_ch2)));
				printf("t24.txt=\"CH2校准2/3\"\xFF\xFF\xFF");
			}
		}break;
		case 2:
		{
			caliboration_mode=0;
			offset_ch1=0;
			offset_ch2=0;
			printf("move t29,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch1),(int)(181-1.5*(offset_ch1)));
			printf("move t30,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch2),(int)(181-1.5*(offset_ch2)));
		}break;
		case 1:
		{
			caliboration_mode=0;
			if(*(__IO uint32_t*)0x08019000==0xffffffff)	printf("vis t44,1\xFF\xFF\xFF");
			else printf("vis t44,0\xFF\xFF\xFF");
			
			printf("vis t45,1\xFF\xFF\xFF");
			printf("vis t46,1\xFF\xFF\xFF");
			printf("vis t49,1\xFF\xFF\xFF");
			printf("vis t57,1\xFF\xFF\xFF");
			printf("vis t50,1\xFF\xFF\xFF");			
			printf("vis t58,1\xFF\xFF\xFF");
			printf("vis t24,0\xFF\xFF\xFF");
			printf("vis t25,1\xFF\xFF\xFF");
			printf("vis t26,1\xFF\xFF\xFF");
			CH1_enable=1;
			CH2_enable=1;
			return;
		}break;
	}
	if(caliboration_mode!=0) return;
	if(cursor_status==1)
	{
		cursor_status=0;
		if(*(__IO uint32_t*)0x08019000==0xffffffff)	printf("vis t44,1\xFF\xFF\xFF");
		else printf("vis t44,0\xFF\xFF\xFF");
		printf("vis t45,1\xFF\xFF\xFF");
		printf("vis t46,1\xFF\xFF\xFF");
		printf("vis t49,1\xFF\xFF\xFF");
		printf("vis t57,1\xFF\xFF\xFF");
		printf("vis t50,1\xFF\xFF\xFF");			
		printf("vis t58,1\xFF\xFF\xFF");
		printf("vis t24,0\xFF\xFF\xFF");
		return;
	}
//	if(menu2_status==0)
//	{
//		menu2_status=1;
//		printf("t0.txt=\"通道\"\xFF\xFF\xFF");
//		printf("t2.txt=\"时间档位\"\xFF\xFF\xFF");
//		if(fft_enable==1) printf("t2.txt=\"频率档位\"\xFF\xFF\xFF");
//		printf("t4.txt=\"垂直档位\"\xFF\xFF\xFF");
//		printf("t6.txt=\"水平偏移\"\xFF\xFF\xFF");
//		printf("t8.txt=\"垂直偏移\"\xFF\xFF\xFF");
//		printf("t10.txt=\"触发阈值\"\xFF\xFF\xFF");
//		printf("t12.txt=\"耦合方式\"\xFF\xFF\xFF");
//		printf("t14.txt=\"触发类型\"\xFF\xFF\xFF");
//	//	printf("vis t24,1\xFF\xFF\xFF");
//		if(*(__IO uint32_t*)0x08019000==0xffffffff)	printf("vis t44,1\xFF\xFF\xFF");
//		else printf("vis t44,0\xFF\xFF\xFF");
//		printf("vis t45,1\xFF\xFF\xFF");
//		printf("vis t46,1\xFF\xFF\xFF");
//		printf("vis t49,1\xFF\xFF\xFF");			
//		printf("vis t57,1\xFF\xFF\xFF");
//		printf("vis t50,1\xFF\xFF\xFF");			
//		printf("vis t58,1\xFF\xFF\xFF");
////		printf("t57.txt=\"->切换参数\"\xff\xff\xff");
////		if(xy_enable==0) printf("t45.txt=\"Y-T\"\xff\xff\xff");
////		else printf("t45.txt=\"X-Y\"\xff\xff\xff");
//		 printf("t50.txt=\"光标模式\"\xff\xff\xff");
//		if(cursor_switch==0) printf("t58.txt=\"->光标关\"\xff\xff\xff");
//		else printf("t58.txt=\"->光标开\"\xff\xff\xff");
//		switch(Trigger_ANS)
//		{
//			case 0:
//			{
//				printf("t46.txt=\"AUTO\"\xff\xff\xff");
//			}break;
//			case 1:
//			{
//				printf("t46.txt=\"NORMAL\"\xff\xff\xff");

//			}break;
//			case 2:
//			{
//				printf("t46.txt=\"SINGLE\"\xff\xff\xff");

//			}break;
//		}
//		if(fft_enable==1) printf("t49.txt=\"FFT开\"\xff\xff\xff");
//		else printf("t49.txt=\"FFT关\"\xff\xff\xff");
//		printf("t44.txt=\"校准模式\"\xff\xff\xff");
////		if(get_freq_enable==0) printf("t50.txt=\"测频关\"\xff\xff\xff");
////		else printf("t50.txt=\"测频开\"\xff\xff\xff");
//	}
//	else
//	{	
//		printf("t2.txt=\"->时间档位\"\xFF\xFF\xFF");
//		menu_status=10;
//		//printf("vis t24,0\xFF\xFF\xFF");
//		printf("vis t44,0\xFF\xFF\xFF");
//		printf("vis t45,0\xFF\xFF\xFF");
//		printf("vis t46,0\xFF\xFF\xFF");
//		printf("vis t49,0\xFF\xFF\xFF");
//		printf("vis t57,0\xFF\xFF\xFF");
//		printf("vis t50,0\xFF\xFF\xFF");			
//		printf("vis t58,0\xFF\xFF\xFF");
//		menu2_status=0;
//	}
}


void confirm_button()
{
	switch(caliboration_mode)
	{
		case 0:break;
		case 1:
		{
			caliboration_mode=2;
			
			if(calibo_ch==1)
			{
				offset_ch1=0;
				printf("move t29,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch1),(int)(181-1.5*(offset_ch1)));
				printf("t24.txt=\"CH1校准\"\xFF\xFF\xFF");
				
			}
//			else
//			{
//				offset_ch2=0;
//				printf("move t30,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch2),(int)(181-1.5*(offset_ch2)));
//				printf("t24.txt=\"CH2校准1/3\"\xFF\xFF\xFF");
//			}
		}break;
//		
		case 2:
		{
			if(*(__IO uint32_t*)0x08019000!=0xffffffff) 
			{
				caliboration_mode=1;
			offset_ch1=0;
			offset_ch2=0;
			printf("move t29,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch1),(int)(181-1.5*(offset_ch1)));
			printf("move t30,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch2),(int)(181-1.5*(offset_ch2)));
				if(calibo_ch==1)
				{
					printf("t24.txt=\"选通道：1\"\xFF\xFF\xFF");
					CH1_enable=1;
					CH2_enable=0;
					printf("cle 1,255\xFF\xFF\xFF");
					printf("vis t29,1\xFF\xFF\xFF");
					printf("vis t30,0\xFF\xFF\xFF");
				}
				else
				{
					printf("t24.txt=\"选通道：2\"\xFF\xFF\xFF");
					CH1_enable=0;
					CH2_enable=1;
					printf("cle 1,255\xFF\xFF\xFF");
					printf("vis t30,1\xFF\xFF\xFF");
					printf("vis t29,0\xFF\xFF\xFF");
				}
				return;
			};
			caliboration_mode=5;
			{
				printf("t24.txt=\"按确定保存\"\xFF\xFF\xFF");
				
			}
		}break;
		case 5:
		{
			
			load_writedata();
			STMFLASH_OnlyWrite(0x08019000,Flash_WData,4);
			caliboration_mode=0;
			offset_ch1=0;
			offset_ch2=0;
			printf("move t29,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch1),(int)(181-1.5*(offset_ch1)));
			printf("move t30,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*offset_ch2),(int)(181-1.5*(offset_ch2)));
			printf("vis t24,0\xff\xff\xff");
			if(*(__IO uint32_t*)0x08019000==0xffffffff)	printf("vis t44,1\xFF\xFF\xFF");
			else printf("vis t44,0\xFF\xFF\xFF");
			menu_status=10;
			menu2_status=0;
			printf("t2.txt=\"->时间档位\"\xff\xff\xff");
			printf("vis t45,1\xFF\xFF\xFF");
			printf("vis t46,1\xFF\xFF\xFF");
			printf("vis t49,1\xFF\xFF\xFF");
			printf("vis t57,1\xFF\xFF\xFF");
			printf("vis t50,1\xFF\xFF\xFF");			
			printf("vis t58,1\xFF\xFF\xFF");
			printf("vis t24,0\xFF\xFF\xFF");
			printf("vis t25,1\xFF\xFF\xFF");
			printf("vis t26,1\xFF\xFF\xFF");
			printf("vis t50,1\xff\xff\xff");
			printf("vis t58,1\xff\xff\xff");
			return;
		}break;
	}
	if(caliboration_mode!=0) return;
	//曲线设定
	if(cursor_status!=0)
	{
			printf("vis t18,0\xFF\xFF\xFF");
			printf("vis t19,0\xFF\xFF\xFF");
			printf("vis t20,0\xFF\xFF\xFF");
			printf("vis t21,0\xFF\xFF\xFF");
			printf("vis t16,0\xFF\xFF\xFF");
			printf("vis t17,0\xFF\xFF\xFF");
			printf("vis t22,0\xFF\xFF\xFF");
			printf("vis t23,0\xFF\xFF\xFF");
			cursor_num=0;
			switch(cursor_mode)
			{
//				case 1:
//				{
//					cursor_mode=2;
//					printf("t24.txt=\"CH2电压：1\"\xff\xff\xff");
//					printf("t52.txt=\"CH2电压1：\"\xff\xff\xff");
//					printf("t51.txt=\"CH2电压2：\"\xff\xff\xff");
//					if(xy_enable==0)
//					{
//						printf("vis t18,1\xFF\xFF\xFF");
//						printf("vis t19,1\xFF\xFF\xFF");
//						printf("vis t20,1\xFF\xFF\xFF");
//						printf("vis t21,1\xFF\xFF\xFF");
//					}
//					else
//					{
//						printf("vis t16,1\xFF\xFF\xFF");
//						printf("vis t17,1\xFF\xFF\xFF");
//						printf("vis t22,1\xFF\xFF\xFF");
//						printf("vis t23,1\xFF\xFF\xFF");
//					}	
//					switch_parament(0);
//				}break;
				case 1:
				{
//					if(xy_enable==1)
//					{
//						cursor_mode=1;
//						printf("t24.txt=\"CH1电压：1\"\xff\xff\xff");
//						printf("t52.txt=\"CH1电压1：\"\xff\xff\xff");
//						printf("t51.txt=\"CH1电压2：\"\xff\xff\xff");
//						printf("vis t18,1\xFF\xFF\xFF");
//						printf("vis t19,1\xFF\xFF\xFF");
//						printf("vis t20,1\xFF\xFF\xFF");
//						printf("vis t21,1\xFF\xFF\xFF");
//						break;
//					}
					cursor_mode=3;
					if(fft_enable==0)
					{
						printf("t24.txt=\"时间：1\"\xff\xff\xff");
						printf("t52.txt=\"时间1：\"\xff\xff\xff");
						printf("t51.txt=\"时间2：\"\xff\xff\xff");
					}
					else
					{
						printf("t24.txt=\"频率：1\"\xff\xff\xff");
						printf("t52.txt=\"频率1：\"\xff\xff\xff");
						printf("t51.txt=\"频率2：\"\xff\xff\xff");
					}
					printf("vis t16,1\xFF\xFF\xFF");
					printf("vis t17,1\xFF\xFF\xFF");
					printf("vis t22,1\xFF\xFF\xFF");
					printf("vis t23,1\xFF\xFF\xFF");
				}break;
				case 3:
				{
					cursor_mode=1;
					printf("t24.txt=\"电压：1\"\xff\xff\xff");
					printf("t52.txt=\"电压1：\"\xff\xff\xff");
					printf("t51.txt=\"电压2：\"\xff\xff\xff");
					printf("vis t18,1\xFF\xFF\xFF");
					printf("vis t19,1\xFF\xFF\xFF");
					printf("vis t20,1\xFF\xFF\xFF");
					printf("vis t21,1\xFF\xFF\xFF");
				}break;
				
			}
		return;
	}
	//菜单2设定
	switch(menu2_status)
	{
		case 1:
		{
			if(cursor_switch==1)
			{
				printf("vis t16,0\xFF\xFF\xFF");
				printf("vis t17,0\xFF\xFF\xFF");
				printf("vis t18,0\xFF\xFF\xFF");
				printf("vis t19,0\xFF\xFF\xFF");
				printf("vis t20,0\xFF\xFF\xFF");
				printf("vis t21,0\xFF\xFF\xFF");
				printf("vis t22,0\xFF\xFF\xFF");
				printf("vis t23,0\xFF\xFF\xFF");
				
				//printf("vis t24,0\xFF\xFF\xFF");
				printf("t58.txt=\"->光标关\"\xff\xff\xff");
				cursor_switch=0;
				
			}
			else if(cursor_switch==0)
			{
				cursor_switch=1;
				printf("t58.txt=\"->光标开\"\xff\xff\xff");
				switch(cursor_mode)
				{
					case 1:
					{
						printf("vis t18,1\xFF\xFF\xFF");
						printf("vis t19,1\xFF\xFF\xFF");
						printf("vis t20,1\xFF\xFF\xFF");
						printf("vis t21,1\xFF\xFF\xFF");
					}break;
					case 2:
					{
						printf("vis t18,1\xFF\xFF\xFF");
						printf("vis t19,1\xFF\xFF\xFF");
						printf("vis t20,1\xFF\xFF\xFF");
						printf("vis t21,1\xFF\xFF\xFF");
					}break;
					case 3:
					{
						printf("vis t16,1\xFF\xFF\xFF");
						printf("vis t17,1\xFF\xFF\xFF");
						printf("vis t22,1\xFF\xFF\xFF");
						printf("vis t23,1\xFF\xFF\xFF");
					}break;
				}
			}
		}break;
		//光标模式
		case 2:
		{
			printf("vis t45,0\xFF\xFF\xFF");
			printf("vis t46,0\xFF\xFF\xFF");
			printf("vis t49,0\xFF\xFF\xFF");
			printf("vis t57,0\xFF\xFF\xFF");
			printf("vis t24,1\xFF\xFF\xFF");
			//printf("t24.txt=\"CH1电压：1\"\xff\xff\xff");
			cursor_switch=1;
			cursor_status=1;//光标模式开标志
			printf("t58.txt=\"光标开\"\xff\xff\xff");
			printf("vis t18,0\xFF\xFF\xFF");
			printf("vis t19,0\xFF\xFF\xFF");
			printf("vis t20,0\xFF\xFF\xFF");
			printf("vis t21,0\xFF\xFF\xFF");
			printf("vis t16,0\xFF\xFF\xFF");
			printf("vis t17,0\xFF\xFF\xFF");
			printf("vis t22,0\xFF\xFF\xFF");
			printf("vis t23,0\xFF\xFF\xFF");
			if(xy_enable==1)
			{
				if(cursor_mode==3) cursor_mode=1;
			}
			//刷新左上角菜单
			switch(cursor_mode)
			{
				case 0:break;
				case 1:
				{
					if(cursor_num==0) printf("t24.txt=\"电压：1\"\xff\xff\xff");
					else printf("t24.txt=\"电压：2\"\xff\xff\xff");
				}break;
//				case 2:
//				{
//					if(cursor_num==0) printf("t24.txt=\"CH2电压：1\"\xff\xff\xff");
//					else printf("t24.txt=\"CH2电压：2\"\xff\xff\xff");
//				}break;
				case 3:
				{
					if(fft_enable==0)
					{
						if(cursor_num==0) printf("t24.txt=\"时间：1\"\xff\xff\xff");
						else printf("t24.txt=\"时间：2\"\xff\xff\xff");
					}
					else
					{
						if(cursor_num==0) printf("t24.txt=\"频率：1\"\xff\xff\xff");
						else printf("t24.txt=\"频率：2\"\xff\xff\xff");
					}
				}break;
			}
			//修改下方参数
			switch(cursor_mode)
			{
				case 1:
				{
					printf("vis t18,1\xFF\xFF\xFF");
					printf("vis t19,1\xFF\xFF\xFF");
					printf("vis t20,1\xFF\xFF\xFF");
					printf("vis t21,1\xFF\xFF\xFF");
				}break;
				case 2:
				{
					if(xy_enable==1)
					{
						printf("vis t16,1\xFF\xFF\xFF");
						printf("vis t17,1\xFF\xFF\xFF");
						printf("vis t22,1\xFF\xFF\xFF");
						printf("vis t23,1\xFF\xFF\xFF");
						break;
					}
					printf("vis t18,1\xFF\xFF\xFF");
					printf("vis t19,1\xFF\xFF\xFF");
					printf("vis t20,1\xFF\xFF\xFF");
					printf("vis t21,1\xFF\xFF\xFF");
				}break;
				case 3:
				{
					printf("vis t16,1\xFF\xFF\xFF");
					printf("vis t17,1\xFF\xFF\xFF");
					printf("vis t22,1\xFF\xFF\xFF");
					printf("vis t23,1\xFF\xFF\xFF");
				}break;
			}
			switch_parament(0);
		}break;
						
		case 3:
		{
			caliboration_mode=2;
			printf("vis t45,0\xFF\xFF\xFF");
			printf("vis t46,0\xFF\xFF\xFF");
			printf("vis t49,0\xFF\xFF\xFF");
			printf("vis t57,0\xFF\xFF\xFF");
			printf("vis t24,1\xFF\xFF\xFF");
			printf("vis t25,0\xFF\xFF\xFF");
			printf("vis t26,0\xFF\xFF\xFF");
			
			printf("vis t30,0\xFF\xFF\xFF");
			fft_enable=0;
			xy_enable=0;
			printf("t24.txt=\"CH1校准\"\xFF\xFF\xFF");
		}break;
	}
	if(menu2_status!=0)return;
	switch(menu_status)
	{
		case 9:
		{
			if(Channel==0)
			{
				Channel=1;
				printf("t1.txt=\"CH2\"\xFF\xFF\xFF");
				switch(voltage_per_grid_1)
				{
					case 1:
					{
						printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
					}break;
					case 2:
					{					
						printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
					}break;
					case 3:
					{
						printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
					}break;
					case 4:
					{
						printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
					}break;
					case 5:
					{	
						printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
					}break;
					case 6:
					{	
						printf("t5.txt=\"1V\"\xFF\xFF\xFF");
					}break;
					case 7:
					{	
						printf("t5.txt=\"2V\"\xFF\xFF\xFF");
					}break;
					case 8:
					{
						printf("t5.txt=\"5V\"\xFF\xFF\xFF");
					}break;
					case 9:
					{
						printf("t5.txt=\"10V\"\xFF\xFF\xFF");
					}break;
				}
				switch(Ouhe1)
				{
					case 0:
					{
						printf("t13.txt=\"DC\"\xFF\xFF\xFF");
					}break;
					case 1:
					{
						printf("t13.txt=\"AC\"\xFF\xFF\xFF");
					}
				}
			}
			else if(Channel==1)
			{
				Channel=0;
				printf("t1.txt=\"CH1\"\xFF\xFF\xFF");
				switch(voltage_per_grid)
				{
					case 1:
					{
						printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
					}break;
					case 2:
					{					
						printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
					}break;
					case 3:
					{
						printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
					}break;
					case 4:
					{
						printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
					}break;
					case 5:
					{	
						printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
					}break;
					case 6:
					{	
						printf("t5.txt=\"1V\"\xFF\xFF\xFF");
					}break;
//					case 7:
//					{	
//						printf("t5.txt=\"2V\"\xFF\xFF\xFF");
//					}break;
//					case 8:
//					{
//						printf("t5.txt=\"5V\"\xFF\xFF\xFF");
//					}break;
//					case 9:
//					{
//						printf("t5.txt=\"10V\"\xFF\xFF\xFF");
//					}break;
				}
				switch(Ouhe)
				{
					case 0:
					{
						printf("t13.txt=\"DC\"\xFF\xFF\xFF");
					}break;
					case 1:
					{
						printf("t13.txt=\"AC\"\xFF\xFF\xFF");
					}
				}
			
			}
		}break;
		case 10:
		{
			switch(time_per_grid)
			{
				case 6:
				{	
					TIM2->PSC=2-1;
					TIM2->ARR=4-1;
					time_per_grid--;
					printf("t3.txt=\"2us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"125KHz\"\xFF\xFF\xFF");
				}break;
				case 7:
				{	
					TIM2->PSC=2-1;
					TIM2->ARR=10-1;
					time_per_grid--;
					printf("t3.txt=\"5us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"50KHz\"\xFF\xFF\xFF");
				}break;
				case 8:
				{
					TIM2->PSC=2-1;
					TIM2->ARR=20-1;
					time_per_grid--;
					printf("t3.txt=\"10us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"25KHz\"\xFF\xFF\xFF");
				}break;
				case 9:
				{	
					TIM2->PSC=2-1;
					TIM2->ARR=40-1;
					time_per_grid--;
					printf("t3.txt=\"20us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"12.5KHz\"\xFF\xFF\xFF");
				}break;
				case 10:
				{
					TIM2->PSC=2-1;
					TIM2->ARR=100-1;
					time_per_grid--;
					printf("t3.txt=\"50us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"5KHz\"\xFF\xFF\xFF");
				}break;
				case 11:
				{
					TIM2->PSC=2-1;
					TIM2->ARR=200-1;
					time_per_grid--;
					printf("t3.txt=\"100us\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t3.txt=\"2.5KHz\"\xFF\xFF\xFF");
				}break;
			}
		}break;
		case 11:
		{
			if(Channel==0)
			{
				switch(voltage_per_grid)
				{	
					case 1:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid--;
						printf("t5.txt=\"10mV\"\xFF\xFF\xFF");
					}break;
					case 2:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid--;
						printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
					}break;
					case 3:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
						voltage_per_grid--;
						printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
					}break;
					case 4:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
						voltage_per_grid--;
						printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
					}break;
					case 5:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid--;
						printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
						TIM4->CCR3=520;
					}break;
					case 6:
					{
						HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
						voltage_per_grid--;
						printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
						TIM4->CCR3=520;
					}break;
				}
			}
		}break;
		//水平偏移
		case 12:
		{	
			if(offset<320)
			offset+=step;
			
			printf("move t26,%d,0,%d,0,0,30\xFF\xFF\xFF",325-step+offset,325+offset);
			if(measure_time_us(offset)>1000) printf("t7.txt=\"+%.2fms\"\xff\xff\xff",measure_time_ms(offset));
			else if (measure_time_us(offset)>=0) printf("t7.txt=\"+%.2fus\"\xff\xff\xff",measure_time_us(offset));
			else if (measure_time_us(offset)<-1000) printf("t7.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(offset));
			else if (measure_time_us(offset)<0) printf("t7.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(offset));
		}break;
		//垂直偏移
		case 13:
		{
			if(Channel==0)
			{
				offset_ch1+=1;
				if(measure_voltage_V(offset_ch1+128,1)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
				else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
				if(Trigger_state==1|Trigger_state==2)
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1-step)),(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1)));
				printf("move t29,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*(offset_ch1-step)),(int)(181-1.5*(offset_ch1)));
			}
			else
			{	
				offset_ch2+=1;
				if(measure_voltage_V(offset_ch2+128,2)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
				else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
				if(Trigger_state==3|Trigger_state==4)
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2-step)),(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2)));
				printf("move t30,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(181-1.5*(offset_ch2-step)),(int)(181-1.5*(offset_ch2)));
			}
		}break;
		case 14:
		{
			if(Trigger_state==1|Trigger_state==2)
			{
				Trigger_set_offset_ch1+=step;
				if(Trigger_set_offset_ch1>127) Trigger_set_offset_ch1=127;
				if(measure_voltage_V(Trigger_set_offset_ch1+128,1)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch1+128,1));
				else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch1+128,1));
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1-step)),(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1)));

				
			}
			else if (Trigger_state==3|Trigger_state==4)
			{
				Trigger_set_offset_ch2+=step;
				if(Trigger_set_offset_ch2>127) Trigger_set_offset_ch2=127;
				if(measure_voltage_V(Trigger_set_offset_ch2+128,2)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch2+128,2));
				else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch2+128,2));
				printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2-step)),(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2)));
			}
			
		}break;
		case 15:
		{
			if(Channel==0)
			{
				if(Ouhe==0)
				{
					Ouhe=1;
					printf("t13.txt=\"AC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_RESET);
				}
				else
				{
					Ouhe=0;
					printf("t13.txt=\"DC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_SET);
				}
			}
			else if(Channel==1)
			{
				if(Ouhe1==0)
				{
					Ouhe1=1;
					printf("t13.txt=\"AC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_RESET);
				}
				else
				{
					Ouhe1=0;
					printf("t13.txt=\"DC\"\xFF\xFF\xFF");
					HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_SET);
				}
			}
		}break;
		case 16:
			{
				switch(Trigger_state)
				{
					case 1:
					{
						Trigger_state=2;
						printf("t15.txt=\"CH1上\"\xFF\xFF\xFF");
					//	printf("t10.pco=\"yellow\"\xFF\xFF\xFF");
					}break;
					case 2:
					{
						Trigger_state=3;
						printf("t15.txt=\"CH2下\"\xFF\xFF\xFF");
				//		printf("t10.pco=\"blue\"\xFF\xFF\xFF");
					}break;
					case 3:
					{
						Trigger_state=4;
						printf("t15.txt=\"CH2上\"\xFF\xFF\xFF");
					//	printf("t10.pco=\"blue\"\xFF\xFF\xFF");
					}break;
					case 4:
					{
						Trigger_state=1;
						printf("t15.txt=\"CH1下\"\xFF\xFF\xFF");
					//	printf("t10.pco=\"yellow\"\xFF\xFF\xFF");
					}break;
				}
		}break;
	}
}

void renew_menu2()
{
	if(*(__IO uint32_t*)0x08019000!=0xffffffff)
	{
		printf("vis t44,0\xff\xff\xff");
	}
	else printf("vis t44,1\xff\xff\xff");
	printf("t44.txt=\"校准模式\"\xff\xff\xff");
	printf("t50.txt=\"光标模式\"\xff\xff\xff");
	if(cursor_switch!=0) printf("t58.txt=\"光标开\"\xff\xff\xff");
	else printf("t58.txt=\"光标关\"\xff\xff\xff");
	switch(menu2_status)
	{
		case 0:
		{
		}break;
			
		case 1:
		{
			if(cursor_switch!=0)
			printf("t58.txt=\"->光标开\"\xff\xff\xff");
			else printf("t58.txt=\"->光标关\"\xff\xff\xff");
		}break;
		case 2:
		{
			printf("t50.txt=\"->光标模式\"\xff\xff\xff");
		}break;
		case 3:
		{
			printf("t44.txt=\"->校准模式\"\xff\xff\xff");
			
		}break;
	}
}

void switch_parament(int para_flag)
{
	if(para_flag==0&&cursor_switch==1)
	{
		parament_flag=0;
		printf("vis t47,0\xFF\xFF\xFF");
		printf("vis t48,0\xFF\xFF\xFF");
		printf("vis t53,0\xFF\xFF\xFF");
		printf("vis t56,0\xFF\xFF\xFF");
		if(cursor_mode==1)
		{
			printf("t52.txt=\"电压1：\"\xff\xff\xff");
			printf("t51.txt=\"电压2：\"\xff\xff\xff");
		}
//		else if(cursor_mode==2)
//		{
//			printf("t52.txt=\"CH2电压1：\"\xff\xff\xff");
//			printf("t51.txt=\"CH2电压2：\"\xff\xff\xff");
//		}
		else if(cursor_mode==3)
		{
			if(fft_enable==0)
			{
				printf("t52.txt=\"时间1：\"\xff\xff\xff");
				printf("t51.txt=\"时间2：\"\xff\xff\xff");
			}
//			else
//			{
//				printf("t52.txt=\"频率1：\"\xff\xff\xff");
//				printf("t51.txt=\"频率2：\"\xff\xff\xff");
//			}
		}
		return;
	}
}

void renew_menu1()
{		
		printf("t2.txt=\"时间档位\"\xFF\xFF\xFF");
		if(fft_enable==1) printf("t2.txt=\"频率档位\"\xFF\xFF\xFF");
		printf("t4.txt=\"垂直档位\"\xFF\xFF\xFF");
		printf("t6.txt=\"水平偏移\"\xFF\xFF\xFF");
		printf("t8.txt=\"垂直偏移\"\xFF\xFF\xFF");
		printf("t10.txt=\"触发阈值\"\xFF\xFF\xFF");
		printf("t12.txt=\"耦合方式\"\xFF\xFF\xFF");
		printf("t14.txt=\"触发类型\"\xFF\xFF\xFF");
		switch(menu_status)
		{
			case 10:printf("t2.txt=\"->时间档位\"\xFF\xFF\xFF");break;
			case 11:printf("t4.txt=\"->垂直档位\"\xFF\xFF\xFF");break;
			case 12:printf("t6.txt=\"->水平偏移\"\xFF\xFF\xFF");break;
		}
}

void cursor_off()
{	
			printf("vis t16,0\xFF\xFF\xFF");
			printf("vis t17,0\xFF\xFF\xFF");
			printf("vis t18,0\xFF\xFF\xFF");
			printf("vis t19,0\xFF\xFF\xFF");
			printf("vis t20,0\xFF\xFF\xFF");
			printf("vis t21,0\xFF\xFF\xFF");
			printf("vis t22,0\xFF\xFF\xFF");
			printf("vis t23,0\xFF\xFF\xFF");
			printf("vis t24,0\xFF\xFF\xFF");
}

void renew_timeorfreq()
{
	switch(time_per_grid)
	{
//		case 3:
//		{
//			printf("t3.txt=\"500ns\"\xFF\xFF\xFF");
//			if(fft_enable==1) printf("t3.txt=\"5MHz\"\xFF\xFF\xFF");
//		}break;
//		case 4:
//		{
//			printf("t3.txt=\"1us\"\xFF\xFF\xFF");
//			if(fft_enable==1) printf("t3.txt=\"2.5MHz\"\xFF\xFF\xFF");
//		}break;
		case 5:
		{
			printf("t3.txt=\"2us\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"1.25MHz\"\xFF\xFF\xFF");
		}break;
		case 6:
		{
			printf("t3.txt=\"5us\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"500KHz\"\xFF\xFF\xFF");
		}break;
		case 7:
		{
			printf("t3.txt=\"10us\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"250KHz\"\xFF\xFF\xFF");
		}break;
		case 8:
		{
			printf("t3.txt=\"20us\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"125KHz\"\xFF\xFF\xFF");
		}break;
		case 9:
		{
			printf("t3.txt=\"50us\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"50KHz\"\xFF\xFF\xFF");
		}break;
		case 10:
		{
			printf("t3.txt=\"100us\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("tF3.txt=\"25KHz\"\xFF\xFF\xFF");
		}break;
		case 11:
		{
			printf("t3.txt=\"200us\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"12.5KHz\"\xFF\xFF\xFF");
		}break;
		case 12:
		{
			printf("t3.txt=\"500us\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"5KHz\"\xFF\xFF\xFF");
		}break;
		case 13:
		{
			printf("t3.txt=\"1ms\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"2.5KHz\"\xFF\xFF\xFF");
		}break;
		case 14:
		{
			printf("t3.txt=\"2ms\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"1.25KHz\"\xFF\xFF\xFF");
		}break;
		case 15:
		{
			printf("t3.txt=\"5ms\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"500Hz\"\xFF\xFF\xFF");
		}break;
		case 16:
		{
			printf("t3.txt=\"10ms\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"250Hz\"\xFF\xFF\xFF");
		}break;
		case 17:
		{
			printf("t3.txt=\"20ms\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"125Hz\"\xFF\xFF\xFF");
		}break;
		case 18:
		{
			printf("t3.txt=\"50ms\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"50Hz\"\xFF\xFF\xFF");
		}break;
		case 19:
		{
			printf("t3.txt=\"100ms\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"25Hz\"\xFF\xFF\xFF");
		}break;
		case 20:
		{
			printf("t3.txt=\"200ms\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"12.5Hz\"\xFF\xFF\xFF");
		}break;
	}
}

