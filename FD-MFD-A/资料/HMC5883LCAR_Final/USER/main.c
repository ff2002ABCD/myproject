#include "delay.h"
#include "sys.h"
#include "oled.h"
#include "bmp.h"
#include "key.h"
#include "led.h"
#include "myiic.h"
#include "HMC5883L.h"
#include "usart.h"
#include "math.h"
double x,y,z,h;
int main(void)
{	
	delay_init();
	IIC_Init();
	hmc_init();
	delay_init();	    	 	  
	NVIC_Configuration(); 	 
	OLED_Init();			  
	OLED_Clear(); 
	LED_Init();		  	 
	KEY_Init();          	
	OLED_Clear();
	IIC_Init();
	USART1_Init(9600);
	Show_welcome();
	while(1)
	{
		KEY_Choice();
	}
}
