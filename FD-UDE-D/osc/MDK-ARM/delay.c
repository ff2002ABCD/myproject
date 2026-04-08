#include "delay.h"

////????

void delay_us(uint32_t nus)
{
 SysTick->LOAD = 9*nus;
 SysTick->VAL=0X00;
 SysTick->CTRL=0X05;
 while(!(SysTick->CTRL&(1<<16))){};
 SysTick->CTRL&=~(1<<0);
}

//????
void delay_ms(uint16_t nms)
{
	while(nms--!=0){
		delay_us(1000);
	}
}

void delay_s(uint16_t ns)
{
	while(ns--!=0){
		delay_ms(1000);
	}
}

