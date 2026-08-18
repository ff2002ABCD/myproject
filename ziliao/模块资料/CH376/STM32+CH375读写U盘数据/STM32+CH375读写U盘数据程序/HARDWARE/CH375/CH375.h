/*******************************************************************************
* File        : CH375.h
* Author      : 
* Date        : 
* Description : CH375 底层驱动函数头文件
* Version     : V1.0

硬件连接：STM32F103         CH375
   	        PF0-PF7  <--->  D0-D7 数据端口
	            PB1  <----  INT#  在复位完成后为中断请求输出，低电平有效
                PA4  ---->  A0    命令/数据选择
	            PA5  ---->  CS#   片选信号
				PA6  ---->  RD#   读选通
		        PA7  ---->  WR#   写选通
*******************************************************************************/
#ifndef  _CH375_H_
#define  _CH375_H_

/* Includes ---------------------------------------------------------------*/

#include"CH375INC.h"  
#include"stm32f10x.h" 
#include "sys.h"
#include "usart.h"

/*端口引脚定义-------------------------------------------------------------*/

/* CH375 的数据端口*/
#define GPIO_CH375_Data  GPIOF
#define RCC_APB2Periph_GPIO_CH375_Data    RCC_APB2Periph_GPIOF

/* CH375 的数据引脚（双向）模式命令定义  PF0-PF7 */
#define DATA_MODE_IN   GPIOF->CRL = 0x44444444 //GPIOF端口定义为输入:IN_FLOATING 
#define DATA_MODE_OUT  GPIOF->CRL = 0x33333333 //GPIOF端口定义为输出:Out_PP,50Hz 


/* CH375 的控制端口*/ 
#define GPIO_CH375_CTL   GPIOA
#define RCC_APB2Periph_GPIO_CH375_CTL     RCC_APB2Periph_GPIOA

/* CH375 的中断端口*/ 
#define GPIO_CH375_INT   GPIOB
#define RCC_APB2Periph_GPIO_CH375_INT     RCC_APB2Periph_GPIOB

/* 命令/数据模式选择 A0: 1-写命令； 0-写数据*/
#define A0_H  GPIO_SetBits(GPIOA,GPIO_Pin_4)
#define A0_L  GPIO_ResetBits(GPIOA,GPIO_Pin_4)

/* 片选 CS#  低电平有效*/ 
#define CS_H  GPIO_SetBits(GPIOA,GPIO_Pin_5)
#define CS_L  GPIO_ResetBits(GPIOA,GPIO_Pin_5)

/* 写选通 WR# 低电平有效*/
#define WR_H  GPIO_SetBits(GPIOA,GPIO_Pin_7)
#define WR_L  GPIO_ResetBits(GPIOA,GPIO_Pin_7)

/* 读选通 RD# 低电平有效*/
#define RD_H  GPIO_SetBits(GPIOA,GPIO_Pin_6)
#define RD_L  GPIO_ResetBits(GPIOA,GPIO_Pin_6)



/* Function Prototype ---------------------------------------------------*/

void CH375_DelayNus(__IO uint32_t nCount);  // CH375操作时需要的延时函数（根据不同的CPU需要调整） 

void CH375_Configuration(void);        // CH375 对应时钟，引脚的配置
 
void CH375_WriteCmd(uint8_t cmd);      // 向CH375写入命令
void CH375_WriteDat(uint8_t dat);      // 向CH375写入数据
uint8_t CH375_ReadCmd(void);           // 从CH375读取命令
uint8_t CH375_ReadDat(void);           // 从CH375读取数据或状态
 
uint8_t CH375_WaitInterrupt(void);     // 主机等待CH375芯片内部操作完成并产生中断，返回操作状态
 
uint8_t CH375_Init(void);              // 初始化CH375芯片
uint8_t CH375_DiskConnect(void);       // 磁盘是否连接
uint8_t CH375_DiskInit(void);          // 初始化磁盘
uint8_t CH375_DiskReady(void);         // 磁盘是否准备好（是够已经被初始化并得到分配地址）

uint8_t CH375_WriteSector(uint32_t addr, const uint8_t *pbuff); // 向U盘一扇区写入数据
uint8_t CH375_ReadSector(uint32_t addr, uint8_t *pbuff); // 从U盘一扇区读出数据

#endif   /*  _CH375_H_  */
 

