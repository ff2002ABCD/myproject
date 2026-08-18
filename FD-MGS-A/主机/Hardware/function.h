#ifndef __FUNCTION_H
#define __FUNCTION_H
#include "main.h"
#include "usart.h"  // 添加UART相关头文件
#define MAX_GROUP 16
#define MAX_NUMBER 100
#define AVER_NUM 50//ųСȡƽ

// 曲线显示相关常量
#define CURVE_CONTROL_COUNT 1         // 只使用s0一个曲线控件
#define DISPLAY_UPDATE_INTERVAL 200   // 显示更新间隔(ms)

typedef struct
{
		float Pos,Current,Strength,GaX,GaY,GaZ;
}TABLE;


void system_init(void);
void Current_control(void);  // 添加电流控制函数声明

// 新增页面曲线显示函数
void Display_Spectrum_Curve(void);  // 光谱测量页面显示
void Display_Calibration_Curve(void);  // 标定页面显示
void Display_Query_Curve(void);  // 查询导出页面显示

// 页面初始化函数
void query_export_page_init(void);  // 查询导出页面初始化

extern int start_position_int,end_position_int,position_step_int;
extern uint8_t group_now,number_now,sheet_now,table_length[MAX_NUMBER],sheet_length;
extern float GaX,GaY,GaZ,rawGaX,rawGaY,rawGaZ,GaXmax,GaXmin,GaYmax,GaYmin,GaZmax,GaZmin,strength,Current,position,Voltage_dac,k;
extern float GaX_array[AVER_NUM],GaY_array[AVER_NUM],GaZ_array[AVER_NUM],strength_array[AVER_NUM];
extern float pos_measure_start;
extern double test_position[MAX_NUMBER];
extern double start_position,end_position,position_step,position_num;
extern TABLE table[MAX_GROUP][MAX_NUMBER];

// 曲线显示相关变量声明
extern uint32_t last_curve_update; // 最后一次曲线更新时间
extern uint32_t displayUpdateTime; // 显示更新时间
extern uint8_t current_page; // 当前显示页面

#endif
