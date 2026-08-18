

#include "main.h"

struct KEY_DATA key_data;									//----- key_data

u8 mod;						//1显示四个值

u8 speed_up;  		//0无,1长按,2加速长按
//u8 medium;				//传播介质

int time_5s;				//5秒计时

int jsh_num;				//计时,查询的计数
int jsh_max;				//设置的计数
u8 com;						//串口指令是否正确
u8 auto_state;			//0手动,1初始,2继续,3结束

//double set_V;				//设定电压
//int bef_num;			//上个设定电压对应参数
//unsigned int control_V;		//控制电压参数
//int set_num;				//设定电压对应参数

int jsh_sta_Tem;		//计时起始温度
int jsh_end_Tem;		//计时结束温度
double now_Tem;				//当前温度
double now_res;		//当前电阻值=电压值x100 精确到0.01
int time_50000;			//50000次计数

double now_sta_Tem;		//当前起始温度
double now_end_Tem;		//当前结束温度
//double angle_du;		//角度
//double set_angle;	//设定角度
//double now_angle;	//当前角度
//int control_step;	//控制角度步数

int time_500m;			//500毫秒计时
 u8 time_500m_flag;				//500毫秒计时标志

int time_100m;				//100毫秒计时
u8 time_100m_flag;				//100毫秒计时标志

u8 cs_flag;				//特殊命令标志
int V_array[20];		//采集电压
int LCDY_array[10];		//采集励磁电压
int SPFD_array[10];		//采集射频幅度
int HTJ_array[20];			//采集毫特计
int V_mun;							//采集数组序号
int HTJ_mun;							//毫特计数组序号

double Reality_VREF;		//实际基准电压

int Freq_now;					//当前频率

int time_array_mun;				//计时数组序号
int time_array_sum;				//计时数组总数

int main()
{
//	unsigned char jl[6];
//	float xsh_time;
	int choose[6] = {0,0,0,0,0,0};			//选择项，0手动自动，1主界面，2参数设置，3数据查询
	int temp_i;
	int temp_j;
	double temp_d2;
	double temp_d;
//	double temp_i_array10[10];
//	double temp_i_array50[50];
	u16 temp_16;
//	char temp_c;
//	char temp_ch_10[10] = {32,32,32,32,32,32,32,32,32,32};
	char temp_ch_8[8] = {32,32,32,32,32,32,32,32};
	char temp_ch_7[7] = {32,32,32,32,32,32,32};
	char temp_ch_6[6] = {32,32,32,32,32,32};
	char temp_ch_5[5] = {32,32,32,32,32};
	char temp_ch_4[4] = {32,32,32,32};
	char temp_ch_3[3] = {32,32,32};
//	char temp_ch_2[2] = {32,32};
//	char a[5] = "@#&^!";	
//	char check[5] = {0,1,3,9,10};
//	char 	open[5] = "@#&^!";		//打开串口
//	char close[5] = "$%&~*";		//关闭串口

	u8 key_num;
	mod = 99;
	SysTick_Init(72);
	Lcd_Init();						//LCD初始化
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);  //中断优先级分组
//	LED_Init();
	KEY_Init();
//	AD9833_Init();
//	Photo_switch_Init();

		
	Filter_Init();
	
	TIM4_Init(5000-1,7200-1);  //定时500ms
	TIM3_Init(10000-1,720-1);  //定时100ms
	Frequency_Init();
//	USART1_Init(9600);
//	IIC_Init();
	ADS1220_Init();//满量程5V

//	TIM1_Init(50000-1,7200-1);	//定时5s
//	Frequency_Init();
	delay_s(2);

	speed_up = 0;

	temp_i = 0;
	
	time_5s = 0;				//5秒计时

  jsh_max = 0;				//设置的计数
	jsh_num = 0;
	com = 0;
	auto_state = 0;
//	control_V = 0;
	
	jsh_sta_Tem = 105;		//计时起始温度
	jsh_end_Tem = 95;		//计时结束温度
	now_Tem = 0;
	now_res = 100;		//当前电阻值=电压值x100 精确到0.01
	time_50000 = 0;
	V_mun = 0;
	HTJ_mun = 0;
	time_array_mun = 0;				//计时数组序号
	time_array_sum = 0;				//计时数组总数
	
	time_500m = 0;			//计时标志
	time_500m_flag = 0;				//结束计时标志
//	
//	data_wait = 0;					//等待发送数据
	
	time_100m = 0;				//100毫秒计时
	time_100m_flag = 0;				//100毫秒计时标志
	
	for(temp_i = 0;temp_i < 20;temp_i++){
		V_array[temp_i] = 16000;
	}
	
	for(temp_i = 0;temp_i < 10;temp_i++){
		LCDY_array[temp_i] = 0;
		SPFD_array[temp_i] = 0;
//		HTJ_array[temp_i] = 0;
	}
	
	for(temp_i = 0;temp_i < 20;temp_i++){
		HTJ_array[temp_i] = 0;
	}
//	time_x0m = 0;				//x0毫秒计时
//	time_x0m_flag = 0;				//x0毫秒计时标志

	
	key_data.key = 0;
	key_data.key_cishu = 0;
	key_data.key_long = 0;
	key_data.key_number = 0;
	key_data.key_number_t1 = 0;
	key_data.key_number_t2 = 0;
	key_data.key_time = 0;
	key_num = 0;
	
	send_command(0x01);//清屏
	delay_ms(5);	
	Disp_black();
	Lcd_Display(0x80,"励磁电流: 2000mA",16);
	Lcd_Display(0x90,"射频幅度: 20.00V",16);
	Lcd_Display(0x88,"毫特计:-2000.0mT",16);
	Lcd_Display(0x98,"频率: 24000000Hz",16);
	
	time_5s = 0;				//未超时
	TIM_SetCounter(TIM3,0);
	mod = 1;
	
	while(1)
	{	
//		temp_i = ADS1220_Config(4);//偏移
//		if(temp_i >= 8388607){
//			temp_i = temp_i - 16777216;
//		}
//		delay_ms(1);
		//采集励磁电压,射频幅度,毫特计
		temp_j = ADS1220_Config(1);
		if(temp_j >= 8388607){
			LCDY_array[V_mun] = temp_j - 16777216;
		}else{
			LCDY_array[V_mun] = temp_j;
		}
		delay_ms(1);
		temp_j = ADS1220_Config(2);
		if(temp_j >= 8388607){
			SPFD_array[V_mun] = temp_j - 16777216;
		}else{
			SPFD_array[V_mun] = temp_j;
		}
		delay_ms(1);
		temp_j = ADS1220_Config(3);
		if(temp_j >= 8388607){
			HTJ_array[V_mun] = temp_j - 16777216;
		}else{
			HTJ_array[V_mun] = temp_j;
		}
		delay_ms(1);
		V_mun++;
		if(V_mun >= 10){
			V_mun = 0;
		}
		
		//毫特计更新
//		if(time_100m_flag == 1){
//			time_100m_flag = 0;
//			
//			temp_j = ADS1115_Conversion_1(2);
//			if(temp_j >= 32768){
//				HTJ_array[HTJ_mun] = temp_j - 65536;
//			}else{
//				HTJ_array[HTJ_mun] = temp_j;
//			}
//			
//			HTJ_mun++;
//			if(HTJ_mun >= 10){
//				HTJ_mun = 0;
//			}
//		}
		//显示更新
		if(time_500m_flag == 1){
			//频率
			temp_d = Freq_now * 1.0000172;//误差修正
			sprintf(temp_ch_8, "%8d", (int)temp_d);
			Lcd_Display(0x9B,temp_ch_8,8);
			
			//励磁电压
			temp_d = avg_Filter_int(LCDY_array,10);
			temp_d2 = temp_d / 8388608.0 * Reality_VREF * 4000.0;//=x/8388608*Reality_VREF*4*1000放大4倍
			if(temp_d2 < 0){
				temp_d2 = 0;
			}
			sprintf(temp_ch_4, "%4.0f", temp_d2);
			Lcd_Display(0x85,temp_ch_4,4);
			
			//射频幅度
			temp_d = avg_Filter_int(SPFD_array,10);
			temp_d2 = temp_d / 2097152 * Reality_VREF;//=x/8388608*Reality_VREF*4放大4倍
			if(temp_d2 < 0){
				temp_d2 = 0;
			}
			sprintf(temp_ch_5, "%5.2f", temp_d2);
			for(temp_i = 0;temp_i < 5;temp_i++){
				temp_ch_6[temp_i] = temp_ch_5[temp_i];
			}
			temp_ch_6[5] = 'V';
			Lcd_Display(0x95,temp_ch_6,6);
			
			//毫特计
			temp_d = avg_Filter_int(HTJ_array,10);
			temp_d2 = temp_d / 8388608.0 * Reality_VREF * -2000.0;//=x/8388608*Reality_VREF*-2*1000反向放大2倍,2V=2000mT
//			temp_d2 = (temp_d*0.0001875-2.5)*-2000.0;//=(x/32768*6.144-2.5)*-2*100*10
			sprintf(temp_ch_7, "%7.1f", temp_d2);
			for(temp_i = 0;temp_i < 7;temp_i++){
				temp_ch_8[temp_i+1] = temp_ch_7[temp_i];
			}
			temp_ch_8[0] = ':';
			Lcd_Display(0x8B,temp_ch_8,8);
			
			time_500m_flag = 0;
		}

	}
}



