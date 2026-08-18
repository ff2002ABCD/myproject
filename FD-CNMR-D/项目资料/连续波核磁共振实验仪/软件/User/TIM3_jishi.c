#include "main.h"

//TIM3初始化
void TIM3_Init(u16 per,u16 psc)
{
	TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure;
	NVIC_InitTypeDef NVIC_InitStructure;
	
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3,ENABLE);//使能TIM3
	
	//初始化定时器
	TIM_TimeBaseInitStructure.TIM_Period=per;   //自动装载值
	TIM_TimeBaseInitStructure.TIM_Prescaler=psc; //分频系数
	TIM_TimeBaseInitStructure.TIM_ClockDivision=TIM_CKD_DIV1;
	TIM_TimeBaseInitStructure.TIM_CounterMode=TIM_CounterMode_Up; //设置向上计数模式
	TIM_TimeBaseInit(TIM3,&TIM_TimeBaseInitStructure);
	
	//允许更新中断，触发方式中断
	TIM_ITConfig(TIM3,TIM_IT_Update,ENABLE); //开启定时器中断
	TIM_ClearITPendingBit(TIM3,TIM_IT_Update);
	
	//中断优先级管理
	NVIC_InitStructure.NVIC_IRQChannel = TIM3_IRQn;//定时器中断通道
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority=0x00;//抢占优先级
	NVIC_InitStructure.NVIC_IRQChannelSubPriority =0x02;		//子优先级
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;			//IRQ通道使能
	NVIC_Init(&NVIC_InitStructure);	
	
	TIM_Cmd(TIM3,ENABLE);
}

void TIM3_IRQHandler(void)
{
	if(TIM_GetITStatus(TIM3,TIM_IT_Update))
	{
		time_100m_flag = 1;
		TIM_ClearITPendingBit(TIM3,TIM_IT_Update);
	}
}















