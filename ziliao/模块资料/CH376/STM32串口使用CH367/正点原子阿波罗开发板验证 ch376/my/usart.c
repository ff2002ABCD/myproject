#include "usart.h"
#include "delay.h"
#include "interface.h"     //底层接口函数
////////////////////////////////////////////////////////////////////////////////// 	 
//如果使用os,则包括下面的头文件即可.
#if SYSTEM_SUPPORT_OS
#include "includes.h"					//os 使用	  
#endif
//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//ALIENTEK STM32F429开发板
//串口1初始化		   
//正点原子@ALIENTEK
//技术论坛:www.openedv.com
//修改日期:2015/9/7
//版本：V1.5
//版权所有，盗版必究。
//Copyright(C) 广州市星翼电子科技有限公司 2009-2019
//All rights reserved
//********************************************************************************
//V1.0修改说明 
////////////////////////////////////////////////////////////////////////////////// 	  
//加入以下代码,支持printf函数,而不需要选择use MicroLIB	  
//#define PUTCHAR_PROTOTYPE int fputc(int ch, FILE *f)	
#if 1
#pragma import(__use_no_semihosting)             
//标准库需要的支持函数                 
struct __FILE 
{ 
	int handle; 
}; 

FILE __stdout;       
//定义_sys_exit()以避免使用半主机模式    
void _sys_exit(int x) 
{ 
	x = x; 
} 
//重定义fputc函数 
int fputc(int ch, FILE *f)
{ 	
	while((USART1->SR&0X40)==0);//循环发送,直到发送完毕   
	USART1->DR = (u8) ch;      
	return ch;
}
#endif 

#if EN_USART1_RX   //如果使能了接收
//串口1中断服务程序
//注意,读取USARTx->SR能避免莫名其妙的错误   	

u8 USART_RX_BUF[USART_REC_LEN] ;//__attribute__ ((at(0X20001000)));//接收缓冲,最大USART_REC_LEN个字节,起始地址为0X20001000.  

//u8 USART_RX_BUF[USART_REC_LEN];     //接收缓冲,最大USART_REC_LEN个字节.
//接收状态
//bit15，	接收完成标志
//bit14，	接收到0x0d
//bit13~0，	接收到的有效字节数目
u16 USART_RX_STA=0;       //接收状态标记	
u32 USART_RX_CNT=0;			//接收的字节数 

u8 aRxBuffer[RXBUFFERSIZE];//HAL库使用的串口接收缓冲
UART_HandleTypeDef UART1_Handler; //UART句柄

//初始化IO 串口1 
//bound:波特率
void uart_init(u32 bound)
{	
	//UART 初始化设置
	UART1_Handler.Instance=USART1;					    //USART1
	UART1_Handler.Init.BaudRate=bound;				    //波特率
	UART1_Handler.Init.WordLength=UART_WORDLENGTH_8B;   //字长为8位数据格式
	UART1_Handler.Init.StopBits=UART_STOPBITS_1;	    //一个停止位
	UART1_Handler.Init.Parity=UART_PARITY_NONE;		    //无奇偶校验位
	UART1_Handler.Init.HwFlowCtl=UART_HWCONTROL_NONE;   //无硬件流控
	UART1_Handler.Init.Mode=UART_MODE_TX_RX;		    //收发模式
	HAL_UART_Init(&UART1_Handler);					    //HAL_UART_Init()会使能UART1
	
	//HAL_UART_Receive_IT(&UART1_Handler, (u8 *)aRxBuffer, RXBUFFERSIZE);//该函数会开启接收中断：标志位UART_IT_RXNE，并且设置接收缓冲以及接收缓冲接收最大数据量(使用回调函数处理中断需要调用该函数）
  
}

//UART底层初始化，时钟使能，引脚配置，中断配置
//此函数会被HAL_UART_Init()调用
//huart:串口句柄

void HAL_UART_MspInit(UART_HandleTypeDef *huart)
{
    //GPIO端口设置
	GPIO_InitTypeDef GPIO_Initure;
	
	if(huart->Instance==USART1)//如果是串口1，进行串口1 MSP初始化
	{
		__HAL_RCC_GPIOA_CLK_ENABLE();			//使能GPIOA时钟
		__HAL_RCC_USART1_CLK_ENABLE();			//使能USART1时钟
	
		GPIO_Initure.Pin=GPIO_PIN_9;			//PA9
		GPIO_Initure.Mode=GPIO_MODE_AF_PP;		//复用推挽输出
		GPIO_Initure.Pull=GPIO_PULLUP;			//上拉
		GPIO_Initure.Speed=GPIO_SPEED_FAST;		//高速
		GPIO_Initure.Alternate=GPIO_AF7_USART1;	//复用为USART1
		HAL_GPIO_Init(GPIOA,&GPIO_Initure);	   	//初始化PA9

		GPIO_Initure.Pin=GPIO_PIN_10;			//PA10
		HAL_GPIO_Init(GPIOA,&GPIO_Initure);	   	//初始化PA10
		__HAL_UART_DISABLE_IT(huart,UART_IT_TC);
#if EN_USART1_RX
		__HAL_UART_ENABLE_IT(huart,UART_IT_RXNE);		//开启接收中断
		HAL_NVIC_EnableIRQ(USART1_IRQn);				//使能USART1中断通道
		HAL_NVIC_SetPriority(USART1_IRQn,3,3);			//抢占优先级3，子优先级3
#endif	
	}

}


 


//串口1中断服务程序
void USART1_IRQHandler(void)                	
{ 
	u8 Res;
#if SYSTEM_SUPPORT_OS	 	//使用OS
	OSIntEnter();    
#endif
	if((__HAL_UART_GET_FLAG(&UART1_Handler,UART_FLAG_RXNE)!=RESET))  //接收中断(接收到的数据必须是0x0d 0x0a结尾)
	{
        HAL_UART_Receive(&UART1_Handler,&Res,1,1000); 
		if(USART_RX_CNT<USART_REC_LEN)
		{
			USART_RX_BUF[USART_RX_CNT]=Res;
			USART_RX_CNT++;			 									     
		}    		 
	}
	HAL_UART_IRQHandler(&UART1_Handler);	
#if SYSTEM_SUPPORT_OS	 	//使用OS
	OSIntExit();  											 
#endif
} 
#endif	

void CH376_PORT_INIT( void )
{
	/*****/
}

//写命令
void xWriteCH376Cmd( unsigned char cmd ) { 				 /* 向CH376的命令端口写入命令,周期不小于2uS,如果单片机较快则延时 */	
	while((USART1->SR&0X40)==0);//循环发送,直到发送完毕
	USART1->DR = 0x57;
	while((USART1->SR&0X40)==0);//循环发送,直到发送完毕   
	USART1->DR = 0xAB;	
	
	USART1->SR = ~(0x20);          //清除RXNE
	
	while((USART1->SR&0X40)==0);//循环发送,直到发送完毕
	USART1->DR = cmd;
	delay_us(2);
	
//	while((USART1->SR&0X40)==0);//循环发送,直到发送完毕   
//	USART1->DR = (u8) ch; 
}

//写数据
void xWriteCH376Data( unsigned char dat ) { 				 /* 向CH376的数据端口写入数据,周期不小于1uS,如果单片机较快则延时 */
	while((USART1->SR&0x40)==0);   
	USART1->DR = dat;
	delay_us(1);
}

//读数据
unsigned char xReadCH376Data(void) {  				     /* 从CH376的数据端口读出数据,周期不小于1uS,如果单片机较快则延时 */
//	unsigned int i;
//	u16 oldcount=0;				    //老的串口接收数据值
//	u32 applenth=0;				    //接收到的app代码长度
//	if(oldcount==USART_RX_CNT)//新周期内,没有收到任何数据,认为本次数据接收完成.
//			{
//				applenth=USART_RX_CNT;
//				oldcount=0;
//				USART_RX_CNT=0;
//				printf("用户程序接收完成!\r\n");
//				printf("代码长度:%dBytes\r\n",applenth);
//				
////				sprintf((char*)t ,"%x",USART_RX_BUF);
////				x =(int)USART_RX_BUF;
////				LCD_ShowString(30,40,200,16,16,x);
//			}else oldcount=USART_RX_CNT;			
//	return ERR_USB_UNKNOWN;
//		return (unsigned char)USART_RX_BUF;
	//return (uint16_t)(USART1->DR & (uint16_t)0x01FF);
//	UINT32 i;
//	for(i=0;i<500000;i++)                      //设置500ms串口接收超时
//	{
//		if(USART2->SR&0x20)    //RXNE
//		{
//			return ((UINT8)USART2->DR);
//		}
//		delay_us(1);
//	}
	return ERR_USB_UNKNOWN;
}

/* 串口方式未用到 */
void xEndCH376Cmd(void)
{
}

/* 查询CH376中断(INT#低电平) */
UINT8	Query376Interrupt( void )
{
#ifdef	CH376_INT_WIRE                  /* 如果连接了CH376的中断引脚则直接查询中断引脚 */
	if(CH376_INT_WIRE) return FALSE ;
	else{
		//xReadCH376Data();               //产生中断的同时，串口会收到一个数据，直接读出来丢掉
		return TRUE ;
	}
#else
	if ( USART1->SR&0x20 ) {             /* 如果未连接CH376的中断引脚则查询串口中断状态码 */
		USART1->SR = ~(0x20);          //清除RXNE	
		return( TRUE );
	}
	else return( FALSE );
#endif	
	
}

/* CH376初始化代码 */
UINT8	mInitCH376Host( void )  /* 初始化CH376 */
{
	UINT8	res[2];	
	delay_ms(500);        /* 上电后至少延时50ms操作 */
	CH376_PORT_INIT( );  /* 接口硬件初始化 */
	xWriteCH376Cmd( CMD11_CHECK_EXIST );  /* 测试单片机与CH376之间的通讯接口 */
	xWriteCH376Data( 0x55 );
	res[0] = USART_RX_BUF[0];
	xEndCH376Cmd( );
	 
	if ( res[0] != 0xAA )
        return( ERR_USB_UNKNOWN );  /* 通讯接口不正常,可能原因有:接口连接异常,其它设备影响(片选不唯一),串口波特率,一直在复位,晶振不工作 */
    //else return( USB_INT_SUCCESS );
	
	xWriteCH376Cmd( CMD11_SET_USB_MODE );  /* 设备USB工作模式 */
	xWriteCH376Data( 0x06 );
	delay_us( 20 );
	res[0] = USART_RX_BUF[0];
	xEndCH376Cmd( );
	if ( res[0] == CMD_RET_SUCCESS || res[1] ==USB_INT_CONNECT) 
		return( USB_INT_SUCCESS );
	else return( ERR_USB_UNKNOWN );  /* 设置模式错误 */		
	
}

/****************************************************************************************/
/****************************************************************************************/
/*************************下面程序通过在回调函数中编写中断控制逻辑*********************/
/****************************************************************************************
***************************************************************************************************

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
	if(huart->Instance==USART1)//如果是串口1
	{
		if((USART_RX_STA&0x8000)==0)//接收未完成
		{
			if(USART_RX_STA&0x4000)//接收到了0x0d
			{
				if(aRxBuffer[0]!=0x0a)USART_RX_STA=0;//接收错误,重新开始
				else USART_RX_STA|=0x8000;	//接收完成了 
			}
			else //还没收到0X0D
			{	
				if(aRxBuffer[0]==0x0d)USART_RX_STA|=0x4000;
				else
				{
					USART_RX_BUF[USART_RX_STA&0X3FFF]=aRxBuffer[0] ;
					USART_RX_STA++;
					if(USART_RX_STA>(USART_REC_LEN-1))USART_RX_STA=0;//接收数据错误,重新开始接收	  
				}		 
			}
		}

	}
}
 
//串口1中断服务程序
void USART1_IRQHandler(void)                	
{ 
#if SYSTEM_SUPPORT_OS	 	//使用OS
	OSIntEnter();    
#endif
	
	HAL_UART_IRQHandler(&UART1_Handler);	//调用HAL库中断处理公用函数
	
    while (HAL_UART_GetState(&UART1_Handler) != HAL_UART_STATE_READY);//等待就绪

	while(HAL_UART_Receive_IT(&UART1_Handler, (u8 *)aRxBuffer, RXBUFFERSIZE) != HAL_OK);//一次处理完成之后，重新开启中断并设置RxXferCount为1
	
#if SYSTEM_SUPPORT_OS	 	//使用OS
	OSIntExit();  											 
#endif
} 
 

**************************************/


