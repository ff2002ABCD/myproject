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
#include "menu.h"
#include "button.h"
//测量值取Num个平均值，波形取K个平均值,核磁共振参数Num0个平均值,采样点数量S
#define Num 3
#define K 10
#define Num0 400
#define S 4000
#define DelayTime 30
#define DelayTime2 60
uint32_t tim3_counter,tim2_counter,tim1_counter,tim3_counter_1;
int16_t ad1[S*K],ad2[S*K];
uint16_t i,j;
int16_t TriggerPoint=1000;
uint8_t Trigger_set=128;
int16_t Trigger_set_offset_ch1=0;
int16_t Trigger_set_offset_ch2=0;
_Bool CH1_enable=1,CH2_enable=1,xy_enable=0,tim3_flag=0,CH1_status,CH2_status,fft_enable=0;
//菜单1相关的变量
uint8_t menu_status=9,Ouhe=1,Ouhe1=1,Channel=0,time_per_grid=12,voltage_per_grid_1=7,voltage_per_grid=5,Trigger_state=1;

//菜单2相关的变量
MENU2_STATUS menu2_status=0;
int16_t caliboration_ch1=0;
int16_t caliboration_ch2=0;
uint8_t Trigger_ANS=0;
uint8_t Trigger_flag=0;
	uint8_t single_flag,single_flag_1,single_flag_2;
uint8_t parament_flag=1; 

//校准
float del_zero_ch1=0,del_zero_ch2=0,del_k_ch1=0,del_k_ch2=0;
int8_t caliboration_mode=0,calibo_ch=1;
float calibo_step_zero=0.002,calibo_step_k=0.00002;

//曲线相关的变量
uint8_t cursor_status=0,hengzong=0,cursor_num=0,cursor_switch=0,cursor_mode=1;
uint16_t x1=200,x2=400,y1=100,y2=300,step=1;
_Bool tim3_flag;

//波形相关数据变量

int flag;
uint16_t mem2[S*K];
uint16_t buffer1[S],buffer2[700],buffer3[S],buffer4[700];
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
int distance1,distance2;

//变量
uint32_t time_50000;
uint32_t timer4;
uint32_t freqency;
_Bool tim5_flag;
_Bool get_freq_enable;
uint8_t RxData[10];
uint32_t temp_freq;


//单片机adc信号采集
CURRENT_CALIBO_STATE current_calibo_state=0;
uint32_t ADC_Value[100];
int LCDY[Num0];
int HTJ[Num0];
int SPFD[Num0];
int temp_int;
double temp_d,temp_d_last;
double current_offset=0;

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
	HAL_TIM_Base_Start_IT(&htim5);
	TIM5->PSC=200-1;
	TIM5->ARR=10000-1;
	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_2);
	//HAL_TIM_Base_Start_IT(&htim1);
	set_offset_ch1(offset_ch1);
	set_offset_ch2(offset_ch2);
	HAL_DAC_Start(&hdac1, DAC_CHANNEL_1);
	HAL_DAC_Start(&hdac1, DAC_CHANNEL_2);
	//DAC设置
	HAL_GPIO_WritePin(DIO_S1_GPIO_Port,DIO_S1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(DIO_S2_GPIO_Port,DIO_S2_Pin,GPIO_PIN_RESET);
	//耦合设置
	HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_RESET);
	HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_RESET);
	//电压档位设置
	HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
  HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
	HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
	HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
	
	HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
	HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
	__HAL_TIM_ENABLE_DMA(&htim2,TIM_DMA_CC1);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC1);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC2);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC3);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC4);
	HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S*K);
	TIM1->PSC=2-1;
	TIM1->ARR=3-1;
	//TIM1->CCR1=2;
	//时间档位5ms
	TIM2->PSC=2-1;
	TIM2->ARR=1000-1;
	TIM2->CCR1=2;
	TIM2->CCR2=2;
	//屏幕刷新率
	//200M/(psc+1)/(arr+1)
	//25Hz
	TIM3->PSC=100-1;
	TIM3->ARR=200-1;
	cursor_off();
	
		
	renew_menu2();
	printf("t5.txt=\"200mV\"\xff\xff\xff");
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
		for(int i=0;i<S*K;i++) 
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
		for(int i=0;i<S;i++) 
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
				for(i=S/4;i<S/2;i++)
				{
					if(ad1[i]>=Trigger_set+offset_ch1+Trigger_set_offset_ch1)
					{
						if(ad1[i+15]<Trigger_set+offset_ch1+Trigger_set_offset_ch1) 
						{
							TriggerPoint=i+8;
							Trigger_flag=1;
							break;
						}
					}
					if(i==S/2-1) 
					{
						Trigger_flag=0;
						single_flag=1;
					}
				}
			}break;
			//CH1上升沿触发
			case 2:
			{
				for(i=S/4;i<S/2;i++)
				{					
					if(ad1[i]<=Trigger_set+offset_ch1+Trigger_set_offset_ch1)
					{
						if(ad1[i+15]>Trigger_set+offset_ch1+Trigger_set_offset_ch1) 
						{
							TriggerPoint=i+8;
							Trigger_flag=1;
							break;
						}
					}
					if(i==S/2-1)
					{
						Trigger_flag=0;
						single_flag=1;
					}
				}
			}break;
			//CH2下降沿
			case 3:
			{
				for(i=S/4-150;i<S/2;i++)
				{
					if(ad2[i]>Trigger_set+offset_ch2+Trigger_set_offset_ch2)
					{
						if(ad2[i+15]<=Trigger_set+offset_ch2+Trigger_set_offset_ch2) 
						{
							TriggerPoint=i+8;
							Trigger_flag=1;
							break;
						}
					}
					if(i==S/2-1)
					{
						Trigger_flag=0;
						single_flag=1;
					}
				}
			}break;
			//CH2上升沿触发
			case 4:
			{
				for(i=S/4-150;i<S/2;i++)
				{			
					if(ad2[i]<Trigger_set+offset_ch2+Trigger_set_offset_ch2)
					{
						if(ad2[i+15]>=Trigger_set+offset_ch2+Trigger_set_offset_ch2) 
						{
							TriggerPoint=i+8;
							Trigger_flag=1;
							break;
						}
					}
					
					if(i==S/2-1) 
					{
						Trigger_flag=0;
						single_flag=1;
					}
				}
			}break;
			//不触发
			case 5:
			{
				TriggerPoint=S/4;
			}break;
		}
		
		if(CH1_enable==1)
		{				
			//Auto输出通道1
			if(Trigger_ANS==0)
			{
				CH1_status=1;
		//		HAL_UART_Receive(&huart4,RX_buffer,1,100);
				printf("addt 1,0,651\xFF\xFF\xFF");
//				
//				while(RX_buffer[0]==0x00);
//				RX_buffer[0]=0x00;
				//delay_ms(70);
				delay_ms(DelayTime);
				for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
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
					delay_ms(DelayTime);
			//		dmatxflag=1;
			//		HAL_UART_Transmit_DMA(&huart1,&ad1[i-325],1300);
					for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
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
					if(single_flag_1==1)return;
					single_flag_1=1;
					
					CH1_status=1;
					printf("addt 1,0,651\xFF\xFF\xFF");
					delay_ms(DelayTime);
			//		dmatxflag=1;
			//		HAL_UART_Transmit_DMA(&huart1,&ad1[i-325],1300);
					for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
					{
						printf("%c",ad1[i-325]);
					}
					printf("\x01\xff\xff\xff");//确保透传结束
				}
			}
		}
		printf("\x01\xff\xff\xff");
		//delay_ms(20);
		if(CH1_enable==1|CH2_enable==1)delay_ms(DelayTime2);
		if(CH2_enable==1)
		{
			if(Trigger_ANS==0)
			{
				//Auto输出通道2
				CH2_status=1;
//				HAL_UART_Receive(&huart4,RX_buffer,1,100);
				printf("addt 1,1,651\xFF\xFF\xFF");
				//HAL_UART_Receive(&huart1,RX_buffer,4,3);
				//delay_ms(70);
				delay_ms(DelayTime);
				
//				while(RX_buffer[0]==0x00);
//				RX_buffer[0]=0x00;
		//		dmatxflag=1;
			//	HAL_UART_Transmit_DMA(&huart1,&ad2[i-325],1300);
				for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
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
					delay_ms(DelayTime);
			//		dmatxflag=1;
				//	HAL_UART_Transmit_DMA(&huart1,&ad2[i-325],1300);
					for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
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
					if(single_flag_2==1)return;
					single_flag_2=1;
					single_flag=0;
					CH2_status=1;
					printf("addt 1,1,651\xFF\xFF\xFF");
					//HAL_UART_Receive(&huart1,RX_buffer,4,3);
					delay_ms(DelayTime);
			//		dmatxflag=1;
				//	HAL_UART_Transmit_DMA(&huart1,&ad2[i-325],1300);
					for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
					{
						printf("%c",ad2[i-325]);
						//printf("%c",((mem2[i]/256)+128)%256);
					}
					printf("\x01\xff\xff\xff");//确保透传结束
				}
			}
		}
		//输出x-y曲线
		if(xy_enable==1)
		{
			
			//Auto
			if(Trigger_ANS==0)
			{
				printf("ref 1\xFF\xFF\xFF");
				delay_ms(20);
				for(i=TriggerPoint-offset,j=0;j<650;j++,i++)
				{
				//	printf("fill %d,%d,3,3,YELLOW\xFF\xFF\xFF",135+ad1[i-325]*3/2,385-ad2[i-325]*3/2);
					printf("line %d,%d,%d,%d,YELLOW\xff\xff\xff",135+ad1[i-325]*3/2,385-ad2[i-325]*3/2,135+ad1[i-325+1]*3/2,385-ad2[i-325+1]*3/2);
					
					
				}
				//delay_ms(100);
			//	printf("fill 0,0,651,385,BLACK\xFF\xFF\xFF");
				
			}
			//Normal
			else if(Trigger_ANS==1)
			{
				if(Trigger_flag==1)
				{
					printf("ref 1\xFF\xFF\xFF");
					delay_ms(20);
					for(i=TriggerPoint-offset,j=0;j<650;j++,i++)
					{
					//	printf("fill %d,%d,1,1,YELLOW\xFF\xFF\xFF",0+ad1[i-325]*3/2,385-ad2[i-325]*3/2);
						printf("line %d,%d,%d,%d,YELLOW\xff\xff\xff",135+ad1[i-325]*3/2,385-ad2[i-325]*3/2,135+ad1[i-325+1]*3/2,385-ad2[i-325+1]*3/2);
					}
				//	delay_ms(100);
				//	printf("fill 0,0,651,385,BLACK\xFF\xFF\xFF");
				}
			}
			//Single
			else if(Trigger_ANS==2)
			{
				if(Trigger_flag==1)
				{
					single_flag=0;
				//	printf("fill 0,0,651,385,BLACK\xFF\xFF\xFF");
					printf("ref 1\xFF\xFF\xFF");
					delay_ms(30);
					for(i=TriggerPoint-offset,j=0;j<650;j++,i++)
					{
						//printf("fill %d,%d,1,1,YELLOW\xFF\xFF\xFF",0+ad1[i-325]*3/2,385-ad2[i-325]*3/2);
						printf("line %d,%d,%d,%d,YELLOW\xff\xff\xff",135+ad1[i-325]*3/2,385-ad2[i-325]*3/2,135+ad1[i-325+1]*3/2,385-ad2[i-325+1]*3/2);
					}
					//delay_ms(100);
				}
			}
 		}	
		if(fft_enable==1) {printf("ref 1\xFF\xFF\xFF");delay_ms(40);dofft(Channel);}
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
		if(Trigger_ANS!=2)HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S*K);
	}


void renew_data(void)
{
	//刷新曲线
	if(cursor_switch==1)
	{
		if(xy_enable==1)
		{
			if(cursor_mode==3)
			{
				cursor_mode=1;
				
			}
			if(cursor_mode==2)
			{
				printf("vis t16,1\xFF\xFF\xFF");
				printf("vis t17,1\xFF\xFF\xFF");
				printf("vis t18,0\xFF\xFF\xFF");
				printf("vis t19,0\xFF\xFF\xFF");
				printf("vis t20,0\xFF\xFF\xFF");
				printf("vis t21,0\xFF\xFF\xFF");
				printf("vis t22,1\xFF\xFF\xFF");
				printf("vis t23,1\xFF\xFF\xFF");
			}
			if(cursor_mode==1)
			{
				printf("vis t16,0\xFF\xFF\xFF");
				printf("vis t17,0\xFF\xFF\xFF");
				printf("vis t18,1\xFF\xFF\xFF");
				printf("vis t19,1\xFF\xFF\xFF");
				printf("vis t20,1\xFF\xFF\xFF");
				printf("vis t21,1\xFF\xFF\xFF");
				printf("vis t22,0\xFF\xFF\xFF");
				printf("vis t23,0\xFF\xFF\xFF");
			}
		}
		else if(xy_enable==0)
		{
			if(cursor_mode==2)
			{
				printf("vis t16,0\xFF\xFF\xFF");
				printf("vis t17,0\xFF\xFF\xFF");
				printf("vis t18,1\xFF\xFF\xFF");
				printf("vis t19,1\xFF\xFF\xFF");
				printf("vis t20,1\xFF\xFF\xFF");
				printf("vis t21,1\xFF\xFF\xFF");
				printf("vis t22,0\xFF\xFF\xFF");
				printf("vis t23,0\xFF\xFF\xFF");
			}
			if(cursor_mode==1)
			{
				printf("vis t16,0\xFF\xFF\xFF");
				printf("vis t17,0\xFF\xFF\xFF");
				printf("vis t18,1\xFF\xFF\xFF");
				printf("vis t19,1\xFF\xFF\xFF");
				printf("vis t20,1\xFF\xFF\xFF");
				printf("vis t21,1\xFF\xFF\xFF");
				printf("vis t22,0\xFF\xFF\xFF");
				printf("vis t23,0\xFF\xFF\xFF");
			}
			if(cursor_mode==3)
			{
				printf("vis t16,1\xFF\xFF\xFF");
				printf("vis t17,1\xFF\xFF\xFF");
				printf("vis t18,0\xFF\xFF\xFF");
				printf("vis t19,0\xFF\xFF\xFF");
				printf("vis t20,0\xFF\xFF\xFF");
				printf("vis t21,0\xFF\xFF\xFF");
				printf("vis t22,1\xFF\xFF\xFF");
				printf("vis t23,1\xFF\xFF\xFF");
			}
		}
	}
	
	
	//刷新垂直偏移
	if(CH1_enable==1)	printf("vis t29,1\xFF\xFF\xFF");
	else printf("vis t29,0\xFF\xFF\xFF");
	if(CH2_enable==1)	printf("vis t30,1\xFF\xFF\xFF");
	else printf("vis t30,0\xFF\xFF\xFF");
	printf("move t29,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(180-1.5*offset_ch1),(int)(180-1.5*(offset_ch1)));
	printf("move t30,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(180-1.5*offset_ch2),(int)(180-1.5*(offset_ch2)));

	if(Channel==0)
	{
		if(measure_voltage_V(offset_ch1+128,1)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
		else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
	}
	else
	{
		if(measure_voltage_V(offset_ch2+128,2)<0) printf("t9.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
		else printf("t9.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
	}
	
	//刷新触发阈值
	if(Trigger_state==1|Trigger_state==2)
	{
		if(measure_voltage_V(Trigger_set_offset_ch1+128,1)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch1+128,1));
		else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch1+128,1));
	}
	else if(Trigger_state==3|Trigger_state==4)
	{
		if(measure_voltage_V(Trigger_set_offset_ch2+128,2)<0) printf("t11.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch2+128,2));
		else printf("t11.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch2+128,2));
	}
	
	//刷新触发线位置
	if(Trigger_state==1|Trigger_state==2)
	{
		printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1)),(int)(192-1.5*(Trigger_set_offset_ch1+offset_ch1)));
	}
	else if(Trigger_state==3|Trigger_state==4)
	{
		printf("move t25,0,%d,0,%d,0,30\xFF\xFF\xFF",(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2)),(int)(192-1.5*(Trigger_set_offset_ch2+offset_ch2)));
	}
	//刷新参数
	//显示核磁共振参数
	if(parament_flag==1)
	{
		printf("vis t31,0\xFF\xFF\xFF");
		printf("vis t32,0\xFF\xFF\xFF");
		printf("vis t33,0\xFF\xFF\xFF");
		printf("vis t34,0\xFF\xFF\xFF");
		printf("vis t35,0\xFF\xFF\xFF");
		printf("vis t36,0\xFF\xFF\xFF");
		
		printf("vis t52,1\xFF\xFF\xFF");
		printf("vis t55,1\xFF\xFF\xFF");		
		printf("vis t51,1\xFF\xFF\xFF");
		printf("vis t54,1\xFF\xFF\xFF");
		printf("vis t47,1\xFF\xFF\xFF");
		printf("vis t48,1\xFF\xFF\xFF");		
		printf("vis t53,1\xFF\xFF\xFF");
		printf("vis t56,1\xFF\xFF\xFF");
		printf("vis t27,0\xFF\xFF\xFF");
		printf("vis t28,0\xFF\xFF\xFF");
		printf("t51.txt=\"励磁电流：\"\xff\xff\xff");
		printf("t52.txt=\"射频幅度：\"\xff\xff\xff");
		printf("t53.txt=\"毫特计：\"\xff\xff\xff");
		printf("t47.txt=\"频率：\"\xff\xff\xff");
	}
	//显示曲线参数
	else if(parament_flag==0&&cursor_switch==1)
	{
		printf("vis t31,0\xFF\xFF\xFF");
		printf("vis t32,0\xFF\xFF\xFF");
		printf("vis t33,0\xFF\xFF\xFF");
		printf("vis t34,0\xFF\xFF\xFF");
		printf("vis t35,0\xFF\xFF\xFF");
		printf("vis t36,0\xFF\xFF\xFF");
		
		printf("vis t47,0\xFF\xFF\xFF");
		printf("vis t48,0\xFF\xFF\xFF");
	//	printf("vis t53,0\xFF\xFF\xFF");
//		printf("vis t56,0\xFF\xFF\xFF");
		printf("vis t27,0\xFF\xFF\xFF");
		printf("vis t28,0\xFF\xFF\xFF");
		printf("vis t51,1\xFF\xFF\xFF");
		printf("vis t52,1\xFF\xFF\xFF");
		printf("vis t53,1\xFF\xFF\xFF");
		printf("vis t54,1\xFF\xFF\xFF");
		printf("vis t55,1\xFF\xFF\xFF");
		printf("vis t56,1\xFF\xFF\xFF");
		
		if(cursor_mode==1)
		{
			printf("t52.txt=\"CH1电压1：\"\xff\xff\xff");
			printf("t51.txt=\"CH1电压2：\"\xff\xff\xff");
			printf("t53.txt=\"电压差：\"\xff\xff\xff");
		}
		else if(cursor_mode==2)
		{
			printf("t52.txt=\"CH2电压1：\"\xff\xff\xff");
			printf("t51.txt=\"CH2电压2：\"\xff\xff\xff");
			printf("t53.txt=\"电压差：\"\xff\xff\xff");
		}
		else if(cursor_mode==3)
		{
			if(fft_enable==0)
			{
				printf("t52.txt=\"时间1：\"\xff\xff\xff");
				printf("t51.txt=\"时间2：\"\xff\xff\xff");
				printf("t53.txt=\"时间差：\"\xff\xff\xff");
			}
			else
			{
				printf("t52.txt=\"频率1：\"\xff\xff\xff");
				printf("t51.txt=\"频率2：\"\xff\xff\xff");
				printf("t53.txt=\"频率差：\"\xff\xff\xff");
			}
		}
		switch(cursor_mode)
		{
			case 1:
			{
				if(fft_enable==1)
				{
					printf("t55.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_fft(y1,1));
					printf("t54.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_fft(y2,1));
					printf("t56.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_fft(y1,1)-cursor_measure_voltage_V_fft(y2,1));
					break;
				}
				if(cursor_measure_voltage_V(y1,1)<0) printf("t55.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,1));
				else printf("t55.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,1));
				if(cursor_measure_voltage_V(y2,1)<0) printf("t54.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y2,1));
				else printf("t54.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y2,1));
				if(cursor_measure_voltage_V(y1,1)-cursor_measure_voltage_V(y2,1)<0)
				printf("t56.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,1)-cursor_measure_voltage_V(y2,1));
				else printf("t56.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,1)-cursor_measure_voltage_V(y2,1));
				
			}break;
			case 2:
			{
				if(fft_enable==1)
				{
					printf("t55.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_fft(y1,2));
					printf("t54.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_fft(y2,2));
					if(cursor_measure_voltage_V_fft(y1,2)-cursor_measure_voltage_V_fft(y2,2)<0)
					printf("t56.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_fft(y1,2)-cursor_measure_voltage_V_fft(y2,2));
					else printf("t56.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_fft(y1,2)-cursor_measure_voltage_V_fft(y2,2));
					break;
				}
				if(xy_enable==1)
				{
					if(cursor_measure_voltage_V_xy(x1,2)<0) printf("t55.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_xy(x1,2));
					else printf("t55.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_xy(x1,2));
					if(cursor_measure_voltage_V_xy(x2,2)<0) printf("t54.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(x2,2));
					else printf("t54.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_xy(x2,2));
					if(cursor_measure_voltage_V_xy(x1,2)-cursor_measure_voltage_V_xy(x2,2)<0) printf("t56.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_xy(x1,2)-cursor_measure_voltage_V_xy(x2,2));
					else printf("t56.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_xy(x1,2)-cursor_measure_voltage_V_xy(x2,2));
					
					break;
				}
				if(cursor_measure_voltage_V(y1,2)<0) printf("t55.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,2));
				else printf("t55.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,2));
				if(cursor_measure_voltage_V(y2,2)<0) printf("t54.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y2,2));
				else printf("t54.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y2,2));
				if(cursor_measure_voltage_V(y1,2)-cursor_measure_voltage_V(y2,2)<0) printf("t56.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,2)-cursor_measure_voltage_V(y2,2));
				else printf("t56.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,2)-cursor_measure_voltage_V(y2,2));
			}break;
			case 3:
			{
				if(xy_enable==1) break;
				if(measure_time_us(x1)>1000) printf("t55.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(x1));
				else printf("t55.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(x1));
				if(measure_time_us(x2)>1000) printf("t54.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(x2));
				else printf("t54.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(x2));
				if(measure_time_us(x1)-measure_time_us(x2)>1000) printf("t56.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(x1)-measure_time_ms(x2));
				else if(measure_time_us(x1)-measure_time_us(x2)>0) printf("t56.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(x1)-measure_time_us(x2));
				else if(measure_time_us(x1)-measure_time_us(x2)<-1000) printf("t56.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(x1)-measure_time_ms(x2));
				else if(measure_time_us(x1)-measure_time_us(x2)<=0) printf("t56.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(x1)-measure_time_us(x2));
				
				if(fft_enable==1)
				{
					if(measure_freq_Hz_fft(x1)<1000) printf("t55.txt=\"%.0fHz\"\xff\xff\xff",measure_freq_Hz_fft(x1));
					else printf("t55.txt=\"%.2fKHz\"\xff\xff\xff",measure_freq_KHz_fft(x1));
					if(measure_freq_Hz_fft(x2)<1000) printf("t54.txt=\"%.0fHz\"\xff\xff\xff",measure_freq_Hz_fft(x2));
					else printf("t54.txt=\"%.2fKHz\"\xff\xff\xff",measure_freq_KHz_fft(x2));
					if(measure_freq_Hz_fft(x1)-measure_freq_Hz_fft(x2)<1000&&measure_freq_Hz_fft(x1)-measure_freq_Hz_fft(x2)>-1000)
						printf("t56.txt=\"%.0fHz\"\xff\xff\xff",measure_freq_Hz_fft(x1)-measure_freq_Hz_fft(x2));
					else printf("t56.txt=\"%.2fKHz\"\xff\xff\xff",measure_freq_KHz_fft(x1)-measure_freq_KHz_fft(x2));
					
				}
			}break;
		}
	}
	//显示测量参数
	else if(parament_flag==0&&cursor_switch==0)
	{
		printf("vis t51,1\xFF\xFF\xFF");

		printf("vis t52,1\xFF\xFF\xFF");

		printf("vis t53,1\xFF\xFF\xFF");

		printf("vis t54,1\xFF\xFF\xFF");
		printf("vis t55,1\xFF\xFF\xFF");
		printf("vis t56,1\xFF\xFF\xFF");		
		printf("vis t47,1\xFF\xFF\xFF");
		
		printf("vis t48,0\xFF\xFF\xFF");
		printf("vis t27,1\xFF\xFF\xFF");
		printf("vis t28,1\xFF\xFF\xFF");
		
		printf("vis t31,1\xFF\xFF\xFF");
		printf("vis t32,1\xFF\xFF\xFF");
		printf("vis t33,1\xFF\xFF\xFF");
		printf("vis t34,1\xFF\xFF\xFF");
		printf("vis t35,1\xFF\xFF\xFF");
		printf("vis t36,1\xFF\xFF\xFF");
		//测量电压VPP
		printf("t52.txt=\"峰峰值：\"\xff\xff\xff");
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
			printf("t55.txt=\"%.2fV\"\xff\xff\xff",Vpp1_sum/Num);
			printf("t47.txt=\"%.2fV\"\xff\xff\xff",Vpp2_sum/Num);
			Vpp1_sum=0;
			Vpp2_sum=0;
		}
		//测量频率周期
		printf("t51.txt=\"周期：\"\xff\xff\xff");
		printf("t53.txt=\"频率：\"\xff\xff\xff");
		static int j=0;
		
		findzeropoint_ch1(&ZeroPoint1,&ZeroPoint2);
		if(measure_cycletime_us(ZeroPoint1,ZeroPoint2)<1000)
		//printf("t37.txt=\"%d\"\xff\xff\xff",ZeroPoint1-ZeroPoint2);
		printf("t54.txt=\"%.1fus\"\xff\xff\xff",measure_cycletime_us(ZeroPoint1,ZeroPoint2));
		else printf("t54.txt=\"%.1fms\"\xff\xff\xff",measure_cycletime_ms(ZeroPoint1,ZeroPoint2));
		
		if(measure_freq_Hz(ZeroPoint1,ZeroPoint2)<1000)
		printf("t56.txt=\"%.0fHz\"\xff\xff\xff",measure_freq_Hz(ZeroPoint1,ZeroPoint2));
		else printf("t56.txt=\"%.2fKHz\"\xff\xff\xff",measure_freq_kHz(ZeroPoint1,ZeroPoint2));
		if(ch1_voltage_max-ch1_voltage_min<0.2) 
		{
			printf("t54.txt=\"0us\"\xff\xff\xff");
			printf("t56.txt=\"0Hz\"\xff\xff\xff");
		}
	
		findzeropoint_ch2(&ZeroPoint1,&ZeroPoint2);
		if(measure_cycletime_us(ZeroPoint1,ZeroPoint2)<1000)
		printf("t27.txt=\"%.1fus\"\xff\xff\xff",measure_cycletime_us(ZeroPoint1,ZeroPoint2));
		else printf("t27.txt=\"%.1fms\"\xff\xff\xff",measure_cycletime_ms(ZeroPoint1,ZeroPoint2));
		
		if(measure_freq_Hz(ZeroPoint1,ZeroPoint2)<1000)
		printf("t28.txt=\"%.0fHz\"\xff\xff\xff",measure_freq_Hz(ZeroPoint1,ZeroPoint2));
		else printf("t28.txt=\"%.2fKHz\"\xff\xff\xff",measure_freq_kHz(ZeroPoint1,ZeroPoint2));
		if(ch2_voltage_max-ch2_voltage_min<0.2) 
		{
			printf("t27.txt=\"0us\"\xff\xff\xff");
			printf("t28.txt=\"0Hz\"\xff\xff\xff");
		}
	}
	//不显示
	else
	{
		printf("vis t51,0\xFF\xFF\xFF");
		printf("vis t52,0\xFF\xFF\xFF");		
		printf("vis t53,0\xFF\xFF\xFF");
		printf("vis t54,0\xFF\xFF\xFF");
		printf("vis t55,0\xFF\xFF\xFF");
		printf("vis t56,0\xFF\xFF\xFF");		
		printf("vis t47,0\xFF\xFF\xFF");
		printf("vis t48,0\xFF\xFF\xFF");
		printf("vis t27,0\xFF\xFF\xFF");
		printf("vis t28,0\xFF\xFF\xFF");
		printf("vis t31,0\xFF\xFF\xFF");
		printf("vis t32,0\xFF\xFF\xFF");
		printf("vis t33,0\xFF\xFF\xFF");
		printf("vis t34,0\xFF\xFF\xFF");
		printf("vis t35,0\xFF\xFF\xFF");
		printf("vis t36,0\xFF\xFF\xFF");
	}
	
	

//	

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
	//25Hz采样
	static int p=0;
	static int j=0;
	LCDY[j]=ADC_Value[2];
	SPFD[j]=ADC_Value[5];
	HTJ[j]=ADC_Value[6];
	
	j++;p++;
	if(j==Num0) j=0;
	temp_int=avg_Filter_int(LCDY,Num0);
	temp_d=(double)(temp_int)/65536*3.3;
	//temp_d=First_Filter(temp_d);
	if(temp_d*4000-current_offset<0) temp_d=current_offset/4000.0000;
	//printf("LCDY=%.2f\xff\xff\xff",temp_d*4000-current_offset);
	//2.5Hz
	if(p==200) printf("t54.txt=\"%.0fmA\"\xff\xff\xff",temp_d*4000-current_offset);
	temp_int=avg_Filter_int(HTJ,Num0);
	temp_d=(double)(temp_int)/65536*3.3;
	//printf("HTJ=%.1f\xff\xff\xff",(temp_d-1.66)*-6/3*1000);
	if(p==200) printf("t56.txt=\"%.0fmT\"\xff\xff\xff",(temp_d-1.61)*-6/3*1000);
	temp_int=avg_Filter_int(SPFD,Num0);
	temp_d=(double)(temp_int)/65536*3.3;
//	printf("SPFD=%.2f\xff\xff\xff",temp_d*(4.26+9.9)/4.26);
	if(p==200) printf("t55.txt=\"%.2fV\"\xff\xff\xff",temp_d*4);
	if(p==200) p=0;
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
	HAL_DAC_SetValue(&hdac1,DAC_CHANNEL_1,DAC_ALIGN_12B_R,4096.00/3.30*((1.23+del_zero_ch1)+(0.0031+del_k_ch1)*offset));
}

void set_offset_ch2(int16_t offset)
{
	HAL_DAC_SetValue(&hdac1,DAC_CHANNEL_2,DAC_ALIGN_12B_R,4096.00/3.30*((1.22+del_zero_ch2)+(0.0031+del_k_ch2)*offset));
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{	
//	if(htim->Instance==htim5.Instance)
//	{	
//		printf("cle 1,255\xff\xff\xff");
//		HAL_TIM_Base_Stop_IT(&htim4);
//		timer4=TIM4->CNT;
//		freqency=(time_50000*50000+timer4)*2;
//		time_50000=0;
//		TIM4->CNT=0;	
//		HAL_TIM_Base_Start_IT(&htim4);
//		tim5_flag=1;
//		if(tim5_flag==1) printf("t48.txt=\"%d\"\xff\xff\xff",(int)(freqency*1.0017));
//		
//	}
//	if(htim->Instance==htim4.Instance)
//	{	
//		time_50000++;
//	}
  if(htim->Instance==htim3.Instance)
	{	
		tim3_counter++;
		tim3_counter_1++;
		HAL_UART_Receive_IT(&huart1,RxData,8);
		printf("t48.txt=\"%sHz\"\xff\xff\xff",RxData);
		//printf("t48.txt=\"2Hz\"\xff\xff\xff");
		if(tim3_counter_1==300) {renew_data();tim3_counter_1=0;}
		if(parament_flag==1) disp_signal();
		//1.25Hz
		if(tim3_counter==100) 
		{
			tim3_counter=0;
			if(flag==1&&long_counter==0)
			{
				if(Trigger_ANS!=2)flag=0;
				display_osc();
			}
		}
		ADC_8CH();
		set_offset_ch1(offset_ch1);
		set_offset_ch2(offset_ch2);
	}
	if(htim->Instance==htim5.Instance)
	{	
		Key_Scan();
		do_key();
		CH1_status=0;
		CH2_status=0;
	}
}
	


