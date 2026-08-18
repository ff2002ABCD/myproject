#ifndef _AD9833_H_
#define _AD9833_H_
 
#include "main.h"
 
//#define AD9833_FSYNC 	PCout(2)
//#define AD9833_SCLK 	PCout(1)
//#define AD9833_SDATA 	PCout(0)
 
#define AD9833_PORT_0 		GPIOD
#define AD9833_FSYNC_GPIO 	GPIO_PIN_11
#define AD9833_SCLK_GPIO 	GPIO_PIN_12
#define AD9833_SDATA_GPIO 	GPIO_PIN_13
 
 
/******************************************************************************/
/* AD9833                                                                    */
/******************************************************************************/
/* 寄存器 */
 
#define AD9833_REG_CMD		(0 << 14)
#define AD9833_REG_FREQ0	(1 << 14)
#define AD9833_REG_FREQ1	(2 << 14)
#define AD9833_REG_PHASE0	(6 << 13)
#define AD9833_REG_PHASE1	(7 << 13)
 
/* 命令控制位 */
 
#define AD9833_B28				(1 << 13)
#define AD9833_HLB				(1 << 12)
#define AD9833_FSEL0			(0 << 11)
#define AD9833_FSEL1			(1 << 11)
#define AD9833_PSEL0			(0 << 10)
#define AD9833_PSEL1			(1 << 10)
#define AD9833_PIN_SW			(1 << 9)
#define AD9833_RESET			(1 << 8)
#define AD9833_SLEEP1			(1 << 7)
#define AD9833_SLEEP12		    (1 << 6)
#define AD9833_OPBITEN		    (1 << 5)
#define AD9833_SIGN_PIB		    (1 << 4)
#define AD9833_DIV2				(1 << 3)
#define AD9833_MODE				(1 << 1)
 
#define AD9833_OUT_SINUS		((0 << 5) | (0 << 1) | (0 << 3))//正弦波 
#define AD9833_OUT_TRIANGLE	((0 << 5) | (1 << 1) | (0 << 3))//三角波
#define AD9833_OUT_MSB			((1 << 5) | (0 << 1) | (1 << 3)) //方波
#define AD9833_OUT_MSB2			((1 << 5) | (0 << 1) | (0 << 3))
 
//void AD983_GPIO_Init(void);//初始化IO口
void AD9833_Init(GPIO_TypeDef* PORT, uint16_t FSYNC_GPIO, uint16_t SCLK_GPIO, uint16_t SDATA_GPIO);	//初始化IO口及寄存器
 
void AD9833_Reset(GPIO_TypeDef* PORT, uint16_t FSYNC_GPIO, uint16_t SCLK_GPIO, uint16_t SDATA_GPIO);	//置位AD9833的复位位
void AD9833_ClearReset(GPIO_TypeDef* PORT, uint16_t FSYNC_GPIO, uint16_t SCLK_GPIO, uint16_t SDATA_GPIO);	//清除AD9833的复位位
 
void AD9833_SetRegisterValue(unsigned short regValue, GPIO_TypeDef* PORT, uint16_t FSYNC_GPIO, uint16_t SCLK_GPIO, uint16_t SDATA_GPIO);	//将值写入寄存器
void AD9833_SetFrequency(unsigned short reg, float fout,unsigned short type, GPIO_TypeDef* PORT, uint16_t FSYNC_GPIO, uint16_t SCLK_GPIO, uint16_t SDATA_GPIO);	//写入频率寄存器
void AD9833_SetPhase(unsigned short reg, unsigned short val, GPIO_TypeDef* PORT, uint16_t FSYNC_GPIO, uint16_t SCLK_GPIO, uint16_t SDATA_GPIO);	//写入相位寄存器
 
void AD9833_Setup(unsigned short freq, unsigned short phase,unsigned short type, GPIO_TypeDef* PORT, uint16_t FSYNC_GPIO, uint16_t SCLK_GPIO, uint16_t SDATA_GPIO);	//选择频率、相位和波形类型
void AD9833_SetFrequencyQuick(float fout,unsigned short type, GPIO_TypeDef* PORT, uint16_t FSYNC_GPIO, uint16_t SCLK_GPIO, uint16_t SDATA_GPIO);	//设置频率及波形类型
 
#endif 