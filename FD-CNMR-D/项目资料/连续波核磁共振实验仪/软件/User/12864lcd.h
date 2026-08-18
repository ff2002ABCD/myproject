#ifndef _12864lcd_H
#define _12864lcd_H

#include "system.h"

#define LCD_RST PBout(4)
#define LCD_STD PBout(6)
#define LCD_CS PBout(7)
#define LCD_SCLK PBout(5)

void Lcd_Init(void);
void send_command(u8 c_data);	//写命令
void send_data(u8 c_data);		//写数据
void Lcd_Display(u8 wzh,char a[],u8 i);				//显示
void Disp_black(void);														//清除绘图区域
void Lcd_Inverse(u8 line,u8 enable);						//反白，取消反白一行
void Lcd_Inverse_Number(u8 x,u8 y);		//反白一个数字
void Lcd_Inverse_xNumber(u8 x1,u8 x2,u8 y);	//反白多个数字
#endif
