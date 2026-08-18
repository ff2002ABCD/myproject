#include "Frequency.h"

/*******************************************************************************
* 函 数 名         : CMOS_Change_Init
* 函数功能		   : 控制CMOS模拟开关
* 输    入         : 无
* 输    出         : 无
*******************************************************************************/
void Frequency_Init()
{
	GPIO_InitTypeDef GPIO_InitStructure;//定义结构体变量
	TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure;
	NVIC_InitTypeDef NVIC_InitStructure;
	
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2,ENABLE);
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);
	
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_0;  //选择你要设置的IO口
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_IPD;	 //下拉输入
	//GPIO_Mode_IPD GPIO_Mode_IN_FLOATING
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;	  //设置传输速率
	GPIO_Init(GPIOA,&GPIO_InitStructure); 	   /* 初始化GPIO */
	
	//初始化定时器
	TIM_DeInit(TIM2);
	TIM_TimeBaseInitStructure.TIM_Period=0xC350;   //自动装载值50000
	TIM_TimeBaseInitStructure.TIM_Prescaler=0; //分频系数
	TIM_TimeBaseInitStructure.TIM_ClockDivision=TIM_CKD_DIV1;
	TIM_TimeBaseInitStructure.TIM_CounterMode=TIM_CounterMode_Up; //设置向上计数模式
	TIM_TimeBaseInit(TIM2,&TIM_TimeBaseInitStructure);
	
	TIM_ETRClockMode2Config(TIM2, TIM_ExtTRGPSC_OFF, TIM_ExtTRGPolarity_NonInverted, 0);	  //使用外部计数模式2
	TIM_SetCounter(TIM2, 0);	 //计数器清零 
	
	TIM_ITConfig(TIM2,TIM_IT_Update,ENABLE); //开启定时器中断
	TIM_ClearITPendingBit(TIM2,TIM_IT_Update);
	
	NVIC_InitStructure.NVIC_IRQChannel = TIM2_IRQn;//定时器中断通道
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority=0x00;//抢占优先级
	NVIC_InitStructure.NVIC_IRQChannelSubPriority =0x00;		//子优先级
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;			//IRQ通道使能
	NVIC_Init(&NVIC_InitStructure);	
	//TIM_Cmd(TIM2, ENABLE);  //使能TIMx外设 
}

/*******************************************************************************
* 函 数 名         : TIM2_IRQHandler
* 函数功能		   : TIM2中断函数
* 输    入         : 无
* 输    出         : 无
*******************************************************************************/
void TIM2_IRQHandler(void)
{
	if(TIM_GetITStatus(TIM2,TIM_IT_Update))
	{
		time_50000++;
	}
	TIM_ClearITPendingBit(TIM2,TIM_IT_Update);	
}


