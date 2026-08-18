#ifndef __GUI_H
#define __GUI_H

/*
	author：Haozi
	
	Author URI：https://blog.csdn.net/weixin_46253745
	
	Describe：对 LCD 的驱动文件进行了包装，方便绘制GUI
*/

#include "stdint.h"		// uint16_t 定义

void drawLineWithColor(uint16_t startX, uint16_t startY, uint16_t endX, uint16_t endY, uint16_t color);
void drawStringWithColor(uint16_t startX, uint16_t startY, uint16_t width, uint8_t *p, uint16_t color);
void setBackGroundColor(void);
void drawNetwork(void);
void setBackGroundText(void);


#endif
