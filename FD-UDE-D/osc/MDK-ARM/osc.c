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
//测量值取Num个平均值，波形取K个平均值,采样点数量S
#define Num 3
#define K 1
#define S 40000
#define DelayTime 50
#define DelayTime2 0
uint32_t tim3_counter,tim2_counter,tim1_counter,tim3_counter_1;
int16_t ad1[S*K],ad2[S*K];
uint16_t i,j;
int16_t TriggerPoint=1000;
uint8_t Trigger_set=128;
int16_t Trigger_set_offset_ch1=0;
int16_t Trigger_set_offset_ch2=0;
_Bool CH1_enable=1,CH2_enable=0,xy_enable=0,tim3_flag=0,CH1_status,CH2_status,fft_enable=0;
//菜单1相关的变量
uint8_t menu_status=10,Ouhe=0,Ouhe1=0,Channel=0,time_per_grid=6,voltage_per_grid_1=6,voltage_per_grid=4,Trigger_state=1;

//菜单2相关的变量
uint8_t menu2_status=0;
int16_t caliboration_ch1=0;
int16_t caliboration_ch2=0;
uint8_t Trigger_ANS=0;
uint8_t Trigger_flag=0;
uint8_t single_flag,single_flag_1,single_flag_2;
uint8_t parament_flag=0; 

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

//
float k,t;
int16_t chaosheng_table[90]=
{
	  0x7F,0xC4,0xF3,0xFD,0xDF,0xA3,0x5B,0x1F,0x01,0x0B,0x3A,
	  0x7F,0xC4,0xF3,0xFD,0xDF,0xA3,0x5B,0x1F,0x01,0x0B,0x3A,
	  0x7F,0xC4,0xF3,0xFD,0xDF,0xA3,0x5B,0x1F,0x01,0x0B,0x3A,
	  0x7F,0xC4,0xF3,0xFD,0xDF,0xA3,0x5B,0x1F,0x01,0x0B,0x3A,
	  0x7F,0xC4,0xF3,0xFD,0xDF,0xA3,0x5B,0x1F,0x01,0x0B,0x3A,
	  0x7F,0xC4,0xF3,0xFD,0xDF,0xA3,0x5B,0x1F,0x01,0x0B,0x3A,
	  0x7F,0xC4,0xF3,0xFD,0xDF,0xA3,0x5B,0x1F,0x01,0x0B,0x3A,
		0x7F,0xC4,0xF3,0xFD,0xDF,0xA3,0x5B,0x1F,0x01,0x0B,0x3A
};

//单片机adc信号采集
uint32_t ADC_Value[100];

int temp_int;
double temp_d,temp_d_last;

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
	delay_ms(5000);
	Filter_Init();
	HAL_ADCEx_Calibration_Start(&hadc1, ADC_CALIB_OFFSET, ADC_SINGLE_ENDED);
	HAL_ADC_Start_DMA(&hadc1, (uint32_t*)&ADC_Value, 100);
	HAL_TIM_Base_Start_IT(&htim3);
	
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
	//10：2CH 01：onlyCH1 
 	HAL_GPIO_WritePin(DIO_S1_GPIO_Port,DIO_S1_Pin,GPIO_PIN_RESET);
	HAL_GPIO_WritePin(DIO_S2_GPIO_Port,DIO_S2_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(DIO_RA0_GPIO_Port,DIO_RA0_Pin,GPIO_PIN_RESET);
//	HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(DIO_RA1_GPIO_Port,DIO_RA1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(RLY1_GPIO_Port,RLY1_Pin,GPIO_PIN_SET);
//	HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_SET);
//	HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
//	HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
	HAL_GPIO_WritePin(HC_C1_GPIO_Port,HC_C1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(HC_B1_GPIO_Port,HC_B1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(HC_A1_GPIO_Port,HC_A1_Pin,GPIO_PIN_SET);
	HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_RESET);
	HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
	HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_RESET);
	HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_RESET);
	
//	HAL_GPIO_WritePin(RLY0_GPIO_Port,RLY0_Pin,GPIO_PIN_SET);
//					HAL_GPIO_WritePin(HC_C0_GPIO_Port,HC_C0_Pin,GPIO_PIN_RESET);
//						HAL_GPIO_WritePin(HC_B0_GPIO_Port,HC_B0_Pin,GPIO_PIN_SET);
//						HAL_GPIO_WritePin(HC_A0_GPIO_Port,HC_A0_Pin,GPIO_PIN_SET);
	
	__HAL_TIM_ENABLE_DMA(&htim2,TIM_DMA_CC1);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC1);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC2);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC3);
	__HAL_TIM_ENABLE_DMA(&htim1,TIM_DMA_CC4);
	__HAL_DMA_DISABLE_IT(&hdma_tim2_ch1, DMA_IT_HT);
	HAL_TIM_PWM_Start(&htim2,TIM_CHANNEL_1);
		HAL_TIM_PWM_Start(&htim2,TIM_CHANNEL_2);
	TIM1->PSC=2-1;
	TIM1->ARR=3-1;
	//TIM1->CCR1=2;
	TIM2->PSC=2-1;
	TIM2->ARR=10-1;
	TIM2->CCR1=2;
	TIM2->CCR2=2;
	
	TIM4->PSC=200;
	TIM4->ARR=1000;
	TIM4->CCR3=520;
	HAL_TIM_PWM_Start(&htim4,TIM_CHANNEL_3);
	
	//屏幕刷新率
	//200M/(psc+1)/(arr+1)
	//25Hz
	printf("page 0\xff\xff\xff");
	TIM3->PSC=100-1;
	TIM3->ARR=200-1;
	cursor_off();
	
		
	renew_menu2();
	renew_menu1();
	//renew_timeorfreq();
	HAL_NVIC_EnableIRQ(EXTI9_5_IRQn);
	printf("t3.txt=\"5us\"\xFF\xFF\xFF");
	printf("t5.txt=\"200mV\"\xFF\xFF\xFF");

}

void display_osc(void)
{

		switch(time_per_grid)
		{
			case 5:t=1;break;//2us
			case 6:t=1.0/2.5;break;//5us
			case 7:t=1.0/5.0;break;//10us
			case 8:t=1.0/10.0;break;//20us
			case 9:t=1.0/25.0;break;//50us
			case 10:t=1.0/50.0;break;//100us
		}
		for(int i=0;i<S*K;i++) 
		{	
			//printf("mem2[%d]=%x\xff\xff\xff",i,mem2[i]);
			temp0=((mem2[i]%256)+128)%256;
			temp=((mem2[i]/256)+128)%256;
			if(temp-128>127/1.25) temp=127/1.25+128;
			else if(temp-128<-128/1.25) temp=-128/1.25+128;
			ad1[i+(int)(88*t)]=((int)(((temp-128)*1.25))+128)%256;
			if(temp0-128>127/1.25) temp0=127/1.25+128;
			else if(temp0-128<-128/1.25) temp0=-128/1.25+128;
			ad2[i]=((int)(((temp0-128)*1.25))+128)%256;
		}
		for(int i=0;i<88*t;i++)
		{
			if(t>=0.4)
			{
				if(i>=0&&i<=11*t) k=1;
				else if(i>11*t&&i<=22*t) k=0.7;
				else if(i>22*t&&i<=33*t) k=0.6;
				else if(i>33*t&&i<=44*t) k=0.6;
				else if(i>44*t&&i<=55*t) k=0.65;
				else if(i>55*t&&i<=66*t) k=0.6;
				else if(i>66*t&&i<=77*t) k=0.55;
				else if(i>77*t&&i<=88*t) k=0.4;
				
				if(voltage_per_grid==8) k*=0.2;
				if(voltage_per_grid==7) k*=0.4;
				if(voltage_per_grid==6) k*=1;
				if(voltage_per_grid==5) k*=2;
				if(voltage_per_grid<=4) k*=4;
				
				
				ad1[i]=(chaosheng_table[(int)(i/t)]-128)*k+128;
				if(ad1[i]>255) ad1[i]=255;
				if(ad1[i]<0) ad1[i]=0;
			}
//			if(time_per_grid==7) {ad1[0]=255;ad1[1]=0;ad1[2]=128;ad1[3]=224;ad1[4]=32;ad1[5]=128;ad1[6]=204;
//				ad1[7]=50;ad1[8]=128;ad1[9]=195;ad1[10]=62;ad1[11]=128;ad1[12]=195;ad1[13]=65;ad1[14]=128;ad1[15]=180;
//				ad1[16]=76;ad1[17]=128;ad1[18]=144;ad1[19]=108;ad1[20]=128;ad1[21]=128;}
//				
//			if(time_per_grid==8) {ad1[0]=255;ad1[1]=0;ad1[2]=255;ad1[3]=0;ad1[4]=224;ad1[5]=32;
//													ad1[6]=192;ad1[7]=64;ad1[8]=128;ad1[9]=160;ad1[10]=96;ad1[11]=128;
//													ad1[12]=128;ad1[13]=128;ad1[14]=128;}
//			
//			if(time_per_grid==9) {ad1[0]=255;ad1[1]=0;ad1[2]=255;ad1[3]=0;ad1[4]=128;ad1[5]=128;ad1[6]=128;ad1[7]=128;ad1[8]=128;}
//				
//			if(time_per_grid==10) {ad1[0]=255;ad1[1]=0;ad1[2]=128;ad1[3]=128;ad1[4]=128;ad1[5]=128;}
		}
//		//取均值
//		for(int i=0;i<S;i++) 
//		{
//			temp=0;
//			temp0=0;
//			for(int j=0;j<K;j++)
//			{
//				temp+=ad1[K*i+j];
//				temp0+=ad2[K*i+j];
//			}
//			ad1[i]=temp/K;
//			ad2[i]=temp0/K;
//			if(ad1[i]>255) ad1[i]=255;
//			else if(ad1[i]<0) ad1[i]=0;
//			if(ad2[i]>255) ad2[i]=255;
//			else if(ad2[i]<0) ad2[i]=0;
//		}
		
		
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
//				printf("\x01\xff\xff\xff");//确保透传结束
//				printf("\x01\xff\xff\xff");//确保透传结束
//				printf("ref 1\xFF\xFF\xFF");
//				delay_ms(20);
//				for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
//				{
//					printf("line %d,%d,%d,%d,YELLOW\xff\xff\xff",j,384-(int)(1.5*ad1[i-325]),j+1,384-(int)(1.5*ad1[i-324]));
//				}
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
//					printf("ref 1\xFF\xFF\xFF");
//					delay_ms(20);
//					for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
//					{
//						printf("line %d,%d,%d,%d,YELLOW\xff\xff\xff",j,384-(int)(1.5*ad1[i-325]),j+1,384-(int)(1.5*ad1[i-324]));
//					}
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
//		if(CH2_enable==1)
//		{
//			if(Trigger_ANS==0)
//			{
//				//Auto输出通道2
//				CH2_status=1;
////				HAL_UART_Receive(&huart4,RX_buffer,1,100);
//				printf("addt 1,1,651\xFF\xFF\xFF");
//				//HAL_UART_Receive(&huart1,RX_buffer,4,3);
//				//delay_ms(70);
//				delay_ms(DelayTime);
//				
////				while(RX_buffer[0]==0x00);
////				RX_buffer[0]=0x00;
//		//		dmatxflag=1;
//			//	HAL_UART_Transmit_DMA(&huart1,&ad2[i-325],1300);
//				for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
//				{
//					printf("%c",ad2[i-325]);
//					//printf("%c",((mem2[i]/256)+128)%256);
//				}
//				printf("\x01\xff\xff\xff");//确保透传结束
//		//		printf("ref 1\xFF\xFF\xFF");
//			//	delay_ms(20);
////				for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
////				{
////					printf("line %d,%d,%d,%d,BLUE\xff\xff\xff",j,384-(int)(1.5*ad2[i-325]),j+1,384-(int)(1.5*ad2[i-324]));
////				}
//			}
//			//Normal输出通道2
//			else if(Trigger_ANS==1)
//			{
//				if(Trigger_flag==1)
//				{
//					CH2_status=1;
//					printf("addt 1,1,651\xFF\xFF\xFF");
//					//HAL_UART_Receive(&huart1,RX_buffer,4,3);
//					delay_ms(DelayTime);
//			//		dmatxflag=1;
//				//	HAL_UART_Transmit_DMA(&huart1,&ad2[i-325],1300);
//					for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
//					{
//						printf("%c",ad2[i-325]);
//						//printf("%c",((mem2[i]/256)+128)%256);
//					}
//					printf("\x01\xff\xff\xff");//确保透传结束
//					delay_ms(20);
////					for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
////					{
////						printf("line %d,%d,%d,%d,BLUE\xff\xff\xff",j,384-(int)(1.5*ad2[i-325]),j+1,384-(int)(1.5*ad2[i-324]));
////					}
//				}
//			}
//			//Single输出通道2
//			else if(Trigger_ANS==2)
//			{
//				if(Trigger_flag==1&&single_flag==1)
//				{
//					if(single_flag_2==1)return;
//					single_flag_2=1;
//					single_flag=0;
//					CH2_status=1;
//					printf("addt 1,1,651\xFF\xFF\xFF");
//					//HAL_UART_Receive(&huart1,RX_buffer,4,3);
//					delay_ms(DelayTime);
//			//		dmatxflag=1;
//				//	HAL_UART_Transmit_DMA(&huart1,&ad2[i-325],1300);
//					for(i=TriggerPoint-offset,j=0;j<651;j++,i++)
//					{
//						printf("%c",ad2[i-325]);
//						//printf("%c",((mem2[i]/256)+128)%256);
//					}
//					printf("\x01\xff\xff\xff");//确保透传结束
//				}
//			}
//		}
//		//输出x-y曲线
//		if(xy_enable==1)
//		{
//			
//			//Auto
//			if(Trigger_ANS==0)
//			{
//				printf("ref 1\xFF\xFF\xFF");
//				delay_ms(20);
//				for(i=TriggerPoint-offset,j=0;j<650;j++,i++)
//				{
//					printf("fill %d,%d,1,1,YELLOW\xFF\xFF\xFF",0+ad1[i-325]*3/2,385-ad2[i-325]*3/2);
//				}
//				//delay_ms(100);
//			//	printf("fill 0,0,651,385,BLACK\xFF\xFF\xFF");
//				
//			}
//			//Normal
//			else if(Trigger_ANS==1)
//			{
//				if(Trigger_flag==1)
//				{
//					printf("ref 1\xFF\xFF\xFF");
//					delay_ms(20);
//					for(i=TriggerPoint-offset,j=0;j<650;j++,i++)
//					{
//						printf("fill %d,%d,1,1,YELLOW\xFF\xFF\xFF",0+ad1[i-325]*3/2,385-ad2[i-325]*3/2);
//					}
//				//	delay_ms(100);
//				//	printf("fill 0,0,651,385,BLACK\xFF\xFF\xFF");
//				}
//			}
//			//Single
//			else if(Trigger_ANS==2)
//			{
//				if(Trigger_flag==1)
//				{
//					single_flag=0;
//				//	printf("fill 0,0,651,385,BLACK\xFF\xFF\xFF");
//					printf("ref 1\xFF\xFF\xFF");
//					delay_ms(30);
//					for(i=TriggerPoint-offset,j=0;j<650;j++,i++)
//					{
//						printf("fill %d,%d,1,1,YELLOW\xFF\xFF\xFF",0+ad1[i-325]*3/2,385-ad2[i-325]*3/2);
//					}
//					//delay_ms(100);
//				}
//			}
// 		}	
//		if(fft_enable==1) {printf("ref 1\xFF\xFF\xFF");delay_ms(40);dofft(Channel);}
		if(Trigger_ANS!=2)flag=0;
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
		HAL_TIM_PWM_Start(&htim2,TIM_CHANNEL_1);
		HAL_TIM_PWM_Start(&htim2,TIM_CHANNEL_2);
		
	}


void renew_data(void)
{
	
  renew_timeorfreq();
	if(*(__IO uint32_t*)0x08019000==0xffffffff)	printf("vis t44,1\xFF\xFF\xFF");
	else printf("vis t44,0\xFF\xFF\xFF");
	//刷新参数
	if(parament_flag==0&&cursor_switch==1)
	{
			

		if(cursor_mode==1)
		{
			printf("vis t51,1\xFF\xFF\xFF");
			printf("t51.txt=\"电压2：\"\xff\xff\xff");
			printf("vis t52,1\xFF\xFF\xFF");
			printf("vis t54,1\xFF\xFF\xFF");
			printf("vis t55,1\xFF\xFF\xFF");
			printf("vis t1,1\xFF\xFF\xFF");
			printf("vis t0,1\xFF\xFF\xFF");
			printf("t52.txt=\"电压1：\"\xff\xff\xff");
			printf("t0.txt=\"电压差：\"\xff\xff\xff");
//				printf("vis t32,0\xFF\xFF\xFF");
//			printf("vis t33,0\xFF\xFF\xFF");
//			printf("vis t34,0\xFF\xFF\xFF");
//			printf("vis t35,0\xFF\xFF\xFF");
//			printf("vis t36,0\xFF\xFF\xFF");
//			
//			printf("vis t47,0\xFF\xFF\xFF");
//			printf("vis t48,0\xFF\xFF\xFF");
//			printf("vis t53,0\xFF\xFF\xFF");
//			printf("vis t56,0\xFF\xFF\xFF");
//			printf("vis t27,0\xFF\xFF\xFF");
//			printf("vis t28,0\xFF\xFF\xFF");
			
		}
//		else if(cursor_mode==2)
//		{
//			printf("t52.txt=\"CH2电压1：\"\xff\xff\xff");
//			printf("t51.txt=\"CH2电压2：\"\xff\xff\xff");
//		}
		else if(cursor_mode==3)
		{
			printf("vis t51,1\xFF\xFF\xFF");
			printf("vis t52,1\xFF\xFF\xFF");
			printf("vis t54,1\xFF\xFF\xFF");
			printf("vis t55,1\xFF\xFF\xFF");
			printf("vis t1,1\xFF\xFF\xFF");
			printf("vis t0,1\xFF\xFF\xFF");
			if(fft_enable==0)
			{
			
				printf("t52.txt=\"时间1：\"\xff\xff\xff");
				printf("t51.txt=\"时间2：\"\xff\xff\xff");
				printf("t0.txt=\"时间差：\"\xff\xff\xff");
			}
			else
			{
				printf("t52.txt=\"频率1：\"\xff\xff\xff");
				printf("t51.txt=\"频率2：\"\xff\xff\xff");
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
					break;
				}
				if(cursor_measure_voltage_V(y1,1)<0) printf("t55.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,1));
				else printf("t55.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,1));
				if(cursor_measure_voltage_V(y2,1)<0) printf("t54.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y2,1));
				else printf("t54.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y2,1));
				if(cursor_measure_voltage_V(y1,1)-cursor_measure_voltage_V(y2,1)<0)
					printf("t1.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,1)-cursor_measure_voltage_V(y2,1));
				else printf("t1.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,1)-cursor_measure_voltage_V(y2,1));
			}break;
			case 2:
			{
				if(fft_enable==1)
				{
					printf("t55.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_fft(y1,2));
					printf("t54.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_fft(y2,2));
					break;
				}
				if(xy_enable==1)
				{
					if(cursor_measure_voltage_V_xy(x1,2)<0) printf("t55.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_xy(x1,2));
					else printf("t55.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_xy(x1,2));
					if(cursor_measure_voltage_V_xy(x2,2)<0) printf("t54.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(x2,2));
					else printf("t54.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V_xy(x2,2));
					break;
				}
				if(cursor_measure_voltage_V(y1,2)<0) printf("t55.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,2));
				else printf("t55.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y1,2));
				if(cursor_measure_voltage_V(y2,2)<0) printf("t54.txt=\"%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y2,2));
				else printf("t54.txt=\"+%.2fV\"\xff\xff\xff",cursor_measure_voltage_V(y2,2));
			}break;
			case 3:
			{
				if(xy_enable==1) break;
				if(measure_time_us(x1)>1000) printf("t55.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(x1));
				else printf("t55.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(x1));
				if(measure_time_us(x2)>1000) printf("t54.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(x2));
				else printf("t54.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(x2));
				
				if(measure_time_us(x1)-measure_time_us(x2)>1000) printf("t1.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(x1)-measure_time_ms(x2));
				else if(measure_time_us(x1)-measure_time_us(x2)<-1000) printf("t1.txt=\"%.2fms\"\xff\xff\xff",measure_time_ms(x1)-measure_time_ms(x2));
				else if(measure_time_us(x1)-measure_time_us(x2)>=0) printf("t1.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(x1)-measure_time_us(x2));
				else if(measure_time_us(x1)-measure_time_us(x2)<0) printf("t1.txt=\"%.2fus\"\xff\xff\xff",measure_time_us(x1)-measure_time_us(x2));
				if(fft_enable==1)
				{
					if(measure_freq_Hz_fft(x1)<1000) printf("t55.txt=\"%.0fHz\"\xff\xff\xff",measure_freq_Hz_fft(x1));
					else printf("t55.txt=\"%.0fKHz\"\xff\xff\xff",measure_freq_KHz_fft(x1));
					if(measure_freq_Hz_fft(x2)<1000) printf("t54.txt=\"%.0fHz\"\xff\xff\xff",measure_freq_Hz_fft(x2));
					else printf("t54.txt=\"%.0fKHz\"\xff\xff\xff",measure_freq_KHz_fft(x2));
				}
			}break;
		}
	}
	//不显示
	else
	{
		printf("vis t0,0\xFF\xFF\xFF");
		printf("vis t1,0\xFF\xFF\xFF");	
		printf("vis t51,0\xFF\xFF\xFF");
		printf("vis t52,0\xFF\xFF\xFF");		
		printf("vis t53,0\xFF\xFF\xFF");
		printf("vis t54,0\xFF\xFF\xFF");
		printf("vis t55,0\xFF\xFF\xFF");
		for(int i=16;i<24;i++)
		printf("vis t%d,0\xff\xff\xff",i);
		if(caliboration_mode==0) printf("vis t24,0\xff\xff\xff");
		else printf("vis t24,1\xff\xff\xff");
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

//void disp_signal()
//{
//	//25Hz采样
//	static int p=0;
//	static int j=0;
//	LCDY[j]=ADC_Value[2];
//	SPFD[j]=ADC_Value[5];
//	HTJ[j]=ADC_Value[6];
//	
//	j++;p++;
//	if(j==Num0) j=0;
//	temp_int=avg_Filter_int(LCDY,Num0);
//	temp_d=(double)(temp_int)/65536*3.3;
//	//temp_d=First_Filter(temp_d);
//	if(temp_d<0) temp_d=0;
//	printf("LCDY=%.2f\xff\xff\xff",temp_d*4000);
//	//2.5Hz
//	if(p==200) printf("t54.txt=\"%.0fmA\"\xff\xff\xff",temp_d*4000);
//	temp_int=avg_Filter_int(HTJ,Num0);
//	temp_d=(double)(temp_int)/65536*3.3;
//	printf("HTJ=%.1f\xff\xff\xff",temp_d*-7/3*1000);
//	if(p==200) printf("t56.txt=\"%.0fmT\"\xff\xff\xff",(temp_d-3.1)*-7/3*1000);
//	temp_int=avg_Filter_int(SPFD,Num0);
//	temp_d=(double)(temp_int)/65536*3.3;
//	printf("SPFD=%.2f\xff\xff\xff",temp_d*4);
//	if(p==200) printf("t55.txt=\"%.2fV\"\xff\xff\xff",temp_d*4);
//	if(p==200) p=0;
//}

//void ADC_DMA(void)
//{
//	
//	if(ADC_flag==1)
//	{
//		ADC_flag=0;
//		for(int i=0;i<100;i++)
//		{
//			printf("ADC_Value[%d]=%d\xff\xff\xff",i,ADC_Value[i]);
//		}
//		//HAL_ADC_Start_DMA(&hadc1, (uint32_t*)&ADC_Value, 100);
//	}
//}

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
//		HAL_UART_Receive_IT(&huart1,RxData,8);
//		printf("t48.txt=\"%sHz\"\xff\xff\xff",RxData);
		//printf("t48.txt=\"2Hz\"\xff\xff\xff");
		if(tim3_counter_1==120) {renew_data();tim3_counter_1=0;if(tim3_counter==100)tim3_counter=80;}
//		if(parament_flag==1) disp_signal();
		//1.25Hz
		if(tim3_counter==100) //1000hz/100=10hz
		{
			tim3_counter=0;
			if(flag==1&&long_counter==0)
			{
				
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

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
	
	if(GPIO_Pin==GPIO_PIN_9)
	{
//		 HAL_NVIC_DisableIRQ(EXTI9_5_IRQn);
	  if(flag==0)
		{                                                                                                                                                                                                                                                   
			if(Trigger_ANS!=2)HAL_DMA_Start_IT(&hdma_tim2_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S*K);
			flag=2;
			TriggerPoint=325;
			Trigger_flag=1;
		}

	}
}
	


