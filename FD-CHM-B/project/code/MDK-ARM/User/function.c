#include "function.h"
#include "18b20.h"
#include "DS18B20_1.h"
#include "JLX256128G.h"
#include "adc.h"
#include "tim.h"
#include "gpio.h"

#define Num 30//取Num个pt100温度平均
#define qianwei 0.1

extern uint16_t count;
extern uchar bitmap_bytes[];
uint16_t adc_value,flag;
uint16_t dutyCycle = 0;//加热器pwm
char dC[10];
uint16_t Pi;
uint32_t n;
float flag_temp=0,voltage,TEMP,TEMP1,TEMP2,TEMP3,TEMP4,Resistor_pt100,TEMP_pt100,Sum_TEMP,Average_TEMP,K=49.4/6.2+1,Heater_set=50,timer,timer2,Vcc=5;
float Error,LastError,Sum_Error,Pout,Iout,Dout,T=100,Ti=10000,Ki,Kp=100,Kd=1000;
char vol[10],tim[10],TP[10],TP1[10],TP2[10],TP3[10],TP4[10],TP_pt100[10],Aver_TEMP[10],RES_pt100[10],Ht_set[10],iout[10],f[10];
float arr[Num];

void initial_arr(void)
{
	for(int i=0;i<Num;i++)
	{
		arr[i]=0;
	}
}

void System_Reset(void) 
{
	
	NVIC_SystemReset(); 
}

void start_led()
{	

	//测试lcd
		initial_lcd(); 
		clear_screen();  	 
		sprintf(Ht_set,"%.0f",Heater_set);
		StringPrint(10,1,Ht_set);
		disp_16x16(1,1,3);
		disp_16x16(2,1,4);
		disp_16x16(3,1,7);
		disp_16x16(4,1,8);
		disp_16x16(7,1,11);
		StringPrint(9,1,":");
		disp_16x16(1,2,5);
		disp_16x16(2,2,6);
		disp_16x16(3,2,7);
		disp_16x16(4,2,8);
		disp_16x16(8,2,11);
		StringPrint(9,2,":");
		StringPrint(1,3,"T1:");
		disp_16x16(5,3,11);
		StringPrint(1,4,"T2:");
		disp_16x16(5,4,11);
		StringPrint(1,5,"T3:");
		disp_16x16(5,5,11);
		StringPrint(1,6,"T4:");
		disp_16x16(5,6,11);
		disp_16x16(1,7,12);
		disp_16x16(2,7,10);
		disp_16x16(3,7,14);
		StringPrint(7,7,":    s");
	
}

void init_18b20(void)
{	
		
		while(DS18B20_Init_1()){	};
		
		while(DS18B20_Init_2()){	};
		while(DS18B20_Init_3()){	};
		while(DS18B20_Init_4()){	};
}

void start_pt100(void)
{
	 //读adc电压
	
		HAL_ADC_Start(&hadc1);

		HAL_ADC_PollForConversion(&hadc1,50);

		if(HAL_IS_BIT_SET(HAL_ADC_GetState(&hadc1),HAL_ADC_STATE_REG_EOC))
		adc_value=HAL_ADC_GetValue(&hadc1);

		voltage=Vcc/4096*adc_value;
		sprintf(vol,"%.2f",voltage);
	
		//StringPrint(20,4,vol);
		//用adc电压计算pt100电阻
		Resistor_pt100=(200*(voltage/K+Vcc/3))/(Vcc*2/3-voltage/K);
		sprintf(RES_pt100,"%.1f",Resistor_pt100);
	
		//用pt100电阻计算温度
		TEMP_pt100=(Resistor_pt100/100-1)/0.00385;
		sprintf(TP_pt100,"%.1f",TEMP_pt100);
		StringPrint(20,6,"      ");
	//	StringPrint(20,6,TP_pt100);//调零用
//		sprintf(dC,"%d",dutyCycle);
//		StringPrint(20,7,"     ");
//		StringPrint(20,7,dC);//加热PWM
		arr[n]=TEMP_pt100;
		n++;
		if(n==Num) n=0;
		Sum_TEMP=0;
		for(int i=0;i<Num;i++) Sum_TEMP+=arr[i];
   	Average_TEMP=Sum_TEMP/Num;
		if (Average_TEMP>=Heater_set-qianwei &&Average_TEMP<=Heater_set+qianwei)
		{
			flag_temp=1;
		}
//		sprintf(f,"%.0f",flag_temp);
//		StringPrint(20,5,f);
		if(flag_temp==1)
		{
			if(Average_TEMP<=Heater_set-qianwei) Average_TEMP=Heater_set-qianwei;
			if(Average_TEMP>=Heater_set+qianwei) Average_TEMP=Heater_set+qianwei;
		}
		sprintf(Aver_TEMP,"%.1f",Average_TEMP);
		//StringPrint(12,5,TP_pt100);
		//控制加热端温度
//			dutyCycle=0;//停止加热
//			__HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_3, dutyCycle);
//			StringPrint(20,4,"          ");
			
		if(TEMP_pt100<Heater_set-5)
		{
			dutyCycle=1000;//全速加热
			__HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_3, dutyCycle);
			
		}
		if(TEMP_pt100>=Heater_set-5&&TEMP_pt100<Heater_set)
		{
			
			Error=Heater_set-TEMP_pt100;//温度误差
			Pout=Kp*Error;//放大倍数控温
			Dout=Kd*(Error-LastError);//微分控温
			Sum_Error+=Error;
			Ki=T/Ti*Kp;
			Iout=Ki*Sum_Error;//积分控温
			
			sprintf(iout,"%.1f",Iout);
		
			dutyCycle=Pout+Dout;//pd控温
			if(dutyCycle<0) dutyCycle=0;
		//	dutyCycle=Pout+Iout;//pi控温
			__HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_3, dutyCycle);
		  LastError=Error;
		}
			
		if(TEMP_pt100>=Heater_set&&TEMP_pt100<Heater_set+2)
		{
			Error=Heater_set-TEMP_pt100;//温度误差
			Sum_Error+=Error;
			dutyCycle=0;//停止加热
			__HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_3, dutyCycle);

		}
		if(TEMP_pt100>=Heater_set+2)
		{	
			dutyCycle=0;//停止加热
			__HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_3, dutyCycle);
			//StringPrint(20,4,"          ");
		}
		//
//		dutyCycle=0;//停止加热
//			__HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_3, dutyCycle);
}

void start_timer(void)
{
		//定时器
		sprintf(tim,"%.0f",timer);
		StringPrint(8,7,tim);
}
	

void start_18b20(void)
{
		//读18B20-空气温度
//		TEMP=DS18B20_Get_Temperature();
//		if(TEMP<0)
//		{
//			sprintf(TP,"-%.1f",TEMP/10);
//			StringPrint(8,3,TP);
//		}
//		else
//		{
//			sprintf(TP,"%.1f",TEMP/10);
//			StringPrint(8,3,TP);
//		}
		//读18B20-TP1
		TEMP1=DS18B20_Get_Temperature_1();
		if(TEMP1<0)
		{
			sprintf(TP1,"-%.1f",TEMP1/10);
			StringPrint(4,3,TP1);
		}
		else
		{
			sprintf(TP1,"%.1f",TEMP1/10);
			StringPrint(4,3,TP1);
		}
//		//读18B20-TP2
		TEMP2=DS18B20_Get_Temperature_2();
		if(TEMP2<0)
		{
			sprintf(TP2,"-%.1f",TEMP2/10);
			StringPrint(4,4,TP2);
		}
		else
		{
			sprintf(TP2,"%.1f",TEMP2/10);
			StringPrint(4,4,TP2);
		}
//			//读18B20-TP3
		TEMP3=DS18B20_Get_Temperature_3();
		if(TEMP3<0)
		{
			sprintf(TP3,"-%.1f",TEMP3/10);
			StringPrint(4,5,TP3);
		}
		else
		{
			sprintf(TP3,"%.1f",TEMP3/10);
			StringPrint(4,5,TP3);
		}
			//读18B20-TP4
		TEMP4=DS18B20_Get_Temperature_4();
		if(TEMP4<0)
		{
			sprintf(TP4,"-%.1f",TEMP4/10);
			StringPrint(4,6,TP4);
		}
		else
		{
			sprintf(TP4,"%.1f",TEMP4/10);
			StringPrint(4,6,TP4);
		}
}

void disp(void)
{	 
	 
//	StringPrint(20,5,"      ");
//	StringPrint(20,5,RES_pt100);
	StringPrint(10,2,"     ");
	StringPrint(10,2,Aver_TEMP);
	
	start_timer();
	start_18b20();
}

void key_scan(void)
{
			//按键识别
		if(HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_8)==GPIO_PIN_RESET)
		{
			while(HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_8)==GPIO_PIN_RESET){};
			if(timer>9999) System_Reset();//复位
			HAL_TIM_Base_Stop_IT(&htim1);
			StringPrint(8,7,"    ");
			flag=0;
			timer=0;
		}
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_13)==GPIO_PIN_RESET)
		{
			while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_13)==GPIO_PIN_RESET)
			{	
				if(Heater_set<120)
				{
					Heater_set+=1;//上调1度
					sprintf(Ht_set,"%.0f",Heater_set);
					StringPrint(10,1,"   ");
					StringPrint(10,1,Ht_set);
					HAL_Delay(100);
				}
					flag_temp=0;
			}
		
			
		}
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_14)==GPIO_PIN_RESET)
		{
			while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_14)==GPIO_PIN_RESET)
			{
				if(Heater_set>0)
				{
					Heater_set-=1;//下调1度
					sprintf(Ht_set,"%.0f",Heater_set);
					StringPrint(10,1,"   ");
					StringPrint(10,1,Ht_set);	
					HAL_Delay(100);
				}	
				flag_temp=0;
			}
			
		}
		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_15)==GPIO_PIN_RESET)
		{	
			while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_15)==GPIO_PIN_RESET){};
			if(flag==0) 
			{
				HAL_TIM_Base_Start_IT(&htim1);
				flag=1;
			}
			else 
			{
				HAL_TIM_Base_Stop_IT(&htim1);
				flag=0;
			}
		}
			
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim){
	if(htim->Instance==htim1.Instance){
		timer+=0.1;
	}
	if(htim->Instance==htim2.Instance){
		
		timer2=1;
	}
}


