#include "gui.h"
#include "stdint.h"		// uint16_t 定义
#include "lcd.h"

/*
	author：Haozi
	
	Author URI：https://blog.csdn.net/weixin_46253745
	
	Describe：对 LCD 的驱动文件进行了包装，方便绘制GUI
*/


/* ===================================================== */
// 描述：画线函数
// 参数：
//		起始和结束的x y坐标。
//		color：线的颜色
// 返回值：
/* ===================================================== */
void drawLineWithColor(uint16_t startX, uint16_t startY, uint16_t endX, uint16_t endY, uint16_t color)
{
	POINT_COLOR = color;
	LCD_DrawLine(startX, startY, endX, endY);
}


/* ===================================================== */
// 描述：显示字符串函数
// 参数：
//		startX、startY：起始的x y坐标。
//		width：			区域宽度。
//		p：				字符串地址。
//		color：			线的颜色
// 返回值：
/* ===================================================== */
void drawStringWithColor(uint16_t startX, uint16_t startY, uint16_t width, uint8_t *p, uint16_t color)
{
    POINT_COLOR = color;
	// 字符区域大小 和 字体大小 直接定死了
    LCD_ShowString(startX, startY, width, 16, 16, p);
}

/* ===================================================== */
// 描述：设置LCD背景。设置显示方向为横向；背景颜色为黑色。
// 参数：
// 返回值：
/* ===================================================== */
void setBackGroundColor(void)
{
	LCD_Display_Dir(1);		// 设置LCD显示方向为横向
	
	LCD_Clear(BLACK);		// 清空LCD，用黑色覆盖
	BACK_COLOR = BLACK;		// 背景颜色
	POINT_COLOR = YELLOW;	// 线的颜色
}

/* ===================================================== */
// 描述：显示字符串函数
// 参数：
//		startX、startY：起始的x y坐标。
//		width：			区域宽度。
//		p：				字符串地址。
//		color：			线的颜色
// 返回值：
/* ===================================================== */
void drawNetwork(void)
{
    uint16_t y = 0;
    uint16_t x = 0;
	
    for(x = 20; x < lcddev.width; x += 20)
    {
        for(y = 20; y < (lcddev.height - 20); y += 5)
        {
            LCD_Fast_DrawPoint(x, y, 0XAAAA);
        }
    }

    for(y = 20; y < (lcddev.height - 20); y += 20)
    {
        for(x = 0 ; x < lcddev.width ; x += 5)
        {
            LCD_Fast_DrawPoint(x, y, 0xAAAA);
        }
    }

	POINT_COLOR = 0X534c;
    drawLineWithColor(0, lcddev.height / 2, lcddev.width, lcddev.height / 2, POINT_COLOR);
    drawLineWithColor(lcddev.width / 2, 20, lcddev.width / 2, (lcddev.height - 20), POINT_COLOR);
    LCD_DrawRectangle(0, 20, lcddev.width, (lcddev.height - 20)); // 矩形
}

/* ===================================================== */
// 描述：设置背景上静态的文字.中间的0.00会后期局部刷新。
// 参数：
// 返回值：
/* ===================================================== */
void setBackGroundText(void)
{
	drawStringWithColor(248, 222, 72, "       Hz", YELLOW);
	
	drawStringWithColor(0, 222, 240, "max:0.00V min:0.00V diff:0.00V", YELLOW);
}
