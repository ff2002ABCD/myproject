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
#include "fft.h"
#include "filter.h"

//测量值取Num个平均值，波形取K个平均值
#define Num 20
#define K 1
uint32_t tim3_counter,tim2_counter,tim1_counter;
int16_t ad1[2800*K],ad2[2800*K];
uint16_t i,j;
int16_t TriggerPoint=1000;
uint8_t Trigger_set=128;
int16_t Trigger_set_offset=0;
_Bool CH1_enable=1,CH2_enable=1,xy_enable=0,tim3_flag=0,CH1_status,CH2_status,fft_enable=0;
//菜单1相关的变量
uint8_t menu_status=0,Ouhe=0,Ouhe1=0,Channel=0,time_per_grid=6,voltage_per_grid_1=6,voltage_per_grid=6,Trigger_state=1;

//菜单2相关的变量
uint8_t menu2_status=0;
int16_t caliboration_ch1=0;
int16_t caliboration_ch2=0;
uint8_t Trigger_ANS=0;
uint8_t Trigger_flag=0;
uint8_t single_flag;
uint8_t parament_flag=1; 

//曲线相关的变量
uint8_t cursor_status=0,hengzong=0,cursor_num=0;
uint16_t x1=200,x2=400,y1=100,y2=300,step=10;
_Bool tim3_flag;

//波形相关数据变量

int flag;
uint16_t mem2[2800*K];
uint16_t buffer1[2800],buffer2[700],buffer3[2800],buffer4[700];
int32_t temp,temp0;
int ADC_flag;
uint8_t RX_buffer[16];
int16_t offset=0;
int16_t offset_ch1=0;
int16_t offset_ch2=0;

int tim1ch1flag,tim1ch2flag,tim1ch3flag,tim1ch4flag;
int dmatxflag;
//测量值相关变量
int16_t ZeroPoint1,ZeroPoint2;
float ch1_voltage_max,ch2_voltage_max,ch1_voltage_min,ch2_voltage_min;
uint32_t freq_counter;
float Vpp1_sum,Vpp2_sum;

//测频变量
uint32_t time_50000;
uint32_t timer4;
uint32_t freqency;
_Bool tim5_flag;
_Bool get_freq_enable;

//单片机adc信号采集
uint32_t ADC_Value[100];
int LCDY[10];
int HTJ[10];
int SPFD[10];
int temp_int;
double temp_d;

void sample_100Mhz(void)
{
	TIM2->PSC=1-1;
	TIM2->ARR=2-1;
	TIM1->PSC=2-1;
	TIM1->ARR=4-1;
	TIM1->CCR1=1;
	TIM1->CCR2=3;
	TIM1->CCR3=5;
	TIM1->CCR4=7;
//	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_1);
//	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_2);
//	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_3);
//	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_4);
	//HAL_DMA_Start_IT(&hdma_tim1_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)buffer1,700);
	//HAL_DMA_Start_IT(&hdma_tim1_ch2,(uint32_t)&GPIOD->IDR,(uint32_t)buffer2,700);
	//HAL_DMA_Start_IT(&hdma_tim1_ch3,(uint32_t)&GPIOD->IDR,(uint32_t)buffer3,700);
	//HAL_DMA_Start_IT(&hdma_tim1_ch4,(uint32_t)&GPIOD->IDR,(uint32_t)buffer4,700);
}

void sample_50Mhz(void)
{
	//__HAL_TIM_DISABLE_DMA(&htim1,TIM_DMA_CC1);
	TIM2->PSC=2-1;
	TIM2->ARR=4-1;
	TIM1->PSC=2-1;
	TIM1->ARR=8-1;
	TIM1->CCR1=1;
	TIM1->CCR3=5;
//	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_1);
//	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_3);
//	//HAL_DMA_Start_IT(&hdma_tim1_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)buffer1,1400);
//	HAL_DMA_Start_IT(&hdma_tim1_ch3,(uint32_t)&GPIOD->IDR,(uint32_t)buffer3,1400);
}

void Init_Osc(void)
{
	Filter_Init();
	HAL_ADCEx_Calibration_Start(&hadc1, ADC_CALIB_OFFSET, ADC_SINGLE_ENDED);
	HAL_ADC_Start_DMA(&hadc1, (uint32_t*)&ADC_Value, 100);
	HAL_TIM_PWM_Start(&htim2,TIM_CHANNEL_1);
	HAL_TIM_PWM_Start(&htim2,TIM_CHANNEL_2);
	HAL_TIM_Base_Start_IT(&htim3);
	__HAL_TIM_CLEAR_FLAG(&htim4, TIM_SR_UIF);
	//HAL_TIM_Base_Start_IT(&htim4);
	//HAL_TIM_Base_Start_IT(&htim5);
	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_2);
	//HAL_TIM_Base_Start_IT(&htim1);
	set_offset_ch1(offset_ch1);
	set_offset_ch2(offset_ch2);
	HAL_DAC_Start(&hdac1, DAC_CHANNEL_1);
	HAL_DAC_Start(&hdac1, DAC_CHANNEL_2);
	HAL_GPIO_WritePin(DIO_S1_GPIO_Port,DIO_S1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(DIO_S2_GPIO_Port,DIO_S2_Pin,GPIO_PIN_RESET);
	HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
	HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
	__HAL_TIM_ENABLE_DMA(&htim2,TIM_DMA_CC1);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC1);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC2);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC3);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC4);
	HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,2800*K);
	TIM1->PSC=2-1;
	TIM1->ARR=3-1;
	//TIM1->CCR1=2;
	TIM2->PSC=2-1;
	TIM2->ARR=100-1;
	TIM2->CCR1=1;
	TIM2->CCR2=1;
	//屏幕刷新率
	//200M/(psc+1)/(arr+1)
	TIM3->PSC=4000-1;
	TIM3->ARR=40000-1;
//	printf("vis t16,0\xFF\xFF\xFF");
//	printf("vis t17,0\xFF\xFF\xFF");
//	printf("vis t18,0\xFF\xFF\xFF");
//	printf("vis t19,0\xFF\xFF\xFF");
//	printf("vis t20,0\xFF\xFF\xFF");
//	printf("vis t21,0\xFF\xFF\xFF");
//	printf("vis t22,0\xFF\xFF\xFF");
//	printf("vis t23,0\xFF\xFF\xFF");
//	printf("vis t24,0\xFF\xFF\xFF");
//	printf("t0.txt=\"通道\"\xFF\xFF\xFF");
//	printf("t1.txt=\"CH1\"\xFF\xFF\xFF");
//	printf("t2.txt=\"时间档位\"\xFF\xFF\xFF");
//	printf("t3.txt=\"50us\"\xFF\xFF\xFF");
//	printf("t4.txt=\"垂直档位\"\xFF\xFF\xFF");
//	printf("t5.txt=\"1V\"\xFF\xFF\xFF");
//	printf("t6.txt=\"水平偏移\"\xFF\xFF\xFF");
//	printf("t7.txt=\"+0\"\xFF\xFF\xFF");
//	printf("t8.txt=\"垂直偏移\"\xFF\xFF\xFF");
//	printf("t9.txt=\"+0\"\xFF\xFF\xFF");
//	printf("t10.txt=\"触发阈值\"\xFF\xFF\xFF");
//	printf("t11.txt=\"+0\"\xFF\xFF\xFF");
//	printf("t12.txt=\"耦合方式\"\xFF\xFF\xFF");
//	printf("t13.txt=\"DC\"\xFF\xFF\xFF");
//	printf("t14.txt=\"触发类型\"\xFF\xFF\xFF");
//	printf("t15.txt=\"CH1下\"\xFF\xFF\xFF");
//	printf("t27.txt=\"电压1：\"\xff\xff\xff");
//	printf("t28.txt=\"电压2：\"\xff\xff\xff");
//	printf("t29.txt=\"时间1：\"\xff\xff\xff");
//	printf("t30.txt=\"时间2：\"\xff\xff\xff");
//	printf("vis t27,0\xFF\xFF\xFF");
//	printf("vis t28,0\xFF\xFF\xFF");
//	printf("vis t29,0\xFF\xFF\xFF");
//	printf("vis t30,0\xFF\xFF\xFF");
//	printf("vis t31,0\xFF\xFF\xFF");
//	printf("vis t32,0\xFF\xFF\xFF");
//	printf("vis t33,0\xFF\xFF\xFF");
//	printf("vis t34,0\xFF\xFF\xFF");
//	printf("vis t35,0\xFF\xFF\xFF");
//	printf("vis t36,0\xFF\xFF\xFF");
//	printf("vis t37,0\xFF\xFF\xFF");
//	printf("vis t38,0\xFF\xFF\xFF");
//	printf("vis t39,0\xFF\xFF\xFF");
//	printf("vis t41,0\xFF\xFF\xFF");
//	printf("vis t42,0\xFF\xFF\xFF");
//	printf("vis t43,0\xFF\xFF\xFF");
//	printf("vis t47,1\xFF\xFF\xFF");
//	printf("vis t48,1\xFF\xFF\xFF");
//	printf("vis t51,1\xFF\xFF\xFF");
//	printf("vis t52,1\xFF\xFF\xFF");
//	printf("vis t53,1\xFF\xFF\xFF");
//	printf("vis t54,1\xFF\xFF\xFF");
//	printf("vis t55,1\xFF\xFF\xFF");
//	printf("vis t56,1\xFF\xFF\xFF");
}

void display_osc(void)
{
//	if(time_per_grid==4)if(tim1ch1flag==1&&tim1ch3flag==1) 
//	{
//		flag=1;
//		tim1ch1flag=0;
//		tim1ch3flag=0;
//	}
//	if(time_per_grid==3)if(tim1ch1flag==1&&tim1ch4flag==1) 
//	{
//		flag=1;
//		tim1ch1flag=0;
//		tim1ch4flag=0;
//	}
//	if(flag==1)
//	{	
//		flag=0;
//		if(time_per_grid==3)
//		{
//			for(int i=0;i<700;i++)
//			{
//				mem2[4*i]=buffer1[i];
//				mem2[4*i+1]=buffer2[i];
//				mem2[4*i+2]=buffer3[i];
//				mem2[4*i+3]=buffer4[i];
//			}
//		}
//		else if(time_per_grid==4)
//		{
////			for(int i=0;i<1400;i++)
////			{
////				mem2[2*i]=buffer1[i];	
////				mem2[2*i+1]=buffer3[i];
////			}
//			for(int i=0;i<1400;i++)
//			{
//				mem2[2*i]=buffer3[i];
//				mem2[2*i+1]=buffer1[i];
//			}
//		}
		for(int i=0;i<2800*K;i++) 
		{	
			//printf("mem2[%d]=%x\xff\xff\xff",i,mem2[i]);
			temp0=((mem2[i]%256)+128)%256;
			temp=((mem2[i]/256)+128)%256;
			if(temp-128>127/1.25) temp=127/1.25+128;
			else if(temp-128<-128/1.25) temp=-128/1.25+128;
			ad1[i]=((int)(((temp-128)*1.25))+128)%256;
			if(temp0-128>127/1.25) temp0=127/1.25+128;
			else if(temp0-128<-128/1.25) temp0=-128/1.25+128;
			ad2[i]=((int)(((temp0-128)*1.25))+128)%256;
		}
		for(int i=0;i<2800;i++) 
		{
			temp=0;
			temp0=0;
			for(int j=0;j<K;j++)
			{
				temp+=ad1[K*i+j];
				temp0+=ad2[K*i+j];
			}
			ad1[i]=temp/K;
			ad2[i]=temp0/K;
			if(ad1[i]>255) ad1[i]=255;
			else if(ad1[i]<0) ad1[i]=0;
			if(ad2[i]>255) ad2[i]=255;
			else if(ad2[i]<0) ad2[i]=0;
		}
		switch(Trigger_state)
		{
			//CH1下降沿触发
			case 1:
			{
				for(i=1200;i<2000;i++)
				{
					if(ad1[i]>=Trigger_set+Trigger_set_offset)
					{
						if(ad1[i+2]<Trigger_set+Trigger_set_offset) 
						{
							TriggerPoint=i;
							Trigger_flag=1;
							break;
						}
					}
					if(i==1999) 
					{
						Trigger_flag=0;
						single_flag=1;
					}
				}
			}break;
			//CH1上升沿触发
			case 2:
			{
				for(i=1200;i<2000;i++)
				{					
					if(ad1[i]<=Trigger_set+Trigger_set_offset)
					{
						if(ad1[i+2]>Trigger_set+Trigger_set_offset) 
						{
							TriggerPoint=i;
							Trigger_flag=1;
							break;
						}
					}
					if(i==1999)
					{
						Trigger_flag=0;
						single_flag=1;
					}
				}
			}break;
			//CH2下降沿
			case 3:
			{
				for(i=1200;i<2000;i++)
				{
					if(ad2[i]>Trigger_set+Trigger_set_offset)
					{
						if(ad2[i+2]<=Trigger_set+Trigger_set_offset) 
						{
							TriggerPoint=i;
							Trigger_flag=1;
							break;
						}
					}
					if(i==1999)
					{
						Trigger_flag=0;
						single_flag=1;
					}
				}
			}break;
			//CH2上升沿触发
			case 4:
			{
				for(i=1200;i<2000;i++)
				{					
					if(ad2[i]<=Trigger_set+Trigger_set_offset)
					{
						if(ad2[i+2]>Trigger_set+Trigger_set_offset) 
						{
							TriggerPoint=i;
							Trigger_flag=1;
							break;
						}
					}
					if(i==1999) 
					{
						Trigger_flag=0;
						single_flag=1;
					}
				}
			}break;
			//不触发
			case 5:
			{
				TriggerPoint=1000;
			}break;
		}
		
		if(CH1_enable==1&&dmatxflag==0)
		{				
			//Auto输出通道1
			if(Trigger_ANS==0)
			{
				CH1_status=1;
				printf("addt 1,0,651\xFF\xFF\xFF");
				HAL_Delay(100);
		//		dmatxflag=1;
		//		HAL_UART_Transmit_DMA(&huart1,&ad1[i-325],1300);
				for(i=TriggerPoint+offset,j=0;j<651;j++,i++)
				{
					printf("%c",ad1[i-325]);
				}
				printf("\x01\xff\xff\xff");//确保透传结束
			}
			//Normal输出通道1
			else if(Trigger_ANS==1)
			{
				if(Trigger_flag==1)
				{
					CH1_status=1;
					printf("addt 1,0,651\xFF\xFF\xFF");
					HAL_Delay(50);
			//		dmatxflag=1;
			//		HAL_UART_Transmit_DMA(&huart1,&ad1[i-325],1300);
					for(i=TriggerPoint+offset,j=0;j<651;j++,i++)
					{
						printf("%c",ad1[i-325]);
					}
					printf("\x01\xff\xff\xff");//确保透传结束
				}
			}
			//Single输出通道1
			else if(Trigger_ANS==2)
			{
				if(Trigger_flag==1&&single_flag==1)
				{	
					CH1_status=1;
					printf("addt 1,0,651\xFF\xFF\xFF");
					HAL_Delay(50);
			//		dmatxflag=1;
			//		HAL_UART_Transmit_DMA(&huart1,&ad1[i-325],1300);
					for(i=TriggerPoint+offset,j=0;j<651;j++,i++)
					{
						printf("%c",ad1[i-325]);
					}
					printf("\x01\xff\xff\xff");//确保透传结束
				}
			}
		}
		HAL_Delay(50);
		
		if(CH2_enable==1&&dmatxflag==0)
		{
			if(Trigger_ANS==0)
			{
				//Auto输出通道2
				CH2_status=1;
				printf("addt 1,1,651\xFF\xFF\xFF");
				//HAL_UART_Receive(&huart1,RX_buffer,4,3);
				HAL_Delay(100);
		//		dmatxflag=1;
			//	HAL_UART_Transmit_DMA(&huart1,&ad2[i-325],1300);
				for(i=TriggerPoint+offset,j=0;j<651;j++,i++)
				{
					printf("%c",ad2[i-325]);
					//printf("%c",((mem2[i]/256)+128)%256);
				}
				printf("\x01\xff\xff\xff");//确保透传结束
			}
			//Normal输出通道2
			else if(Trigger_ANS==1)
			{
				if(Trigger_flag==1)
				{
					CH2_status=1;
					printf("addt 1,1,651\xFF\xFF\xFF");
					//HAL_UART_Receive(&huart1,RX_buffer,4,3);
					HAL_Delay(50);
			//		dmatxflag=1;
				//	HAL_UART_Transmit_DMA(&huart1,&ad2[i-325],1300);
					for(i=TriggerPoint+offset,j=0;j<651;j++,i++)
					{
						printf("%c",ad2[i-325]);
						//printf("%c",((mem2[i]/256)+128)%256);
					}
					printf("\x01\xff\xff\xff");//确保透传结束
				}
			}
			//Single输出通道2
			else if(Trigger_ANS==2)
			{
				if(Trigger_flag==1&&single_flag==1)
				{
					single_flag=0;
					CH2_status=1;
					printf("addt 1,1,651\xFF\xFF\xFF");
					//HAL_UART_Receive(&huart1,RX_buffer,4,3);
					HAL_Delay(50);
			//		dmatxflag=1;
				//	HAL_UART_Transmit_DMA(&huart1,&ad2[i-325],1300);
					for(i=TriggerPoint+offset,j=0;j<651;j++,i++)
					{
						printf("%c",ad2[i-325]);
						//printf("%c",((mem2[i]/256)+128)%256);
					}
					printf("\x01\xff\xff\xff");//确保透传结束
				}
			}
		}
		//输出x-y曲线
		HAL_Delay(5);
		
		if(xy_enable==1)
		{
			//Auto
			if(Trigger_ANS==0)
			{
				for(i=TriggerPoint+offset,j=0;j<100;j++,i++)
				{
					printf("fill %d,%d,1,1,RED\xFF\xFF\xFF",0+ad1[i-325]*3/2,385-ad2[i-325]*3/2);
				}
				HAL_Delay(100);
				printf("fill 0,0,651,385,BLACK\xFF\xFF\xFF");
				printf("ref 1\xFF\xFF\xFF");
			}
			//Normal
			else if(Trigger_ANS==1)
			{
				if(Trigger_flag==1)
				{
					for(i=TriggerPoint+offset,j=0;j<100;j++,i++)
					{
						printf("fill %d,%d,1,1,RED\xFF\xFF\xFF",0+ad1[i-325]*3/2,385-ad2[i-325]*3/2);
					}
					HAL_Delay(100);
					printf("fill 0,0,651,385,BLACK\xFF\xFF\xFF");
					printf("ref 1\xFF\xFF\xFF");
				}
			}
			//Single
			else if(Trigger_ANS==2)
			{
				if(Trigger_flag==1&&single_flag==1)
				{
					single_flag=0;
					printf("fill 0,0,651,385,BLACK\xFF\xFF\xFF");
					printf("ref 1\xFF\xFF\xFF");
					for(i=TriggerPoint+offset,j=0;j<100;j++,i++)
					{
						printf("fill %d,%d,1,1,RED\xFF\xFF\xFF",0+ad1[i-325]*3/2,385-ad2[i-325]*3/2);
					}
					HAL_Delay(100);
					
				}
			}
 		}	
		if(fft_enable==1) dofft(Channel);
		HAL_TIM_PWM_Start(&htim2,TIM_CHANNEL_1);
		HAL_TIM_PWM_Start(&htim2,TIM_CHANNEL_2);
//		if(time_per_grid==3 )
//		{
//			HAL_DMA_Start_IT(&hdma_tim1_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)buffer1,700);
//			HAL_DMA_Start_IT(&hdma_tim1_ch2,(uint32_t)&GPIOD->IDR,(uint32_t)buffer2,700);
//			HAL_DMA_Start_IT(&hdma_tim1_ch3,(uint32_t)&GPIOD->IDR,(uint32_t)buffer3,700);
//			HAL_DMA_Start_IT(&hdma_tim1_ch4,(uint32_t)&GPIOD->IDR,(uint32_t)buffer4,700);
//		}
//		else if(time_per_grid==4)
//		{
//			HAL_DMA_Start_IT(&hdma_tim1_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)buffer1,1400);
//			HAL_DMA_Start_IT(&hdma_tim1_ch3,(uint32_t)&GPIOD->IDR,(uint32_t)buffer3,1400);
//		}
		HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,2800*K);
	}


void renew_data(void)
{
	CH1_status=0;
	CH2_status=0;
	//刷新曲线信息
	switch(cursor_status)
	{
		case 0:
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
		}break;
		case 1:
		{
			printf("vis t16,1\xFF\xFF\xFF");
			printf("vis t17,1\xFF\xFF\xFF");
			printf("vis t18,1\xFF\xFF\xFF");
			printf("vis t19,1\xFF\xFF\xFF");
			printf("vis t20,1\xFF\xFF\xFF");
			printf("vis t21,1\xFF\xFF\xFF");
			printf("vis t22,1\xFF\xFF\xFF");
			printf("vis t23,1\xFF\xFF\xFF");
			printf("vis t24,1\xFF\xFF\xFF");
			if(hengzong==0) printf("t24.txt=\"选横纵：横\"\xFF\xFF\xFF");
			else printf("t24.txt=\"选横纵：纵\"\xFF\xFF\xFF");
		}break;
		case 2:
		{
			printf("vis t16,1\xFF\xFF\xFF");
			printf("vis t17,1\xFF\xFF\xFF");
			printf("vis t18,1\xFF\xFF\xFF");
			printf("vis t19,1\xFF\xFF\xFF");
			printf("vis t20,1\xFF\xFF\xFF");
			printf("vis t21,1\xFF\xFF\xFF");
			printf("vis t22,1\xFF\xFF\xFF");
			printf("vis t23,1\xFF\xFF\xFF");
			printf("vis t24,1\xFF\xFF\xFF");
			if(cursor_num==0)
			{
				printf("t24.txt=\"选通道：1\"\xFF\xFF\xFF");
			}
			else
			{
				printf("t24.txt=\"选通道：2\"\xFF\xFF\xFF");
			}
		}break;
		case 3:
		{
			printf("vis t16,1\xFF\xFF\xFF");
			printf("vis t17,1\xFF\xFF\xFF");
			printf("vis t18,1\xFF\xFF\xFF");
			printf("vis t19,1\xFF\xFF\xFF");
			printf("vis t20,1\xFF\xFF\xFF");
			printf("vis t21,1\xFF\xFF\xFF");
			printf("vis t22,1\xFF\xFF\xFF");
			printf("vis t23,1\xFF\xFF\xFF");
			printf("vis t24,1\xFF\xFF\xFF");
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
	//刷新菜单2
	printf("vis t44,1\xFF\xFF\xFF");
	printf("vis t45,1\xFF\xFF\xFF");
	printf("vis t46,1\xFF\xFF\xFF");
	printf("vis t49,1\xFF\xFF\xFF");
	printf("vis t57,1\xFF\xFF\xFF");
	printf("t44.txt=\"零点校准\"\xff\xff\xff");
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
	printf("t57.txt=\"切换参数\"\xff\xff\xff");
	switch(menu2_status)
	{
		case 0:
		{
			printf("vis t44,0\xFF\xFF\xFF");
			printf("vis t45,0\xFF\xFF\xFF");
			printf("vis t46,0\xFF\xFF\xFF");
			printf("vis t49,0\xFF\xFF\xFF");
			printf("vis t50,0\xFF\xFF\xFF");
			printf("vis t57,0\xFF\xFF\xFF");
		}break;
		case 1:
		{
			printf("t44.txt=\"->零点校准\"\xff\xff\xff");
			
		}break;
		case 2:
		{
			if(xy_enable==0)
			printf("t45.txt=\"->Y-T\"\xff\xff\xff");
			else printf("t45.txt=\"->X-Y\"\xff\xff\xff");
		}break;
		case 3:
		{
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
		case 4:
		{
			if(fft_enable==1) printf("t49.txt=\"->FFT开\"\xff\xff\xff");
			else printf("t49.txt=\"->FFT关\"\xff\xff\xff");
		}break;
		case 5:
		{
			if(get_freq_enable==1) printf("t50.txt=\"->测频开\"\xff\xff\xff");
			else printf("t50.txt=\"->测频关\"\xff\xff\xff");
		}break;
		case 6:
		{
			printf("t57.txt=\"->切换参数\"\xff\xff\xff");
		}break;
	}
	//刷新菜单1
	printf("t0.txt=\"通道\"\xFF\xFF\xFF");
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
		case 1:
		{
			printf("t0.txt=\"*通道\"\xFF\xFF\xFF");
		}break;
		case 2:
		{
			printf("t2.txt=\"*时间档位\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t2.txt=\"*频率档位\"\xFF\xFF\xFF");
		}break;
		case 3:
		{
			printf("t4.txt=\"*垂直档位\"\xFF\xFF\xFF");
		}break;
		case 4:
		{
			printf("t6.txt=\"*水平偏移\"\xFF\xFF\xFF");
		}break;
		case 5:
		{
			printf("t8.txt=\"*垂直偏移\"\xFF\xFF\xFF");
		}break;
		case 6:
		{
			printf("t10.txt=\"*触发阈值\"\xFF\xFF\xFF");
		}break;
		case 7:
		{
			printf("t12.txt=\"*耦合方式\"\xFF\xFF\xFF");
		}break;
		case 8:
		{
			printf("t14.txt=\"*触发类型\"\xFF\xFF\xFF");
		}break;
		case 9:
		{
			printf("t0.txt=\"->通道\"\xFF\xFF\xFF");
		}break;
		case 10:
		{
			printf("t2.txt=\"->时间档位\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t2.txt=\"->频率档位\"\xFF\xFF\xFF");
		}break;
		case 11:
		{
			printf("t4.txt=\"->垂直档位\"\xFF\xFF\xFF");
		}break;
		case 12:
		{
			printf("t6.txt=\"->水平偏移\"\xFF\xFF\xFF");
		}break;
		case 13:
		{
			printf("t8.txt=\"->垂直偏移\"\xFF\xFF\xFF");
		}break;
		case 14:
		{
			printf("t10.txt=\"->触发阈值\"\xFF\xFF\xFF");
		}break;
		case 15:
		{
			printf("t12.txt=\"->耦合方式\"\xFF\xFF\xFF");
		}break;
		case 16:
		{
			printf("t14.txt=\"->触发类型\"\xFF\xFF\xFF");
		}break;
	}
	//水平偏移
	if(measure_time_us(offset)>1000) printf("t7.txt=\"+%.2fms\"\xff\xff\xff",measure_time_ms(offset));
	else if (measure_time_us(offset)>=0) printf("t7.txt=\"+%.2fus\"\xff\xff\xff",measure_time_us(offset));
	else printf("t7.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(offset));
	//垂直偏移
	
	if(Channel==0)
	{
		if(measure_voltage_V(offset_ch1+128,1)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
		else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
		if(Ouhe==0) 
		{
			printf("t13.txt=\"DC\"\xFF\xFF\xFF");
			HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_SET);
		}
		else 
		{
			printf("t13.txt=\"AC\"\xFF\xFF\xFF");
			HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_RESET);
		}
	}
	else
	{
		if(measure_voltage_V(offset_ch2+128,2)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
		else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
		if(Ouhe1==0)
		{ 
			printf("t13.txt=\"DC\"\xFF\xFF\xFF");
			HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_SET);
		}
		else 
		{
			printf("t13.txt=\"AC\"\xFF\xFF\xFF");
			HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_RESET);
		}
	}
	//刷新触发阈值
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
	
	switch(time_per_grid+3)
	{
		case 3:
		{
			printf("t3.txt=\"500ns\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"5MHz\"\xFF\xFF\xFF");
		}break;
		case 4:
		{
			printf("t3.txt=\"1us\"\xFF\xFF\xFF");
			if(fft_enable==1) printf("t3.txt=\"2.5MHz\"\xFF\xFF\xFF");
		}break;
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
			if(fft_enable==1) printf("t3.txt=\"25KHz\"\xFF\xFF\xFF");
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
	//刷新测量值
	if(parament_flag==1)
	{
		
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
	printf("t27.txt=\"电压1：\"\xff\xff\xff");
	printf("t28.txt=\"电压2：\"\xff\xff\xff");
	printf("t29.txt=\"时间1：\"\xff\xff\xff");
	printf("t30.txt=\"时间2：\"\xff\xff\xff");
	
	printf("vis t25,1\xff\xff\xff");
	printf("vis t26,1\xff\xff\xff");
	if(cursor_measure_voltage_V(y1,1)<0) printf("t31.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,1));
	else printf("t31.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,1));
	if(cursor_measure_voltage_V(y2,2)<0) printf("t32.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y2,2));
	else printf("t32.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y2,2));
	
	if(fft_enable==1)
	{
		printf("vis t25,0\xff\xff\xff");
		printf("vis t26,0\xff\xff\xff");
		printf("t29.txt=\"频率1：\"\xff\xff\xff");
		printf("t30.txt=\"频率2：\"\xff\xff\xff");
		printf("t31.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_fft(y1,1));
		printf("t32.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_fft(y2,2));
	}
	if(measure_time_us(x1)>1000) printf("t33.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(x1));
	else printf("t33.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(x1));
	if(measure_time_us(x2)>1000) printf("t34.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(x2));
	else printf("t34.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(x2));
	if(fft_enable==1)
	{
		if(measure_freq_Hz_fft(x1)<1000) printf("t33.txt=\"%.0fHz\"\xff\xff\xff",measure_freq_Hz_fft(x1));
		else printf("t33.txt=\"%.0fKHz\"\xff\xff\xff",measure_freq_KHz_fft(x1));
		if(measure_freq_Hz_fft(x2)<1000) printf("t34.txt=\"%.0fHz\"\xff\xff\xff",measure_freq_Hz_fft(x2));
		else printf("t34.txt=\"%.0fKHz\"\xff\xff\xff",measure_freq_KHz_fft(x2));
	}
	
	
	findzeropoint_ch1(&ZeroPoint1,&ZeroPoint2);
	if(measure_cycletime_us(ZeroPoint1,ZeroPoint2)<1000)
	printf("t37.txt=\"%.2fus\"\xff\xff\xff",measure_cycletime_us(ZeroPoint1,ZeroPoint2));
	else printf("t37.txt=\"%.2fms\"\xff\xff\xff",measure_cycletime_ms(ZeroPoint1,ZeroPoint2));
	
	if(measure_freq_kHz(ZeroPoint1,ZeroPoint2)<1000)
	printf("t38.txt=\"%.2fKHz\"\xff\xff\xff",measure_freq_kHz(ZeroPoint1,ZeroPoint2));
	else printf("t38.txt=\"%.2fHz\"\xff\xff\xff",measure_freq_Hz(ZeroPoint1,ZeroPoint2));
	
	findzeropoint_ch2(&ZeroPoint1,&ZeroPoint2);
	if(measure_cycletime_us(ZeroPoint1,ZeroPoint2)<1000)
	printf("t39.txt=\"%.2fus\"\xff\xff\xff",measure_cycletime_us(ZeroPoint1,ZeroPoint2));
	else printf("t39.txt=\"%.2fms\"\xff\xff\xff",measure_cycletime_ms(ZeroPoint1,ZeroPoint2));
	
	if(measure_freq_kHz(ZeroPoint1,ZeroPoint2)<1000)
	printf("t40.txt=\"%.2fKHz\"\xff\xff\xff",measure_freq_kHz(ZeroPoint1,ZeroPoint2));
	else printf("t40.txt=\"%.2fHz\"\xff\xff\xff",measure_freq_Hz(ZeroPoint1,ZeroPoint2));
	
	ch1_voltage_max=measure_voltage_V(find_max_ch1(),1);
	ch1_voltage_min=measure_voltage_V(find_min_ch1(),1);
	ch2_voltage_max=measure_voltage_V(find_max_ch2(),2);
	ch2_voltage_min=measure_voltage_V(find_min_ch2(),2);
	static int i=0;
	
	Vpp1_sum+=ch1_voltage_max-ch1_voltage_min;
	Vpp2_sum+=ch2_voltage_max-ch2_voltage_min;
	i++;
	if(i==Num)
	{
		i=0;
		printf("t42.txt=\"%.2fV\"\xff\xff\xff",Vpp1_sum/Num);
		printf("t43.txt=\"%.2fV\"\xff\xff\xff",Vpp2_sum/Num);
		Vpp1_sum=0;
		Vpp2_sum=0;
	}
	//刷新测量值2
	
//	printf("t42.txt=\"%.2fV\"\xff\xff\xff",ch1_voltage_max-ch1_voltage_min);
//	printf("t43.txt=\"%.2fV\"\xff\xff\xff",ch2_voltage_max-ch2_voltage_min);
}

void ADC_8CH(void)
{
	//8通道ad采集
	for(int i=0;i<8;i++)
	{	

		HAL_ADC_Start(&hadc1);
		HAL_ADC_PollForConversion(&hadc1, 50);
		if(HAL_IS_BIT_SET(HAL_ADC_GetState(&hadc1), HAL_ADC_STATE_REG_EOC))
		{
			ADC_Value[i] = HAL_ADC_GetValue(&hadc1);
			if(i!=0) printf("ad%d=%d\xFF\xFF\xFF",i,ADC_Value[i-1]);
			if(i==0) printf("ad%d=%d\xFF\xFF\xFF",i,ADC_Value[7]);
		}
	}
}

void disp_signal()
{
	static int j=0;
	LCDY[j]=ADC_Value[4];
	SPFD[j]=ADC_Value[5];
	HTJ[j]=ADC_Value[6];
	
	j++;
	if(j==10) j=0;
	temp_int=avg_Filter_int(LCDY,10);
	temp_d=(double)(temp_int)/65536*3.3;
	printf("LCDY=%.2f\xff\xff\xff",temp_d*4000);
	printf("t54.txt=\"%.0fmA\"\xff\xff\xff",temp_d*4000);
	temp_int=avg_Filter_int(HTJ,10);
	temp_d=(double)(temp_int)/65536*3.3;
	printf("HTJ=%.0f\xff\xff\xff",temp_d*-7/3*1000);
	printf("t56.txt=\"%.1fmT\"\xff\xff\xff",temp_d*-7/3*1000);
	temp_int=avg_Filter_int(SPFD,10);
	temp_d=(double)(temp_int)/65536*3.3;
	printf("SPFD=%.2f\xff\xff\xff",temp_d*4);
	printf("t55.txt=\"%.2fV\"\xff\xff\xff",temp_d*4);
}

void ADC_DMA(void)
{
	
	if(ADC_flag==1)
	{
		ADC_flag=0;
		for(int i=0;i<100;i++)
		{
			printf("ADC_Value[%d]=%d\xff\xff\xff",i,ADC_Value[i]);
		}
		//HAL_ADC_Start_DMA(&hadc1, (uint32_t*)&ADC_Value, 100);
	}
}

void set_offset_ch1(int16_t offset)
{
	HAL_DAC_SetValue(&hdac1,DAC_CHANNEL_1,DAC_ALIGN_8B_R,255/3.3*(1.4+0.004*offset)/45*58);
}

void set_offset_ch2(int16_t offset)
{
	HAL_DAC_SetValue(&hdac1,DAC_CHANNEL_2,DAC_ALIGN_8B_R,255/3.3*(1.4+0.004*offset)/45*58);
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{	
	if(htim->Instance==htim5.Instance)
	{	
		printf("cle 1,255\xff\xff\xff");
		HAL_TIM_Base_Stop_IT(&htim4);
		timer4=TIM4->CNT;
		freqency=(time_50000*50000+timer4)*2;
		time_50000=0;
		TIM4->CNT=0;	
		HAL_TIM_Base_Start_IT(&htim4);
		tim5_flag=1;
		if(tim5_flag==1) printf("t48.txt=\"%dHz\"\xff\xff\xff",(int)(freqency*1.0017));
		
	}
	if(htim->Instance==htim4.Instance)
	{	
		time_50000++;
	}
  if(htim->Instance==htim3.Instance)
	{	
		
		renew_data();
		disp_signal();
		display_osc();
		//HAL_Delay(100);
		//ADC_DMA();
		ADC_8CH();
		
	}
}