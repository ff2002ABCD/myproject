#include "includes.h"

CURSOR cursor=TIME_GRID;
CURSOR cursor_last;
CALIBORATION_STATE caliboration_state=NONE;
char *txtname[]={"T_light","T_pool","ctrl","I_hori","I_vert","I_scan","scan_shape",
	"freq","time","mag_scale","light_scale","trig_mode","mag_offset","light_offset",
"trig_value","mag_couple","light_couple","step"};
float temp_light_set=90,temp_pool_set=60,temp_pool_now,temp_light_now,current_hori=10,current_vert=20,current_scan=350;
uint16_t freq_scan=1;
uint8_t scan_shape_now=1,time_grid_now=1,mag_scale_now=1,light_scale_now=1,trig_mode_now=0;
char *scan_shape[]={"三角波","方波","正弦波"};
char *time_grid[]={"50ms","20ms","10ms","5ms","2ms","1ms","500us","200us","100us","50us","20us","10us","5us","2us","1us","500ns"};
char *mag_scale[]={"10V","5V","2V","1V","500mV","200mV","100mV","50mV","20mV","10mV"};
char *light_scale[]={"10V","5V","2V","1V","500mV","200mV","100mV","50mV","20mV","10mV"};
char *trig_mode[]={"磁路上升沿","磁路下降沿","光路上升沿","光路下降沿"};
_Bool start_ctrl=0;
extern int flag;

void up_button()
{
	
}

void down_button()
{	
	
}

void left_button()
{
	
	
}

void right_button()
{
	
}

void confirm_button()
{
	switch(cursor)
	{
		case CALIBO:
			if(caliboration_state!=7) caliboration_state++;
			else
			{
				caliboration_state=0;
				cursor=0;
				load_writedata();
				STMFLASH_OnlyWrite(0x08019000,Flash_WData,4);
			}
			calibo_step();
		break;
		case CTRL:if(start_ctrl==0) start_ctrl=1;else start_ctrl=0;break;
		default:right_button();break;
	}
}

void cancel_button()
{
	flag=0;
	osc_state=FREE;
	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_1);
	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_2);
	HAL_DMA_Start_IT(&hdma_tim1_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S*K);
	if(*(__IO uint32_t*)0x08019000==0xffffffff)
	{
		if(cursor!=CALIBO) cursor=CALIBO;
		if(caliboration_state==0) 
		{
			caliboration_state=1;
		}
		else
		{			
			caliboration_state--;
			if(caliboration_state==0) cursor=0;
		}
		calibo_step();
	}
}


void renew_menu()
{

}


void calibo_step()
{
	switch(caliboration_state)
	{
		case CH1_OFFSET:
		{
			offset_ch1=0;
			printf("move zero1,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch1),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch1)));
		}break;
		case CH1_K_1:
		{
			offset_ch1=100;
			printf("move zero1,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch1),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch1)));
		}break;
		case CH1_K_2:
		{
			offset_ch1=-100;
			printf("move zero1,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch2),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch1)));
		}break;	
		case CH2_OFFSET:
		{
			offset_ch2=0;
			printf("move zero2,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch2),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch2)));
		}break;
		case CH2_K_1:
		{
			offset_ch2=100;
			printf("move zero2,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch2),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch2)));
		}break;
		case CH2_K_2:
		{
			offset_ch2=-100;
			printf("move zero2,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch2),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch2)));
		}break;
		case SAVE:
		{
			offset_ch1=0;
			printf("move zero1,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch1),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch1)));
			offset_ch2=0;
			printf("move zero2,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch2),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch2)));
		}break;
		default:break;
	}
}

