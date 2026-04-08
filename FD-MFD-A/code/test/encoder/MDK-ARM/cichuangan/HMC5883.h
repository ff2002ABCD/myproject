#ifndef __HMC5883_H
#define __HMC5883_H

#include "main.h"
#include  <math.h>    //Keil library  
#include  <stdio.h>   //Keil library	
#include "stdint.h"
#define  uchar unsigned char
#define  uint unsigned int	
typedef unsigned char BYTE;
typedef unsigned short WORD;

extern BYTE BUF[8];                         //接收数据缓存区      	
extern uchar ge,shi,bai,qian,wan;           //显示变量

void Init_HMC5883(void);            //初始化5883

void conversion(uint temp_data);

void  Multiple_Read_HMC5883();      //连续的读取内部寄存器数据

#endif
