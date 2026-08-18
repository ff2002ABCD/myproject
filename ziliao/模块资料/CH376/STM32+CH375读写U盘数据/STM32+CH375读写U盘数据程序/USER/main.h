#include "string.h"				//字符数组
#include "sys.h"				//库函数
#include "delay.h"				//延时
#include "usart.h"				//串口驱动
#include "led.h"				//LED灯驱动
#include "key.h"				//按键驱动
#include "lcd.h"				//LCD显示屏
#include "ch375.h"				//ch375驱动
#include "znfat.h"				//znfat
#include "tpad.h"				//触摸板驱动
#include "adc.h"				//ADC驱动
#include "lsens.h"				//光敏传感器驱动

struct znFAT_Init_Args Init_Args;//初始化TF卡参数集合
struct FileInfo fileinfo; 		//文件信息集合 
u8 key;							//按键键值
u32 i=0;						//循环变量
u8 status;						//函数运行结果量
u8 str[30];						//字符串缓存区
int main(void);					//主函数
void Main_Disp(void);			//主菜单显示界面函数
void SYS_Init(void);			//系统初始化总函数
void Udish_Init(void);			//U盘初始化及属性参数读取函数
void Udish_Read(void);			//U盘读操作实例函数
void Udish_Write(void);			//U盘写操作实例函数

