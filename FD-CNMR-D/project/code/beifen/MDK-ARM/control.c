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

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{		
	if(CH2_status==1)
	{
		for(;j<651;j++,i++)
		{
			printf("%c",ad2[i-325]);
		}
		printf("\x01\xff\xff\xff");//确保透传结束
	}
	else if(CH1_status==1)
	{
		for(;j<651;j++,i++)
		{
			printf("%c",ad1[i-325]);
		}
		printf("\x01\xff\xff\xff");//确保透传结束
	}
	//renew_data();
	//菜单——按钮
	if(GPIO_Pin==GPIO_PIN_15)
	{
		HAL_Delay(20);
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_15)==GPIO_PIN_SET)
		{
			HAL_Delay(500);
			if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_15)==GPIO_PIN_SET)
			{
				while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_15)==GPIO_PIN_SET)
				{
				
				}
				//printf("changan\r\n");
				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
				printf("changan\xFF\xFF\xFF");
				menu_status=0;
				printf("t0.txt=\"通道\"\xFF\xFF\xFF");
				printf("t2.txt=\"时间档位\"\xFF\xFF\xFF");
				if(fft_enable==1) printf("t2.txt=\"频率档位\"\xFF\xFF\xFF");
				printf("t4.txt=\"垂直档位\"\xFF\xFF\xFF");
				printf("t6.txt=\"水平偏移\"\xFF\xFF\xFF");
				printf("t8.txt=\"垂直偏移\"\xFF\xFF\xFF");
				printf("t10.txt=\"触发阈值\"\xFF\xFF\xFF");
				printf("t12.txt=\"耦合方式\"\xFF\xFF\xFF");
				printf("t14.txt=\"触发类型\"\xFF\xFF\xFF");
			}
			else
			{
				//printf("duanan\r\n");
				for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
				printf("duan\xFF\xFF\xFF");
				switch(menu_status)
				{
					//待机
					case 0:
					{
						menu_status=1;
						printf("t0.txt=\"*通道\"\xFF\xFF\xFF");
					}break;
					//通道
					case 1:
					{
						menu_status+=8;
						printf("t0.txt=\"->通道\"\xFF\xFF\xFF");
					}break;
					//时间档位
					case 2:
					{
						menu_status+=8;
						printf("t2.txt=\"->时间档位\"\xFF\xFF\xFF");
						if(fft_enable==1) printf("t2.txt=\"->频率档位\"\xFF\xFF\xFF");
					}break;
					//垂直档位
					case 3:
					{
						menu_status+=8;
						printf("t4.txt=\"->垂直档位\"\xFF\xFF\xFF");
					}break;
					//水平偏移
					case 4:
					{
						menu_status+=8;
						printf("t6.txt=\"->水平偏移\"\xFF\xFF\xFF");
					}break;
					//垂直偏移
					case 5:
					{
						menu_status+=8;
						printf("t8.txt=\"->垂直偏移\"\xFF\xFF\xFF");
					}break;
					//触发阈值
					case 6:
					{
						menu_status+=8;
						printf("t10.txt=\"->触发阈值\"\xFF\xFF\xFF");
					}break;
					//耦合方式
					case 7:
					{
						menu_status+=8;
						printf("t12.txt=\"->耦合方式\"\xFF\xFF\xFF");
					}break;
					//触发类型
					case 8:
					{
						menu_status+=8;
						printf("t14.txt=\"->触发类型\"\xFF\xFF\xFF");
					}break;
					//通道
					case 9:
					{
						menu_status-=8;
						printf("t0.txt=\"*通道\"\xFF\xFF\xFF");
					}break;
					//时间档位
					case 10:
					{
						menu_status-=8;
						printf("t2.txt=\"*时间档位\"\xFF\xFF\xFF");
					}break;
					//垂直档位
					case 11:
					{
						menu_status-=8;
						printf("t4.txt=\"*垂直档位\"\xFF\xFF\xFF");
					}break;
					//水平偏移
					case 12:
					{
						menu_status-=8;
						printf("t6.txt=\"*水平偏移\"\xFF\xFF\xFF");
					}break;
					//垂直偏移
					case 13:
					{
						menu_status-=8;
						printf("t8.txt=\"*垂直偏移\"\xFF\xFF\xFF");
					}break;
					//触发阈值
					case 14:
					{
						menu_status-=8;
						printf("t10.txt=\"*触发阈值\"\xFF\xFF\xFF");
					}break;
					//耦合方式
					case 15:
					{
						menu_status-=8;
						printf("t12.txt=\"*耦合方式\"\xFF\xFF\xFF");
					}break;
					//触发类型
					case 16:
					{
						menu_status-=8;
						printf("t14.txt=\"*触发类型\"\xFF\xFF\xFF");
					}break;
				}
			}
		}
	}
	//菜单——旋转编码器
	//顺时针转
	else if(GPIO_Pin==GPIO_PIN_1)
	{	
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_2)==GPIO_PIN_RESET) 
		{
			printf("shunshizheng\xFF\xFF\xFF");
			//HAL_Delay(50);
			//for(int i=0;i<200;i++) printf("\x01\xff\xff\xff");//确保透传结束
			switch(menu_status)
			{
				case 1:
				{
					menu_status+=1;
					printf("t0.txt=\"通道\"\xFF\xFF\xFF");
					printf("t2.txt=\"*时间档位\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t2.txt=\"*频率档位\"\xFF\xFF\xFF");
				}break;
				case 2:
				{
					menu_status+=1;
					printf("t2.txt=\"时间档位\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t2.txt=\"频率档位\"\xFF\xFF\xFF");
					printf("t4.txt=\"*垂直档位\"\xFF\xFF\xFF");
				}break;
				case 3:
				{
					menu_status+=1;
					printf("t4.txt=\"垂直档位\"\xFF\xFF\xFF");
					printf("t6.txt=\"*水平偏移\"\xFF\xFF\xFF");
				}break;
				case 4:
				{
					menu_status+=1;
					printf("t6.txt=\"水平偏移\"\xFF\xFF\xFF");
					printf("t8.txt=\"*垂直偏移\"\xFF\xFF\xFF");
				}break;
				case 5:
				{
					menu_status+=1;
					printf("t8.txt=\"垂直偏移\"\xFF\xFF\xFF");
					printf("t10.txt=\"*触发阈值\"\xFF\xFF\xFF");
				}break;
				case 6:
				{
					menu_status+=1;
					printf("t10.txt=\"触发阈值\"\xFF\xFF\xFF");
					printf("t12.txt=\"*耦合方式\"\xFF\xFF\xFF");
				}break;
				case 7:
				{
					menu_status+=1;
					printf("t12.txt=\"耦合方式\"\xFF\xFF\xFF");
					printf("t14.txt=\"*触发类型\"\xFF\xFF\xFF");
				}break;
				case 8:
				{
					menu_status=1;
					printf("t14.txt=\"触发类型\"\xFF\xFF\xFF");
					printf("t0.txt=\"*通道\"\xFF\xFF\xFF");
				}break;
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
						case 3:
						{
							//sample_50Mhz();
							time_per_grid++;
							printf("t3.txt=\"10us\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"250MHz\"\xFF\xFF\xFF");
						}break;
						case 4:
						{	
							TIM2->PSC=2-1;
							TIM2->ARR=4-1;
							time_per_grid++;
							printf("t3.txt=\"20us\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"100Hz\"\xFF\xFF\xFF");
							HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,2800);
						}break;
						case 5:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=10-1;
							time_per_grid++;
							printf("t3.txt=\"50us\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"50KMHz\"\xFF\xFF\xFF");
						}break;
						case 6:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=20-1;
							time_per_grid++;
							printf("t3.txt=\"100us\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"25KHz\"\xFF\xFF\xFF");
						}break;
						case 7:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=40-1;
							time_per_grid++;
							printf("t3.txt=\"200us\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"12.5KHz\"\xFF\xFF\xFF");
						}break;
						case 8:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=100-1;
							time_per_grid++;
							printf("t3.txt=\"500us\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"5KHz\"\xFF\xFF\xFF");
						}break;
						case 9:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=200-1;
							time_per_grid++;
							printf("t3.txt=\"1ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"2.5KHz\"\xFF\xFF\xFF");
						}break;
						case 10:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=400-1;
							time_per_grid++;
							printf("t3.txt=\"2ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"1.25KHz\"\xFF\xFF\xFF");
						}break;
						case 11:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=1000-1;
							time_per_grid++;
							printf("t3.txt=\"5ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"500Hz\"\xFF\xFF\xFF");
						}break;
						case 12:
						{
							TIM2->PSC=500-1;
							TIM2->ARR=8-1;
							time_per_grid++;
							printf("t3.txt=\"10ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"250Hz\"\xFF\xFF\xFF");
						}break;
						case 13:
						{	
							TIM2->PSC=500-1;
							TIM2->ARR=16-1;
							time_per_grid++;
							printf("t3.txt=\"20ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"125Hz\"\xFF\xFF\xFF");
						}break;
						case 14:
						{
							TIM2->PSC=500-1;
							TIM2->ARR=40-1;
							time_per_grid++;
							printf("t3.txt=\"50ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"50Hz\"\xFF\xFF\xFF");
						}break;
						case 15:
						{	
							TIM2->PSC=500-1;
							TIM2->ARR=80-1;
							time_per_grid++;
							printf("t3.txt=\"100ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"25Hz\"\xFF\xFF\xFF");
						}break;
						case 16:
						{	
							TIM2->PSC=500-1;
							TIM2->ARR=160-1;
							time_per_grid++;
							printf("t3.txt=\"200ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"12.5Hz\"\xFF\xFF\xFF");
						}break;
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
							}break;
							case 4:
							{	
								HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
								voltage_per_grid++;
								printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
							}break;
							case 5:
							{	
								HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
								voltage_per_grid++;
								printf("t5.txt=\"1V\"\xFF\xFF\xFF");
							}break;
							case 6:
							{	
								HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
								voltage_per_grid++;
								printf("t5.txt=\"2V\"\xFF\xFF\xFF");
							}break;
							case 7:
							{
								HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
								voltage_per_grid++;
								printf("t5.txt=\"5V\"\xFF\xFF\xFF");
							}break;
							case 8:
							{
								HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
								voltage_per_grid++;
								printf("t5.txt=\"10V\"\xFF\xFF\xFF");
							}break;
	//						case 9:
	//						{
	//							voltage_per_grid=0;
	//							printf("t5.txt=\"10mV\"\xFF\xFF\xFF");
	//						}break;
						}

					}
					if(Channel==1)
					{
						switch(voltage_per_grid_1)
						{
							case 0:
							{
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
								voltage_per_grid_1++;
								printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
							}break;
							case 1:
							{
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
								voltage_per_grid_1++;
								printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
							}break;
							case 2:
							{
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
								voltage_per_grid_1++;
								printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
							}break;
							case 3:
							{
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
								voltage_per_grid_1++;
								printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
							}break;
							case 4:
							{	
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
								voltage_per_grid_1++;
								printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
							}break;
							case 5:
							{	
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
								voltage_per_grid_1++;
								printf("t5.txt=\"1V\"\xFF\xFF\xFF");
							}break;
							case 6:
							{	
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
								voltage_per_grid_1++;
								printf("t5.txt=\"2V\"\xFF\xFF\xFF");
							}break;
							case 7:
							{
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
								voltage_per_grid_1++;
								printf("t5.txt=\"5V\"\xFF\xFF\xFF");
							}break;
							case 8:
							{
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
								voltage_per_grid_1++;
								printf("t5.txt=\"10V\"\xFF\xFF\xFF");
							}break;
	//						case 9:
	//						{
	//							voltage_per_grid=0;
	//							printf("t5.txt=\"10mV\"\xFF\xFF\xFF");
	//						}break;
						}
					}
				}break;
					
				case 12:
				{
					offset+=5;
					if(offset<=325)
					printf("move t26,%d,0,%d,0,0,30\xFF\xFF\xFF",325-5+offset,325+offset);
					if(measure_time_us(offset)>1000) printf("t7.txt=\"+%.2fms\"\xff\xff\xff",measure_time_ms(offset));
					else if (measure_time_us(offset)>=0) printf("t7.txt=\"+%.2fus\"\xff\xff\xff",measure_time_us(offset));
					else printf("t7.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(offset));
				}break;
				case 13:
				{
					if(Channel==0)
					{
						offset_ch1+=1;
						if(measure_voltage_V(offset_ch1+128,1)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
						else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
					}
					else
					{	
						offset_ch2+=1;
						if(measure_voltage_V(offset_ch2+128,2)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
						else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
					}
				}break;
				case 14:
				{
					Trigger_set_offset+=5;
					if(Trigger_set_offset>127) Trigger_set_offset=127;
					if(Channel==0)
					{
						if(measure_voltage_V(Trigger_set_offset+128,1)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset+128,1));
						else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset+128,1));
					}
					else
					{
						if(measure_voltage_V(Trigger_set_offset+128,2)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset+128,2));
						else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset+128,2));
					}
					printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1-1.5*Trigger_set_offset),(int)(192-1.5*Trigger_set_offset));
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
	}
	//逆时针转
	else if(GPIO_Pin==GPIO_PIN_2)
	{	
		if(HAL_GPIO_ReadPin(GPIOE,GPIO_PIN_1)==GPIO_PIN_RESET) 
		{
			//HAL_Delay(50);
			//for(int i=0;i<200;i++) printf("\x01\xff\xff\xff");//确保透传结束
			//delay_ms(10);
			printf("nishizheng\xFF\xFF\xFF");
			switch(menu_status)
			{
				case 3:
				{
					menu_status-=1;
					printf("t4.txt=\"垂直档位\"\xFF\xFF\xFF");
					printf("t2.txt=\"*时间档位\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t2.txt=\"*频率档位\"\xFF\xFF\xFF");
				}break;
				case 4:
				{
					menu_status-=1;
					printf("t6.txt=\"水平偏移\"\xFF\xFF\xFF");
					printf("t4.txt=\"*垂直档位\"\xFF\xFF\xFF");
				}break;
				case 5:
				{
					menu_status-=1;
					printf("t8.txt=\"垂直偏移\"\xFF\xFF\xFF");
					printf("t6.txt=\"*水平偏移\"\xFF\xFF\xFF");
				}break;
				case 6:
				{
					menu_status-=1;
					printf("t10.txt=\"触发阈值\"\xFF\xFF\xFF");
					printf("t8.txt=\"*垂直偏移\"\xFF\xFF\xFF");
				}break;
				case 7:
				{
					menu_status-=1;
					printf("t12.txt=\"耦合方式\"\xFF\xFF\xFF");
					printf("t10.txt=\"*触发阈值\"\xFF\xFF\xFF");
				}break;
				case 8:
				{
					menu_status-=1;
					printf("t14.txt=\"触发类型\"\xFF\xFF\xFF");
					printf("t12.txt=\"*耦合方式\"\xFF\xFF\xFF");
				}break;
				case 1:
				{
					menu_status=8;
					printf("t0.txt=\"通道\"\xFF\xFF\xFF");
					printf("t14.txt=\"*触发类型\"\xFF\xFF\xFF");
				}break;
				case 2:
				{
					menu_status-=1;
					printf("t2.txt=\"时间档位\"\xFF\xFF\xFF");
					if(fft_enable==1) printf("t2.txt=\"频率档位\"\xFF\xFF\xFF");
					printf("t0.txt=\"*通道\"\xFF\xFF\xFF");
				}break;
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
							printf("t3.txt=\"20us\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"125KHz\"\xFF\xFF\xFF");
						}break;
						case 7:
						{	
							TIM2->PSC=2-1;
							TIM2->ARR=10-1;
							time_per_grid--;
							printf("t3.txt=\"50us\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"50KHz\"\xFF\xFF\xFF");
						}break;
						case 8:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=20-1;
							time_per_grid--;
							printf("t3.txt=\"100us\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"25KHz\"\xFF\xFF\xFF");
						}break;
						case 9:
						{	
							TIM2->PSC=2-1;
							TIM2->ARR=40-1;
							time_per_grid--;
							printf("t3.txt=\"200us\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"12.5KHz\"\xFF\xFF\xFF");
						}break;
						case 10:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=100-1;
							time_per_grid--;
							printf("t3.txt=\"500us\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"5KHz\"\xFF\xFF\xFF");
						}break;
						case 11:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=200-1;
							time_per_grid--;
							printf("t3.txt=\"1ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"2.5KHz\"\xFF\xFF\xFF");
						}break;
						case 12:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=400-1;
							time_per_grid--;
							printf("t3.txt=\"2ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"1.25KHz\"\xFF\xFF\xFF");
						}break;
						case 13:
						{
							TIM2->PSC=2-1;
							TIM2->ARR=1000-1;
							time_per_grid--;
							printf("t3.txt=\"5ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"500Hz\"\xFF\xFF\xFF");
						}break;
						case 14:
						{
							TIM2->PSC=500-1;
							TIM2->ARR=8-1;
							time_per_grid--;
							printf("t3.txt=\"10ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"250KHz\"\xFF\xFF\xFF");
						}break;
						case 15:
						{
							TIM2->PSC=500-1;
							TIM2->ARR=16-1;
							time_per_grid--;
							printf("t3.txt=\"20ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"125Hz\"\xFF\xFF\xFF");
						}break;
						case 16:
						{
							TIM2->PSC=500-1;
							TIM2->ARR=40-1;
							time_per_grid--;
							printf("t3.txt=\"50ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"50Hz\"\xFF\xFF\xFF");
						}break;
						case 17:
						{
							TIM2->PSC=500-1;
							TIM2->ARR=80-1;
							time_per_grid--;
							printf("t3.txt=\"100ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"25Hz\"\xFF\xFF\xFF");
						}break;
						case 18:
						{
							TIM2->PSC=500-1;
							TIM2->ARR=160-1;
							time_per_grid--;
							printf("t3.txt=\"200ms\"\xFF\xFF\xFF");
							if(fft_enable==1) printf("t3.txt=\"12.5Hz\"\xFF\xFF\xFF");
						}break;
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
								HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
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
							}break;
							case 6:
							{
								HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
								voltage_per_grid--;
								printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
							}break;
							case 7:
							{
								HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
								voltage_per_grid--;
								printf("t5.txt=\"1V\"\xFF\xFF\xFF");
							}break;
							case 8:
							{	
								HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
								voltage_per_grid--;
								printf("t5.txt=\"2V\"\xFF\xFF\xFF");
							}break;
							case 9:
							{
								HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
								voltage_per_grid--;
								printf("t5.txt=\"5V\"\xFF\xFF\xFF");
							}break;
	//						case 0:
	//						{
	//							voltage_per_grid=9;
	//							printf("t5.txt=\"10V\"\xFF\xFF\xFF");
	//						}break;
						}
					
					}
					else if(Channel==1)
					{
						switch(voltage_per_grid_1)
						{	
							case 1:
							{
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
								voltage_per_grid_1--;
								printf("t5.txt=\"10mV\"\xFF\xFF\xFF");
							}break;
							case 2:
							{
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
								voltage_per_grid_1--;
								printf("t5.txt=\"20mV\"\xFF\xFF\xFF");
							}break;
							case 3:
							{
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
								voltage_per_grid_1--;
								printf("t5.txt=\"50mV\"\xFF\xFF\xFF");
							}break;
							case 4:
							{
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
								voltage_per_grid_1--;
								printf("t5.txt=\"100mV\"\xFF\xFF\xFF");
							}break;
							case 5:
							{
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
								voltage_per_grid_1--;
								printf("t5.txt=\"200mV\"\xFF\xFF\xFF");
							}break;
							case 6:
							{
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
								voltage_per_grid_1--;
								printf("t5.txt=\"500mV\"\xFF\xFF\xFF");
							}break;
							case 7:
							{
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
								voltage_per_grid_1--;
								printf("t5.txt=\"1V\"\xFF\xFF\xFF");
							}break;
							case 8:
							{	
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
								voltage_per_grid_1--;
								printf("t5.txt=\"2V\"\xFF\xFF\xFF");
							}break;
							case 9:
							{
								HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
								HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
								HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET); 
								voltage_per_grid_1--;
								printf("t5.txt=\"5V\"\xFF\xFF\xFF");
							}break;
	//						case 0:
	//						{
	//							voltage_per_grid=9;
	//							printf("t5.txt=\"10V\"\xFF\xFF\xFF");
	//						}break;
						}
					}
				}break;
				case 12:
				{
					offset-=5;
					if(offset>=-325)
					printf("move t26,%d,0,%d,0,0,30\xFF\xFF\xFF",325+5+offset,325+offset);
					if(measure_time_us(offset)>1000) printf("t7.txt=\"+%.2fms\"\xff\xff\xff",measure_time_ms(offset));
					else if (measure_time_us(offset)>=0) printf("t7.txt=\"+%.2fus\"\xff\xff\xff",measure_time_us(offset));
					else printf("t7.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(offset));
				}break;
				case 13:
				{	
					if(Channel==0)
					{
						offset_ch1-=1;
						if(measure_voltage_V(offset_ch1+128,1)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
						else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
					}
					else
					{	
						offset_ch2-=1;
						if(measure_voltage_V(offset_ch2+128,2)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
						else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
					}
				}break;
				case 14:
				{
					Trigger_set_offset-=5;
					if(Trigger_set_offset<-128) Trigger_set_offset=-128;
					if(Channel==0)
					{
						if(measure_voltage_V(Trigger_set_offset+128,1)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset+128,1));
						else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset+128,1));
					}
					else
					{
						if(measure_voltage_V(Trigger_set_offset+128,2)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset+128,2));
						else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset+128,2));
					}
					printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192+1-1.5*Trigger_set_offset),(int)(192-1.5*Trigger_set_offset));
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
	}
	
	//曲线——按钮
	else if(GPIO_Pin==GPIO_PIN_3)
	{
		HAL_Delay(20);
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_3)==GPIO_PIN_SET)
		{
			HAL_Delay(500);
			if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_3)==GPIO_PIN_SET)
			{
				while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_3)==GPIO_PIN_SET)
				{
				
				}
				//printf("changan\r\n");
				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
				if(cursor_status==1)
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
					printf("vis t24,0\xFF\xFF\xFF");
				}
				else
				{
					cursor_status=1;
					hengzong=0;
					cursor_num=0;
					printf("t24.txt=\"选横纵：横\"\xFF\xFF\xFF");
				}
			}
			else
			{
				//printf("duanan\r\n");
				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
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
						printf("vis t24,1\xFF\xFF\xFF");
					}break;
					case 1:
					{
						cursor_status=2;
						printf("t24.txt=\"选通道：1\"\xFF\xFF\xFF");
					}break;
					case 2:
					{
						cursor_status=3;
						if(hengzong==0)
						{
							if(cursor_num==0)
							{
								printf("t24.txt=\"选中：横1\"\xFF\xFF\xFF");
							}
							else if(cursor_num==1)
							{
								printf("t24.txt=\"选中：横2\"\xFF\xFF\xFF");
							}
						}
						else
						{
							if(cursor_num==0)
							{
								printf("t24.txt=\"选中：纵1\"\xFF\xFF\xFF");
							}
							else if(cursor_num==1)
							{
								printf("t24.txt=\"选中：纵2\"\xFF\xFF\xFF");
							}
						}
					}break;
				}
			}
		}
	}
	//曲线——编码器
	else if(GPIO_Pin==GPIO_PIN_4)
	{
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_5)==GPIO_PIN_RESET)
		{
			//for(int i=0;i<700;i++) printf("\x01\xff\xff\xff");//确保透传结束
			printf("shunshizheng\xFF\xFF\xFF");
			switch(cursor_status)
			{
				case 1:
				{
					if(hengzong==0)
					{
						hengzong=1;
						printf("t24.txt=\"选横纵：纵\"\xFF\xFF\xFF");
					}
					else if(hengzong==1)
					{
						hengzong=0;
						printf("t24.txt=\"选横纵：横\"\xFF\xFF\xFF");
					}
				}break;
				case 2:
				{
					if(cursor_num==0)
					{
						cursor_num=1;
						printf("t24.txt=\"选通道：2\"\xFF\xFF\xFF");
					}
					else
					{
						cursor_num=0;
						printf("t24.txt=\"选通道：1\"\xFF\xFF\xFF");
					}
				}break;
				case 3:
				{
					if(hengzong==0)
						{
							if(cursor_num==0)
							{
								//printf("t24.txt=\"选中：横1\"\xFF\xFF\xFF");
								printf("move t18,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1+step);
								printf("move t20,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1+step);
								y1+=step;
							}
							else if(cursor_num==1)
							{
								//printf("t24.txt=\"选中：横2\"\xFF\xFF\xFF");
								printf("move t19,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2+step);
								printf("move t21,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2+step);
								y2+=5;
							}
						}
						else
						{
							if(cursor_num==0)
							{
								//printf("t24.txt=\"选中：纵1\"\xFF\xFF\xFF");
								printf("move t16,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1+step);
								printf("move t22,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1+step);
								x1+=step;
							}
							else if(cursor_num==1)
							{
								//printf("t24.txt=\"选中：纵2\"\xFF\xFF\xFF");
								printf("move t17,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2+step);
								printf("move t23,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2+step);
								x2+=step;
							}
						}
				}break;
			}
		}
	}
	else if(GPIO_Pin==GPIO_PIN_5)
	{
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_4)==GPIO_PIN_RESET)
		{
			//for(int i=0;i<700;i++) printf("\x01\xff\xff\xff");//确保透传结束
			printf("nishizheng\xFF\xFF\xFF");
			switch(cursor_status)
			{
				case 1:
				{
					if(hengzong==0)
					{
						hengzong=1;
						printf("t24.txt=\"选横纵：纵\"\xFF\xFF\xFF");
					}
					else
					{
						hengzong=0;
						printf("t24.txt=\"选横纵：横\"\xFF\xFF\xFF");
					}
				}break;
				case 2:
				{
					if(cursor_num==0)
					{
						cursor_num=1;
						printf("t24.txt=\"选通道：2\"\xFF\xFF\xFF");
					}
					else
					{
						cursor_num=0;
						printf("t24.txt=\"选通道：1\"\xFF\xFF\xFF");
					}
				}break;
				case 3:
				{
					if(hengzong==0)
						{
							if(cursor_num==0)
							{
								//printf("t24.txt=\"选中：横1\"\xFF\xFF\xFF");
								printf("move t18,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1-step);
								printf("move t20,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1-step);
								y1-=step;
							}
							else if(cursor_num==1)
							{
								//printf("t24.txt=\"选中：横2\"\xFF\xFF\xFF");
								printf("move t19,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2-step);
								printf("move t21,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2-step);
								y2-=step;
							}
						}
						else
						{
							if(cursor_num==0)
							{
								//printf("t24.txt=\"选中：纵1\"\xFF\xFF\xFF");
								printf("move t16,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1-step);
								printf("move t22,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1-step);
								x1-=step;
							}
							else if(cursor_num==1)
							{
								//printf("t24.txt=\"选中：纵2\"\xFF\xFF\xFF");
								printf("move t17,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2-step);
								printf("move t23,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2-step);
								x2-=step;
							}
						}
				}break;
			}
		}
	}
	//菜单2-按钮
	else if(GPIO_Pin==GPIO_PIN_6)
	{
		HAL_Delay(20);
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_6)==GPIO_PIN_SET)
		{
			HAL_Delay(500);
			if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_6)==GPIO_PIN_SET)
			{
				while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_6)==GPIO_PIN_SET)
				{
				
				}
				//changan
				printf("vis t44,0\xFF\xFF\xFF");
				printf("vis t45,0\xFF\xFF\xFF");
				printf("vis t46,0\xFF\xFF\xFF");
				printf("vis t49,0\xFF\xFF\xFF");
				printf("vis t50,0\xFF\xFF\xFF");
				menu2_status=0;
			}
			else 
			{
			 //duanan
				switch(menu2_status)
				{
					case 0:
					{
						menu2_status=1;
						printf("vis t44,1\xFF\xFF\xFF");
						printf("vis t45,1\xFF\xFF\xFF");
						printf("vis t46,1\xFF\xFF\xFF");
						printf("vis t49,1\xFF\xFF\xFF");
						printf("vis t50,1\xFF\xFF\xFF");
						printf("t44.txt=\"->零点校准\"\xff\xff\xff");
						if(xy_enable==0) printf("t45.txt=\"Y-T\"\xff\xff\xff");
						else printf("t45.txt=\"X-Y\"\xff\xff\xff");
						switch(Trigger_ANS)
						{
							case 0:
							{
								printf("t46.txt=\"AUTO\"\xff\xff\xff");
							}break;
							case 1:
							{
								printf("t46.txt=\"NROMAL\"\xff\xff\xff");
							}break;
							case 2:
							{
								printf("t46.txt=\"SINGLE\"\xff\xff\xff");
							}break;
						}
						if(fft_enable==1) printf("t49.txt=\"FFT开\"\xff\xff\xff");
						else printf("t49.txt=\"FFT关\"\xff\xff\xff");
						if(get_freq_enable==0) printf("t50.txt=\"测频关\"\xff\xff\xff");
						else printf("t50.txt=\"测频开\"\xff\xff\xff");
					}break;
					case 1:
					{
						caliboration(&caliboration_ch1,&caliboration_ch2);
					}break;
					case 2:
					{
						if(xy_enable==0)
						{
							xy_enable=1;
							CH1_enable=0;
							CH2_enable=0;
							printf("cle 1,255\xff\xff\xff");
							printf("t45.txt=\"->X-Y\"\xff\xff\xff");
						}
						else
						{
							xy_enable=0;
							CH1_enable=1;
							CH2_enable=1;
							HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,2800);
							printf("t45.txt=\"->Y-T\"\xff\xff\xff");
						}
					}break;
					case 3:
					{
						switch(Trigger_ANS)
						{
							case 0:
							{
								Trigger_ANS++;
								printf("t46.txt=\"->NROMAL\"\xff\xff\xff");
							}break;
							case 1:
							{
								Trigger_ANS++;
								single_flag=1;
								printf("t46.txt=\"->SINGLE\"\xff\xff\xff");
							}break;
							case 2:
							{
								Trigger_ANS=0;
								printf("t46.txt=\"->AUTO\"\xff\xff\xff");
							}break;
						}
					}break;
					case 4:
					{
						if(fft_enable==1)
						{
							fft_enable=0;
							CH1_enable=1;
							CH2_enable=1;
							HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,2800);
							printf("t49.txt=\"->FFT关\"\xff\xff\xff");
						}
						else
						{
							fft_enable=1;
							CH1_enable=0;
							CH2_enable=0;
							xy_enable=0;
							printf("t45.txt=\"X-Y\"\xff\xff\xff");
							printf("t49.txt=\"->FFT开\"\xff\xff\xff");
							printf("cle 1,255\xff\xff\xff");
						}
					}break;
					case 5:
					{
						if(get_freq_enable==0)
						{
							get_freq_enable=1;
							printf("cle 1,255\xff\xff\xff");
							printf("t50.txt=\"->测频开\"\xff\xff\xff");
							HAL_TIM_Base_Stop(&htim3);
							HAL_TIM_Base_Start_IT(&htim5);
							HAL_TIM_Base_Start_IT(&htim4);
						}
						else
						{
							get_freq_enable=0;
							printf("t50.txt=\"->测频关\"\xff\xff\xff");
							HAL_TIM_Base_Start_IT(&htim3);
							HAL_TIM_Base_Stop_IT(&htim5);
							HAL_TIM_Base_Stop_IT(&htim4);
						}
					}break;
					case 6:
					{
						if(parament_flag==0)
						{
							parament_flag=1;
							printf("vis t27,0\xFF\xFF\xFF");
							printf("vis t28,0\xFF\xFF\xFF");
							printf("vis t29,0\xFF\xFF\xFF");
							printf("vis t30,0\xFF\xFF\xFF");
							printf("vis t31,0\xFF\xFF\xFF");
							printf("vis t32,0\xFF\xFF\xFF");
							printf("vis t33,0\xFF\xFF\xFF");
							printf("vis t34,0\xFF\xFF\xFF");
							printf("vis t35,0\xFF\xFF\xFF");
							printf("vis t36,0\xFF\xFF\xFF");
							printf("vis t37,0\xFF\xFF\xFF");
							printf("vis t38,0\xFF\xFF\xFF");
							printf("vis t39,0\xFF\xFF\xFF");
							printf("vis t40,0\xFF\xFF\xFF");
							printf("vis t41,0\xFF\xFF\xFF");
							printf("vis t42,0\xFF\xFF\xFF");
							printf("vis t43,0\xFF\xFF\xFF");
							printf("vis t47,1\xFF\xFF\xFF");
							printf("vis t48,1\xFF\xFF\xFF");
							printf("vis t51,1\xFF\xFF\xFF");
							printf("vis t52,1\xFF\xFF\xFF");
							printf("vis t53,1\xFF\xFF\xFF");
							printf("vis t54,1\xFF\xFF\xFF");
							printf("vis t55,1\xFF\xFF\xFF");
							printf("vis t56,1\xFF\xFF\xFF");
						}
						else
						{
							parament_flag=0;
							printf("vis t27,1\xFF\xFF\xFF");
							printf("vis t28,1\xFF\xFF\xFF");
							printf("vis t29,1\xFF\xFF\xFF");
							printf("vis t30,1\xFF\xFF\xFF");
							printf("vis t31,1\xFF\xFF\xFF");
							printf("vis t32,1\xFF\xFF\xFF");
							printf("vis t33,1\xFF\xFF\xFF");
							printf("vis t34,1\xFF\xFF\xFF");
							printf("vis t35,1\xFF\xFF\xFF");
							printf("vis t36,1\xFF\xFF\xFF");
							printf("vis t37,1\xFF\xFF\xFF");
							printf("vis t38,1\xFF\xFF\xFF");
							printf("vis t39,1\xFF\xFF\xFF");
							printf("vis t40,1\xFF\xFF\xFF");
							printf("vis t41,1\xFF\xFF\xFF");
							printf("vis t42,1\xFF\xFF\xFF");
							printf("vis t43,1\xFF\xFF\xFF");
							printf("vis t47,0\xFF\xFF\xFF");
							printf("vis t48,0\xFF\xFF\xFF");
							printf("vis t51,0\xFF\xFF\xFF");
							printf("vis t52,0\xFF\xFF\xFF");
							printf("vis t53,0\xFF\xFF\xFF");
							printf("vis t54,0\xFF\xFF\xFF");
							printf("vis t55,0\xFF\xFF\xFF");
							printf("vis t56,0\xFF\xFF\xFF");
						}
					}break;
				}
			}
		}
	}
	//菜单2—顺时针
	else if(GPIO_Pin==GPIO_PIN_7)
	{	
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_8)==GPIO_PIN_RESET) 
		{
			printf("shunshizheng\xFF\xFF\xFF");
			switch(menu2_status)
			{
				case 1:
				{
					menu2_status++;
					printf("t44.txt=\"零点校准\"\xff\xff\xff");
					if(xy_enable==0)
					printf("t45.txt=\"->Y-T\"\xff\xff\xff");
					else printf("t45.txt=\"->X-Y\"\xff\xff\xff");
				}break;
				case 2:
				{
					menu2_status++;
					printf("t44.txt=\"零点校准\"\xff\xff\xff");
					if(xy_enable==0)
					printf("t45.txt=\"Y-T\"\xff\xff\xff");
					else printf("t45.txt=\"X-Y\"\xff\xff\xff");
					switch(Trigger_ANS)
					{
						case 0:
						{
							printf("t46.txt=\"->AUTO\"\xff\xff\xff");
						}break;
						case 1:
						{
							printf("t46.txt=\"->NROMAL\"\xff\xff\xff");
						}break;
						case 2:
						{
							printf("t46.txt=\"->SINGLE\"\xff\xff\xff");
						}break;
					}
				}break;
				case 3:
				{
					menu2_status++;
					switch(Trigger_ANS)
					{
						case 0:
						{
							printf("t46.txt=\"AUTO\"\xff\xff\xff");
						}break;
						case 1:
						{
							printf("t46.txt=\"NROMAL\"\xff\xff\xff");
						}break;
						case 2:
						{
							printf("t46.txt=\"SINGLE\"\xff\xff\xff");
						}break;
					}
					if(fft_enable==1)
					{
						printf("t49.txt=\"->FFT开\"\xff\xff\xff");
					}
					else printf("t49.txt=\"->FFT关\"\xff\xff\xff");
				}break;
				case 4:
				{
					menu2_status++;
					if(fft_enable==1)
					{
						printf("t49.txt=\"FFT开\"\xff\xff\xff");
					}
					else printf("t49.txt=\"FFT关\"\xff\xff\xff");
					if(get_freq_enable==1) printf("t50.txt=\"->测频开\"\xff\xff\xff");
					else printf("t50.txt=\"->测频关\"\xff\xff\xff");
				}break;
				case 5:
				{
					menu2_status++;
					if(get_freq_enable==1) printf("t50.txt=\"测频开\"\xff\xff\xff");
					else printf("t50.txt=\"测频关\"\xff\xff\xff");
					printf("t57.txt=\"->切换参数\"\xff\xff\xff");
				}
			}
		}
	}
	//菜单2-逆时针
	else if(GPIO_Pin==GPIO_PIN_8)
	{	
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_7)==GPIO_PIN_RESET) 
		{
			printf("nishizheng\xFF\xFF\xFF");
			switch(menu2_status)
			{
//				case 1:
//				{
//					menu2_status=5;
//				}break;
				case 2:
				{
					menu2_status--;
					printf("t44.txt=\"->零点校准\"\xff\xff\xff");
					if(xy_enable==0)
					printf("t45.txt=\"Y-T\"\xff\xff\xff");
					else printf("t45.txt=\"X-Y\"\xff\xff\xff");
				}break;
				case 3:
				{
					menu2_status--;
					if(xy_enable==0)
					printf("t45.txt=\"->Y-T\"\xff\xff\xff");
					else printf("t45.txt=\"->X-Y\"\xff\xff\xff");
					switch(Trigger_ANS)
					{
						case 0:
						{
							printf("t46.txt=\"AUTO\"\xff\xff\xff");
						}break;
						case 1:
						{
							printf("t46.txt=\"NROMAL\"\xff\xff\xff");
						}break;
						case 2:
						{
							printf("t46.txt=\"SINGLE\"\xff\xff\xff");
						}break;
					}
				}break;
				case 4:
				{
					menu2_status--;
					switch(Trigger_ANS)
					{
						case 0:
						{
							printf("t46.txt=\"->AUTO\"\xff\xff\xff");
						}break;
						case 1:
						{
							printf("t46.txt=\"->NROMAL\"\xff\xff\xff");
						}break;
						case 2:
						{
							printf("t46.txt=\"->SINGLE\"\xff\xff\xff");
						}break;
					}
					if(fft_enable==1)
					{
						printf("t49.txt=\"FFT开\"\xff\xff\xff");
					}
					else printf("t49.txt=\"FFT关\"\xff\xff\xff");
				}break;
				case 5:
				{
					menu2_status--;
					if(fft_enable==1)
					{
						printf("t49.txt=\"->FFT开\"\xff\xff\xff");
					}
					else printf("t49.txt=\"->FFT关\"\xff\xff\xff");
					if(get_freq_enable==1) printf("t50.txt=\"测频开\"\xff\xff\xff");
					else printf("t50.txt=\"测频关\"\xff\xff\xff");
				}break;
				case 6:
				{
					menu2_status--;
					if(get_freq_enable==1) printf("t50.txt=\"->测频开\"\xff\xff\xff");
					else printf("t50.txt=\"->测频关\"\xff\xff\xff");
				}break;
			}
		
		}
	}
	if(GPIO_Pin==GPIO_PIN_15)
	{
		freq_counter++;
	}
	set_offset_ch1(offset_ch1+caliboration_ch1);
	set_offset_ch2(offset_ch2+caliboration_ch2);
	 __HAL_GPIO_EXTI_CLEAR_IT(GPIO_Pin);
}

//void delay_ms(uint32_t ms)
//{
//	for(uint32_t i=0;i<ms;i++)
//	{
//		delay_us(1000);
//	}
//	
//}

//void delay_us(uint32_t us)
//{
//	if(us>65535)
//	{	
//		us=65535;
//		printf("%s %d param us is overrun \r\n",__FILE__,__LINE__);
//	}
//	__HAL_TIM_SET_COUNTER(&htim4,0);
//	__HAL_TIM_SET_AUTORELOAD(&htim4,us);
//	HAL_TIM_Base_Start(&htim4);
//	while(!__HAL_TIM_GET_FLAG(&htim4,TIM_FLAG_UPDATE));
//	__HAL_TIM_CLEAR_FLAG(&htim4,TIM_FLAG_UPDATE);
//	HAL_TIM_Base_Stop(&htim4);
//	
//}	
