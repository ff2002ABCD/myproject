#ifndef _ADS1220_H
#define _ADS1220_H

#include "system.h"

#define ADS1220_CS PAout(2)
#define ADS1220_SCLK PAout(3)
#define ADS1220_DOUT PAin(4)
#define ADS1220_DIN PAout(5)


//***********************命令******************************************************************************/
#define ADS1220_RESET			0x06		//复位器件
#define ADS1220_START    	0x08    //启动或重启转换
#define ADS1220_POWERDOWN	0x02    //进入掉电模式
#define ADS1220_RDATA    	0x10    //通过命令读取数据
#define ADS1220_RREG  		0x20  	//读取寄存器
#define ADS1220_WREG 			0x40 		//写入寄存器

/************************配置初始值*******************************************************************/
//寄存器0
#define MUX_A0			MUX_8			//AINP = AIN0，AINN = AVSS	2.5V确定基准
#define MUX_A1     	MUX_11   	//AINP = AIN3，AINN = AVSS	励磁电压
#define MUX_A2     	MUX_10   	//AINP = AIN2，AINN = AVSS	射频幅度
#define MUX_A3     	MUX_6    	//AINP = AIN1，AINN = AIN0	毫特计
#define MUX_A4     	MUX_14    //AINP 和 AINN 短接至 (AVDD + AVSS) / 2
#define MUX_A5     	MUX_13  		//(AVDD – AVSS) / 4 监视（旁路 PGA）
#define PGA_A0			PGA_0			//增益 = 1
#define PGA_BYPASS	PGA_BYPASS_Disable//已禁用和旁路
//#define PGA_BYPASS_1	PGA_BYPASS_Enable//PGA 已启用

//寄存器1
#define DR         	DR_175SPS //正常模式:175SPS;高性能模式:350SPS
#define MODE				MODE_2 		//高性能模式（512kHz 调制器时钟）输入引入的噪声低
#define ConverMode	ConverMode_0//单次转换模式（默认设置）

//寄存器2
#define VREF				VREF_3 		//用模拟电源作为基准电压 (AVDD – AVSS)
#define FIR					FIR_Mode0 //无 50Hz 或 60Hz 抑制（默认设置）

//寄存器3
#define DRDY_Mode		DRDY_Mode1//同时通过 DOUT/DRDY 和 DRDY 指示数据就绪。


//***********************起始寄存器地址**********************************************************************/
#define Register_0	0x00		//输入多路复用器配置=4;增益配置=3;禁用和旁路内部低噪声PGA=1
#define Register_1	0x04		//数据速率=3;工作模式=2;转换模式=1;温度传感器模式=1;烧毁电流源=1
#define Register_2	0x08		//基准电压选择=2;FIR 滤波器配置=2;低侧电源开关配置=1;IDAC 电流设置=3
#define Register_3	0x0C		//IDAC1 路由配置=3;IDAC2 路由配置=3;DRDY 模式=1;保留=1

//寄存器0
/*-----------输入多路复用器配置 -------------------------
**这些位配置输入多路复用器。 
**对于 AINN = AVSS 的设置，PGA 必须禁用 (PGA_BYPASS = 1)，
**并且仅可使用 增益 1、2 和 4。
-------------------------------------------------------*/
#define MUX_0  0X00//0000：AINP = AIN0，AINN = AIN1（默认设置）
#define MUX_1  0X10//0001：AINP = AIN0，AINN = AIN2
#define MUX_2  0X20//0010：AINP = AIN0，AINN = AIN3
#define MUX_3  0X30//0011：AINP = AIN1，AINN = AIN2
#define MUX_4  0X40//0100：AINP = AIN1，AINN = AIN3
#define MUX_5  0X50//0101：AINP = AIN2，AINN = AIN3
#define MUX_6  0X60//0110：AINP = AIN1，AINN = AIN0
#define MUX_7  0X70//0111：AINP = AIN3，AINN = AIN2
#define MUX_8  0X80//1000：AINP = AIN0，AINN = AVSS
#define MUX_9  0X90//1001：AINP = AIN1，AINN = AVSS
#define MUX_10 0XA0//1010：AINP = AIN2，AINN = AVSS
#define MUX_11 0XB0//1011：AINP = AIN3，AINN = AVSS
#define MUX_12 0XC0//1100：(V(REFPx) – V(REFNx)) / 4 监视（旁路 PGA）
#define MUX_13 0XD0//1101：(AVDD – AVSS) / 4 监视（旁路 PGA）
#define MUX_14 0XE0//1110：AINP 和 AINN 短接至 (AVDD + AVSS) / 2
//1111：保留

/*------------增益配置---------------------------------- 
**这些位用于配置器件增益。 在不使用 PGA 的情况下，
**可使用增益 1、2 和 4。在这种情况下，通过开关电容结 构获得增益。
------------------------------------------------------*/
#define PGA_0  	0X00//000：增益 = 1（默认设置
#define PGA_1  	0X02//001：增益 = 2
#define PGA_4 	0X04//010：增益 = 4
#define PGA_8  	0X06//011：增益 = 8
#define PGA_16 	0X08//100：增益 = 16
#define PGA_32 	0X0A//101：增益 = 32
#define PGA_64 	0X0C//110：增益 = 64
#define PGA_128 0X0E//111：增益 = 128

/*-----------------禁用和旁路内部低噪声 PGA----------------------
**禁用 PGA 会降低整体功耗，并可将共模电压范围 (VCM) 扩展为 AVSS – 0.1V 至AVDD + 0.1V。 
**只能针对增益 1、2 和 4 禁用 PGA。 
无论 PGA_BYPASS 设置如何，都始终针对增益设置 8 至 128 启用 PGA。 
**0：PGA 已启用（默认设置） 
**1：PGA 已禁用和旁路
---------------------------------------------------------------------*/
#define PGA_BYPASS_Enable  0x00//PGA 已启用（默认设置） 
#define PGA_BYPASS_Disable 0x01//已禁用和旁路
 
//寄存器1
/*----------------------数据速率----------------------------------
**这些位控制数据速率设置，取决于所选工作模式。
**表 18 列出了正常模式、占空比 模式和 Turbo 模式对应的位设置。
-----------------------------------------------------------------*/
#define DR_20SPS   0X00
#define DR_45SPS   0X20
#define DR_90SPS   0X40
#define DR_175SPS  0X60
#define DR_330SPS  0X80
#define DR_600SPS  0XA0
#define DR_1000SPS 0XC0
 
/*-----------------工作模式 ---------------------------------------
**这些位控制器件所处的工作模式。
00：正常模式（256kHz 调制器时钟，默认设置）
01：占空比模式（内部占空比 1:4）
10：高性能模式（512kHz 调制器时钟）输入引入的噪声低
11：保留
------------------------------------------------------------------*/
#define MODE_0 0x00	//正常模式（256kHz 调制器时钟，默认设置）
#define MODE_1 0x08	//占空比模式（内部占空比 1:4）
#define MODE_2 0x10	//高性能模式（512kHz 调制器时钟）输入引入的噪声低

/*------------------转换模式----------------------------------------
此位用于为器件设置转换模式。 
0：单次模式（默认设置）
1：连续转换模式
-------------------------------------------------------------------*/
#define ConverMode_0 0x00//单次模式（默认设置）
#define ConverMode_1 0x04//连续转换模式

//寄存器2 
/*--------------------基准电压选择---------------------------------
这些位用于选择转换所使用的基准电压源。
00：选择 2.048V 内部基准电压（默认设置）
01：使用专用 REFP0 和 REFN0 输入选择的外部基准电压
10：使用 AIN0/REFP1 和 AIN3/REFN1 输入选择的外部基准电压
11：用作基准的模拟电源 (AVDD – AVSS)
--------------------------------------------------------------------*/
#define VREF_0 0X00//选择 2.048V 内部基准电压（默认设置）
#define VREF_1 0X40//使用专用 REFP0 和 REFN0 输入选择的外部基准电压
#define VREF_2 0X80//使用 AIN0/REFP1 和 AIN3/REFN1 输入选择的外部基准电压
#define VREF_3 0XC0//用作基准的模拟电源 (AVDD – AVSS)
 
/*----------------------FIR 滤波器配置------------------------------
这些位用于为内部 FIR 滤波器配置滤波器系数。 
在正常模式下，这些位仅与 20SPS 设置结合使用；
在占空比模式下，这些位仅与
5SPS 设置结合使用。对于所有其他数据速率，这些位均设置为 00。
00：无 50Hz 或 60Hz 抑制（默认设置）
01：同时抑制 50Hz 和 60Hz
10：只抑制 50Hz
11：只抑制 60Hz
------------------------------------------------------------------*/
#define FIR_Mode0  0x00//无 50Hz 或 60Hz 抑制（默认设置）
#define FIR_Mode1  0x10//同时抑制 50Hz 和 60Hz
#define FIR_Mode2  0x20//只抑制 50Hz
#define FIR_Mode3  0x30//只抑制 60Hz

//寄存器3
/*-----------------------DRDY 模式 -----------------------------
该位用于控制新数据就绪时 DOUT/DRDY 引脚的行为。 
---------------------------------------------------------------*/
#define DRDY_Mode0 0x00  //0：仅专用 DRDY 引脚用于指示数据何时就绪（默认设置）
#define DRDY_Mode1 0x02  //1：同时通过 DOUT/DRDY 和 DRDY 指示数据就绪。


//u8 AT24CXX_ReadOneByte(u16 ReadAddr);							//指定地址读取一个字节
//void AT24CXX_WriteOneByte(u16 WriteAddr,u8 DataToWrite);		//指定地址写入一个字节
//void AT24CXX_WriteLenByte(u16 WriteAddr,u32 DataToWrite,u8 Len);//指定地址开始写入指定长度的数据
//u32 AT24CXX_ReadLenByte(u16 ReadAddr,u8 Len);					//指定地址开始读取指定长度数据
//void AT24CXX_Write(u16 WriteAddr,u8 *pBuffer,u16 NumToWrite);	//从指定地址开始写入指定长度的数据
//void AT24CXX_Read(u16 ReadAddr,u8 *pBuffer,u16 NumToRead);   	//从指定地址开始读出指定长度的数据


void ADS1220_Init(void); 	//初始化ADS1220
int ADS1220_Config(u8 ain);//设置采集端口
int ADS1220_Single_shot(void);//单次采集
void ADS1220_WriteRegister(u8 StartAddress, u8 NumRegs, u8 * pData);	//写寄存器
int ADS1220_ReadRegister(void);	//读寄存器



#endif
