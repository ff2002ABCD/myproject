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
#include "pid.h"
#include "pid2.h"
#include "function.h"
#include "AC.h"
#include "button.h"
#include "string.h"
#include "18B20.h"
#include "pt100.h"
OSC_STATE osc_state=FREE;
extern DMA_HandleTypeDef hdma_uart4_tx;
uint32_t tim3_counter,tim2_counter,tim1_counter,tim3_counter_1;
int16_t ad1[S*K],ad2[S*K];
uint16_t i,j;
int16_t TriggerPoint=1000;
uint8_t Trigger_set=128;
int16_t Trigger_set_offset_ch1=0;
int16_t Trigger_set_offset_ch2=0;
_Bool CH1_enable=1,CH2_enable=1,xy_enable=0,tim3_flag=0,CH1_status,CH2_status,fft_enable=0;
_Bool ready=0;
//菜单1相关的变量
uint8_t menu_status=9,Ouhe=0,Ouhe1=0,Channel=0,voltage_per_grid=6,Trigger_state=1;
TIME_PER_GRID time_per_grid;
VOLTAGE_PER_GRID voltage_per_grid,voltage_per_grid_1;

//菜单2相关的变量
uint8_t menu2_status=0;
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
uint8_t my_data[500];
uint8_t uart4_tx_buffer[500];  
volatile uint8_t uart4_dma_tx_complete = 0;

int flag;
uint16_t mem2[S*K];
uint16_t buffer1[S],buffer2[700],buffer3[S],buffer4[700];
int32_t temp,temp0;
int ADC_flag;
uint8_t RX_buffer[16];

int16_t offset=0;
int16_t offset_ch1=0;
int16_t offset_ch2=0;
const uint8_t target_data[4] = {0xFE, 0xFF, 0xFF, 0xFF}; 
const uint8_t target_data2[4] = {0xFD, 0xFF, 0xFF, 0xFF}; 
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


////单片机adc信号采集
//uint32_t ADC_Value[100];
//int LCDY[Num0];
//int HTJ[Num0];
//int SPFD[Num0];
//int temp_int;
//double temp_d,temp_d_last;

void Init_Osc(void)
{
	Filter_Init();
	HAL_ADCEx_Calibration_Start(&hadc1, ADC_CALIB_OFFSET, ADC_SINGLE_ENDED);
//	HAL_ADC_Start_DMA(&hadc1, (uint32_t*)&ADC_Value, 100);
	HAL_TIM_PWM_Start(&htim8,TIM_CHANNEL_1);
	HAL_TIM_PWM_Start(&htim8,TIM_CHANNEL_2);
	HAL_TIM_Base_Start_IT(&htim3);
	TIM5->PSC=200-1;
	TIM5->ARR=10000-1;//10ms
	HAL_TIM_Base_Start_IT(&htim5);
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
	HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
	__HAL_TIM_ENABLE_DMA(&htim8,TIM_DMA_CC1);
	__HAL_DMA_DISABLE_IT(&hdma_uart4_tx, DMA_IT_HT); 
	
//	TIM1->PSC=1-1;
//	//TIM1->CCR1=2;
	TIM8->PSC=500-1;
	TIM8->ARR=160-1;
	TIM8->CCR1=2;
	TIM8->CCR2=2;
	//屏幕刷新率
	//200M/(psc+1)/(arr+1)
	//25Hz
	TIM3->PSC=100-1;
	TIM3->ARR=200-1;//10khz
	HAL_UART_Receive_IT(&huart4, RX_buffer, 4);
	for(int i=0;i<800;i++)printf("\x01\xff\xff\xff");
	printf("cle 32,255\xff\xff\xff");
	HAL_DMA_Start_IT(&hdma_tim8_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S*K);
}

void display_osc(void)
{
	for(int i=0;i<S*K;i++) 
	{	
		temp0=((mem2[i]%256)+128)%256;//高8位通道1
		temp=((mem2[i]/256)+128)%256;//低8位通道2
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
			if(osc_state==FREE)
			{
				printf("addt 32,0,%d\xFF\xFF\xFF",DATA_NUM);
				osc_state=CH1_PREPARING;
			}
		}
	}
}


void renew_data(void)
{
	//刷新电压档位
	voltage_per_grid=mag_scale_now;
	switch(voltage_per_grid)
	{
		case _10V:
			HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
		break;
		case _5V:
			HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
		break;
		case _2V:
			HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
		break;
		case _1V:
			HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
		break;
		case _500mV:
			HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
		break;
		case _200mV:
			HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
		break;
		case _100mV:
			HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
		break;
		case _50mV:
			HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
		break;
		case _20mV:
			HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
		break;
//		case _10mV:
	}
	voltage_per_grid_1=light_scale_now+7;
	switch(voltage_per_grid_1)
	{
		case _10V:
			HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
			break;
		case _5V:
			HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
			break;
		case _2V:
			HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
			break;
		case _1V:
			HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
			break;
		case _500mV:
			HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
		break;
		case _200mV:
			HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
			break;
		case _100mV:
			HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
			break;
		case _50mV:
			HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
			break;
		case _20mV:
			HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
			break;
		case _10mV:
			HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
			HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_RESET);
			HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
			break;
			
	}
	time_per_grid=time_grid_now+1;
	//刷新时间档位
	switch(time_per_grid)
	{
		case _100ms:
			TIM8->PSC=500-1;
			TIM8->ARR=800-1;
			break;
		case _50ms:
			TIM8->PSC=500-1;
			TIM8->ARR=400-1;
			break;
		case _20ms:
			TIM8->PSC=500-1;
			TIM8->ARR=160-1;
			break;
		case _10ms:
			TIM8->PSC=500-1;
			TIM8->ARR=80-1;
			break;
		case _5ms:
			TIM8->PSC=500-1;
			TIM8->ARR=40-1;
			break;
		case _2ms:
			TIM8->PSC=500-1;
			TIM8->ARR=16-1;
			break;
		case _1ms:
			TIM8->PSC=500-1;
			TIM8->ARR=8-1;
			break;
		case _500us:
			TIM8->PSC=2-1;
			TIM8->ARR=1000-1;
			break;
		case _200us:
			TIM8->PSC=2-1;
			TIM8->ARR=400-1;
			break;
		case _100us:
			TIM8->PSC=2-1;
			TIM8->ARR=200-1;
			break;
		case _50us:
			TIM8->PSC=2-1;
			TIM8->ARR=100-1;
			break;
		case _20us:
			TIM8->PSC=2-1;
			TIM8->ARR=40-1;
			break;
		case _10us:
			TIM8->PSC=2-1;
			TIM8->ARR=20-1;
			break;
		case _5us:
			TIM8->PSC=2-1;
			TIM8->ARR=10-1;
			break;
		case _2us:
			TIM8->PSC=2-1;
			TIM8->ARR=4-1;
			break;
	}
	
	//刷新垂直偏移
		if(measure_voltage_V(offset_ch1+128,1)<0) printf("mag_offset.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));
		else printf("mag_offset.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch1+128,1));

		if(measure_voltage_V(offset_ch2+128,2)<0) printf("light_offset.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
		else printf("light_offset.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(offset_ch2+128,2));
	//刷新零点标志
		printf("move zero1,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch1),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch1)));
		printf("move zero2,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch2),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch2)));
	
	//刷新触发阈值
	if(Trigger_state==1|Trigger_state==2)
	{
		
		if(measure_voltage_V(Trigger_set_offset_ch1+128,1)<0) printf("trig_value.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch1+128,1));
		else printf("trig_value.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch1+128,1));
	}
	else if(Trigger_state==3|Trigger_state==4)
	{
		if(measure_voltage_V(Trigger_set_offset_ch2+128,2)<0) printf("trig_value.txt=\"%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch2+128,2));
		else printf("trig_value.txt=\"+%.2fV\"\xff\xff\xff",measure_voltage_V(Trigger_set_offset_ch2+128,2));
	}
	Trigger_state=trig_mode_now+1;
	//刷新触发线位置
	if(Trigger_state==1|Trigger_state==2)
	{
		printf("vis trig2,0\xff\xff\xff");
		printf("vis trig1,1\xff\xff\xff");
		printf("move trig1,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_down+grid_up)/2-1.5*(Trigger_set_offset_ch1+offset_ch1)),grid_left,(int)((grid_down+grid_up)/2-1.5*(Trigger_set_offset_ch1+offset_ch1)));
	}
	else if(Trigger_state==3|Trigger_state==4)
	{
		printf("vis trig1,0\xff\xff\xff");
		printf("vis trig2,1\xff\xff\xff");
		printf("move trig2,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_down+grid_up)/2-1.5*(Trigger_set_offset_ch2+offset_ch2)),grid_left,(int)((grid_down+grid_up)/2-1.5*(Trigger_set_offset_ch2+offset_ch2)));
	}
	//刷新耦合方式
	switch(Ouhe)
	{
		case 0:HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_SET);break;
		case 1:HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_RESET);break;
	}
	switch(Ouhe1)
	{
		case 0:HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_SET);break;
		case 1:HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_RESET);break;
	}
}

void set_offset_ch1(int16_t offset)
{
	HAL_DAC_SetValue(&hdac1,DAC_CHANNEL_1,DAC_ALIGN_12B_R,4096.00/3.30*((1.23+del_zero_ch1)+(0.0031+del_k_ch1)*offset));
}

void set_offset_ch2(int16_t offset)
{
	HAL_DAC_SetValue(&hdac1,DAC_CHANNEL_2,DAC_ALIGN_12B_R,4096.00/3.30*((1.23+del_zero_ch2)+(0.0031+del_k_ch2)*offset));
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{	

  if(htim->Instance==htim3.Instance)
	{	

		if(osc_state==CH1_PREPARE_OK)
		{
			osc_state=CH1_SENDING;
			for(i=TriggerPoint-offset,j=0;j<DATA_NUM;j++,i++)
			{
				my_data[j]=(uint8_t)ad1[i-(DATA_NUM-1)/2];	
			//	printf("%c",ad1[i-DATA_NUM/2]);
			}
			UART4_DMA_Send(my_data,DATA_NUM);
		//	printf("\x01\xff\xff\xff");//确保透传结束
		}
		else if(osc_state==CH2_PREPARE_OK)
		{
			osc_state=CH2_SENDING;
			for(i=TriggerPoint-offset,j=0;j<DATA_NUM;j++,i++)
			{
				
				my_data[j]=(uint8_t)ad2[i-(DATA_NUM-1)/2];
			//	printf("%c",ad2[i-DATA_NUM/2]);
			}
			UART4_DMA_Send(my_data,DATA_NUM);
	//		printf("\x01\xff\xff\xff");//确保透传结束
	//		CH2_status=0;
	//		HAL_TIM_PWM_Start(&htim8,TIM_CHANNEL_1);
	//		HAL_TIM_PWM_Start(&htim8,TIM_CHANNEL_2);
	//		HAL_DMA_Start_IT(&hdma_tim8_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S*K);
		}
	//	HAL_UART_Receive_IT(&huart4, RX_buffer, 4);
		tim3_counter++;
		tim3_counter_1++;

		if(tim3_counter_1>=1000) //10K/1000=10Hz
		{
			tim3_counter_1=0;
			if(osc_state==FREE)
			{

			//	temp_light_now=current_temperature;
				if(start_ctrl==1)	printf("T_light.txt=\"%.1f℃\"\xff\xff\xff",temp_light_now);
				else printf("T_light.txt=\"%.1f℃\"\xff\xff\xff",temp_light_set);
				if(start_ctrl==1)	printf("T_pool.txt=\"%.1f℃\"\xff\xff\xff",temp_pool_now);
				else printf("T_pool.txt=\"%.1f℃\"\xff\xff\xff",temp_pool_set);
		//		DAC_renew();
				renew_data();
				renew_menu();
			}
			output_ctrl1();
			
		}
		//1.25Hz
		if(tim3_counter>=100) //10K/100=10Hz
		{
			tim3_counter=0;
			if(flag==1)
			{
				if(Trigger_ANS!=2)flag=0;
				display_osc();
			}
		}
		set_offset_ch1(offset_ch1);
		set_offset_ch2(offset_ch2);
	}
	if(htim->Instance==htim5.Instance)//10ms
	{	
		Key_Scan();
		static int tim5_counter=0;
		tim5_counter++;
		//tim5_counter=0;
		if(tim5_counter>=2)//100/2=50Hz
		{	
			tim5_counter=0;
			//if(osc_state==FREE)
				do_key();
		}		
	}
	if (htim->Instance == TIM2) 
	{
		
		if(start_ctrl==0)
		{
			
			HAL_GPIO_WritePin(PWM_GPIO_PORT, PWM_GPIO_PIN, GPIO_PIN_RESET); 
		}
		else if(start_ctrl==1)
		{
			
			pwm_counter++;
			if (pwm_counter >= PWM_PERIOD) 
			{
				pwm_counter = 0;
			}
			if (pwm_counter < pwm_duty_cycle) 
			{
				HAL_GPIO_WritePin(PWM_GPIO_PORT, PWM_GPIO_PIN, GPIO_PIN_SET);
			} 
			else 
			{
				HAL_GPIO_WritePin(PWM_GPIO_PORT, PWM_GPIO_PIN, GPIO_PIN_RESET); 
			}
		}
	}
	if (htim->Instance == TIM4&&start_ctrl==1) 
	{
		static int tim4_counter=0;
		
		if(start_ctrl==0)
		{
			HAL_GPIO_WritePin(PWM_GPIO_PORT2, PWM_GPIO_PIN2, GPIO_PIN_RESET); 
		}
		else if(start_ctrl==1)
		{
			tim4_counter++;
			if(tim4_counter>=100)//100/100=1Hz
			{
				tim4_counter=0;
				temp_light_now = DS18B20_Get_Temperature()*0.0625;
				temp_pool_now=pt100_getTemperature();
			}
			
			pwm_counter2++;
			if (pwm_counter2 >= PWM_PERIOD2)
			{
					pwm_counter2 = 0;
			}
			if (pwm_counter2 < pwm_duty_cycle2)
			{
				HAL_GPIO_WritePin(PWM_GPIO_PORT2, PWM_GPIO_PIN2, GPIO_PIN_SET);
			} 
			else 
			{
				HAL_GPIO_WritePin(PWM_GPIO_PORT2, PWM_GPIO_PIN2, GPIO_PIN_RESET); 
			}
		}
	}
	if(htim->Instance==htim6.Instance)
	{	

		output_ctrl2();
	}
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == UART4) {
				if (memcmp(RX_buffer, target_data, 4) == 0) 
				{
					if(osc_state==CH1_PREPARING)
						osc_state=CH1_PREPARE_OK;
					else if(osc_state==CH2_PREPARING)
						osc_state=CH2_PREPARE_OK;
         //  printf("透传准备完成\xff\xff\xff");
					
				}
				else if (memcmp(RX_buffer, target_data2, 4) == 0)
				{
				//	printf("透传结束\xff\xff\xff");
					if(osc_state==CH1_SENDING)
					{
						printf("\x01\xff\xff\xff");
						osc_state=CH1_SEND_OK;
						printf("addt 32,1,%d\xFF\xFF\xFF",DATA_NUM);
						osc_state=CH2_PREPARING;
					}	
					else if(osc_state==CH2_SENDING)
					{
						printf("\x01\xff\xff\xff");
						osc_state=CH2_SEND_OK;
						HAL_TIM_PWM_Start(&htim8,TIM_CHANNEL_1);
						HAL_TIM_PWM_Start(&htim8,TIM_CHANNEL_2);
						HAL_DMA_Start_IT(&hdma_tim8_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S*K);
						osc_state=FREE;
					}
				}
				HAL_UART_Receive_IT(&huart4, RX_buffer, 4);
    }
}

HAL_StatusTypeDef UART4_DMA_Send(uint8_t *data, uint16_t size)
{
    if(size > 500) return HAL_ERROR; 
    
    uart4_dma_tx_complete = 0;

    memcpy(uart4_tx_buffer, data, size);
    
    HAL_StatusTypeDef status = HAL_UART_Transmit_DMA(&huart4, uart4_tx_buffer, size);
    
    if(status != HAL_OK)
    {
			
        return status;
    }
    
    return HAL_OK;
}


