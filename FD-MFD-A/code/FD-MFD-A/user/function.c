#include "function.h"
#include "dac.h"
#include "tim.h"
double test_position[MAX_NUMBER];
int start_position_int,end_position_int,position_step_int;
double start_position,end_position,position_step,position_num;
float GaX,GaY,GaZ,rawGaX,rawGaY,rawGaZ,GaXmax,GaXmin,GaYmax,GaYmin,GaZmax,GaZmin,strength,Current=0,position,Voltage_dac,Voltage_out,k=6.53;
float GaX_ground,GaY_ground,GaZ_ground;
float pos_measure_start;
float GaX_array[AVER_NUM],GaY_array[AVER_NUM],GaZ_array[AVER_NUM],strength_array[AVER_NUM];
TABLE table[MAX_GROUP][MAX_NUMBER];
uint8_t table_length[MAX_NUMBER],sheet_length;
uint8_t number_now,sheet_now,group_now;//用于指示当前操作目标

void gener_cordinate()
{
	input_judge=0;
	start_position=start_position_int/100.00;
	end_position=end_position_int/100.00;
	position_step=position_step_int/100.00;
	if(position_step==0) return;
//	if(end_position-start_position<=0) return;
	if((end_position-start_position)/position_step>50) return;
	if(fabs((end_position-start_position)/position_step-(int)((end_position-start_position)/position_step))<1e-6)
	{
		position_num=(end_position-start_position)/position_step+1;
		input_judge=1;
		for(int i=0;i<position_num;i++)
		{
			test_position[i]=start_position+i*position_step;
		}
	}
	
}

void start_measure()
{
	static int i=0;
	hmc5883l_rawread(&rawGaX, &rawGaY, &rawGaZ);
	GaX_array[i]=x1*(rawGaX-x0);
	GaY_array[i]=y1*(rawGaY-y0);
	GaZ_array[i]=z1*(rawGaZ-z0);
	strength_array[i]=sqrt(GaX_array[i]*GaX_array[i]+GaY_array[i]*GaY_array[i]+GaZ_array[i]*GaZ_array[i]);
	i++;
	if(i==AVER_NUM) i=0;
}

void measure_ground()
{
	get_averdata();
	GaX_ground=GaX;
	GaY_ground=GaY;
	GaZ_ground=GaZ;
	
}

//记录数据到table
void record_data()
{
	table[group_now][number_now].Current=Current;
	table[group_now][number_now].GaX=GaX*100;
	table[group_now][number_now].GaY=GaY*100;
	table[group_now][number_now].GaZ=GaZ*100;
	table[group_now][number_now].Pos=position;
	table[group_now][number_now].Strength=strength*100;
	table_length[group_num]++;
}

//输出sheet
void data_sheet()
{
	printf("group_num.txt=\"第%d组\"\xff\xff\xff",cursor_group_num+1);
	for(int i=0;i<6;i++)
	{
		
		printf("n%d.txt=\"%d\"\xff\xff\xff",i,sheet_now*6+i+1);
		printf("pos%d.txt=\"%.2f\"\xff\xff\xff",i,table[cursor_group_num][sheet_now*6+i].Pos);
		printf("a%d.txt=\"%.1f\"\xff\xff\xff",i,table[cursor_group_num][sheet_now*6+i].Current);
		printf("m%d.txt=\"%.1f\"\xff\xff\xff",i,table[cursor_group_num][sheet_now*6+i].Strength);
		printf("x%d.txt=\"%.1f\"\xff\xff\xff",i,table[cursor_group_num][sheet_now*6+i].GaX);
		printf("y%d.txt=\"%.1f\"\xff\xff\xff",i,table[cursor_group_num][sheet_now*6+i].GaY);
		printf("z%d.txt=\"%.1f\"\xff\xff\xff",i,table[cursor_group_num][sheet_now*6+i].GaZ);
	}
}

void Current_control()
{
	Voltage_dac=(k*Current/1000+3)/2;
	HAL_DAC_SetValue(&hdac,DAC_CHANNEL_1,DAC_ALIGN_12B_R,4096.00*Voltage_dac/3.30);
}

void system_init()
{
	HAL_DAC_Start(&hdac, DAC_CHANNEL_1);
	HAL_TIM_Encoder_Start(&htim2,TIM_CHANNEL_ALL);
	__HAL_TIM_SetCounter(&htim2,30000);
//	HAL_DAC_SetValue(&hdac,DAC_CHANNEL_1,DAC_ALIGN_12B_R,4096.00*1.283/3.30);
	if(*(__IO uint32_t*)0x08009000!=0xffffffff) k= *(__IO uint32_t*)0x08009000/100.000;
//	Current_control();
//	Current=100;
	Init_HMC5883L_HAL(&hi2c1);
	HAL_TIM_Base_Start_IT(&htim3);
	HAL_TIM_Base_Start_IT(&htim4);
	HAL_TIM_Base_Start_IT(&htim5);
	HAL_TIM_Base_Start_IT(&htim6);
	page=MAIN;
	printf("page 主页面\xff\xff\xff");
	
//	ch376_init();
//	ch376_writetest();
	//Flash_writeData();
}

void get_averdata()
{
  GaX=0,GaY=0,GaZ=0,GaXmax=0,GaYmax=0,GaZmax=0,GaXmin=0,GaYmin=0,GaZmin=0;
	strength=0;
	for(int i=0;i<AVER_NUM;i++)
	{
//		if(GaX_array[i]>GaXmax) GaXmax=GaX_array[i];
//		if(GaY_array[i]>GaYmax) GaYmax=GaY_array[i];
//		if(GaZ_array[i]>GaZmax) GaZmax=GaZ_array[i];
//		if(GaX_array[i]<GaXmin) GaXmin=GaX_array[i];
//		if(GaY_array[i]<GaYmin) GaYmin=GaY_array[i];
//		if(GaZ_array[i]<GaZmin) GaZmin=GaZ_array[i];
		
		GaX+=GaX_array[i];
		GaY+=GaY_array[i];
		GaZ+=GaZ_array[i];
		strength+=strength_array[i];
	}
//	GaX=GaX-GaXmax-GaXmin;
//	GaY=GaY-GaYmax-GaYmin;
//	GaZ=GaZ-GaZmax-GaZmin;
	GaX=GaX/AVER_NUM;
	GaY=GaY/AVER_NUM;
	GaZ=GaZ/AVER_NUM;
	strength=strength/AVER_NUM;
}

void set_zero()
{
	GaX-=GaX_ground;
	GaY-=GaY_ground;
	GaZ-=GaZ_ground;
	strength=sqrt(GaX*GaX+GaY*GaY+GaZ*GaZ);
}