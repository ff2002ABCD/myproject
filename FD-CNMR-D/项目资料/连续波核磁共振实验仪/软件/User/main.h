#include "system.h"
#include "SysTick.h"
#include "led.h"
#include "key.h"
//#include "huoer.h"
#include "time.h"
#include "TIM3_jishi.h"
////#include "TIM1_jishi.h"
//#include "automatic.h"
//#include "ltc1655.h"

//#include "encoder.h"
//lcd
#include "Frequency.h"
//#include "iic.h"
#include "ADS1220.h"
#include "usart.h"
//#include "DM542S.h"
#include "filter.h"

#include "12864lcd.h"
//#include "ad9833.h"
#include "stdlib.h"
#include "math.h"

#ifndef MAIN_H
#define MAIN_H

//----- 按键
typedef struct KEY_DATA
{
	u8 key_number_t1;		//按下的键暂存1
	u8 key_number_t2;		//按下的键暂存2
	int key_time;		//键按下的时间
	u8 key_long;			//1长按
	u8 key;					//1按下
	u8 key_number;		//按下的键
	int key_cishu;		//长按的次数
} KEY_DATA;

extern KEY_DATA key_data;

//extern int key_time;		//键按下的时间
//extern u8 key_long;			//1长按
//extern u8 key;					//0按下
//extern u8 key_number;		//按下的键
//extern int key_cishu;		//长按的次数

extern u8 mod;					//1显示四个值

//int choose[6] = {0,0,0,0,0,0};			//选择项，0手动自动，1主界面，2参数设置，3数据查询
extern u8 speed_up;  		//0无,1长按,2加速长按
//extern u8 medium;				//传播介质

extern int time_5s;				//5秒计时

extern int jsh_num;				//计时,查询的计数
extern int jsh_max;				//设置的计数
extern u8 com;						//串口指令是否正确
extern u8 auto_state;			//0手动,1初始,2继续,3结束

//extern double set_V;			//设定电压
//extern int bef_num;			//上个设定电压对应参数
//extern unsigned int control_V;	//控制电压参数
//extern int set_num;				//设定电压对应参数

extern int jsh_sta_Tem;		//计时起始温度
extern int jsh_end_Tem;		//计时结束温度
extern double now_Tem;				//当前温度
extern double now_res;		//当前电阻值=电压值x100 精确到0.01
extern int time_50000;			//50000次计数

extern double now_sta_Tem;		//当前起始温度
extern double now_end_Tem;		//当前结束温度

//extern double angle_du;		//角度
//extern double set_angle;	//设定角度
//extern double now_angle;	//当前角度
//extern int control_step;	//控制角度步数


extern int time_500m;			//500毫秒计时
extern u8 time_500m_flag;				//500毫秒计时标志

extern int time_100m;				//100毫秒计时
extern u8 time_100m_flag;				//100毫秒计时标志

extern u8 cs_flag;				//特殊命令标志

extern int V_array[20];		//采集电压


extern int LCDY_array[10];		//采集励磁电压
extern int SPFD_array[10];		//采集射频幅度
extern int HTJ_array[20];			//采集毫特计
extern int V_mun;							//采集数组序号
extern int HTJ_mun;							//毫特计数组序号

extern double Reality_VREF;		//实际基准电压


extern int time_array_mun;				//计时数组序号
extern int time_array_sum;				//计时数组总数

//extern u8 data_wait;					//等待发送数据
//extern int time_x0m;				//x0毫秒计时
//extern u8 time_x0m_flag;				//x0毫秒计时标志

extern int Freq_now;					//当前频率


//extern u8 pass;										//小车通过测速光电门
//extern u8 velocimeter;						//测速完成
//extern int disconnect_time;	//间断时间
//extern double dB_V;						//正玄波幅度
//extern double dB_V_avg;						//正玄波幅度的平均值
//extern u8 disconnect_condition;		//间断状态

//extern u8 PinLv_twinkle;//频率的某一位闪烁

static const u8 wz0[][2]=	//位置
{
	96,13,224,13,96,9
};

# define set_min_Tem 50			//设定温度下限
# define set_max_Tem 150		//设定温度上限

# define factor_A 0.00390802
# define factor_B -0.0000005802
//# define factor_C -0.0000000000042735

#endif
