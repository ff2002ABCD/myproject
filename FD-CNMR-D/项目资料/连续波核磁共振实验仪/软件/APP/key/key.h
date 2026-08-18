#ifndef _key_H
#define _key_H


#include "system.h"
 
#define KEY_UP_Pin    	GPIO_Pin_12   	//向上
#define KEY_DOWN_Pin    GPIO_Pin_13    	//向下
//#define KEY_LEFT_Pin   	GPIO_Pin_14   	//向左
//#define KEY_RIGHT_Pin   GPIO_Pin_15    	//向右
#define KEY_QD_Pin   		GPIO_Pin_14   	//确定
#define KEY_FH_Pin   	 	GPIO_Pin_15    	//返回
//#define KEY_UP_Pin      GPIO_Pin_0  //定义KEY_UP管脚

//#define KEY_Port (GPIOB) //定义端口
//#define KEY_UP_Port (GPIOA) //定义端口


//使用位操作定义
#define K_UP 		PBin(12)
#define K_DOWN 	PBin(13)
//#define K_LEFT 	PBin(14)
//#define K_RIGHT PBin(15)
#define K_QD 		PBin(14)
#define K_FH 		PBin(15)
//#define K_RESET PAin(8)

//使用读取管脚状态库函数定义 
//#define K_UP      GPIO_ReadInputDataBit(KEY_UP_Port,KEY_UP_Pin)
//#define K_DOWN    GPIO_ReadInputDataBit(KEY_Port,KEY_DOWN_Pin)
//#define K_LEFT    GPIO_ReadInputDataBit(KEY_Port,KEY_LEFT_Pin)
//#define K_RIGHT   GPIO_ReadInputDataBit(KEY_Port,KEY_RIGHT_Pin)


//定义各个按键值  
#define KEY_UP 		1
#define KEY_DOWN 	2
#define KEY_LEFT 	3
#define KEY_RIGHT 4
#define KEY_QD 		5
#define KEY_FH 		6  
//#define KEY_RESET 5 


void KEY_Init(void);
u8 KEY_Scan(void);
void ReadKeyPort(void);
#endif
