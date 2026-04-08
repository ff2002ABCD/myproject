#include "main.h"
#include "dac.h"
#include "adc.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"
#include "stdio.h"
#include "osc.h"
#include "stdlib.h"
#include "control.h"
#include "measure.h"
#include "menu.h"
#include "flash.h"
#include "string.h"
#include "function.h"
CURSOR cursor=T_LIGHT;
CURSOR cursor_last;
CALIBORATION_STATE caliboration_state=NONE;
char *txtname[]={"T_light","T_pool","ctrl","I_hori","I_vert","I_scan","scan_shape",
	"freq","time","mag_scale","light_scale","trig_mode","mag_offset","light_offset",
"trig_value","mag_couple","light_couple","step"};
float temp_light_set=90,temp_pool_set=60,temp_pool_now,temp_light_now,current_hori=50,current_vert=200,current_scan=100;
uint16_t freq_scan=10;
uint8_t scan_shape_now,time_grid_now=1,mag_scale_now=1,light_scale_now=1,trig_mode_now=0;
char *scan_shape[]={"三角波","方波","正弦波"};
char *time_grid[]={"50ms","20ms","10ms"};
char *mag_scale[]={"10V","5V","2V","1V","500mv"};
char *light_scale[]={"50mV","20mv","10mV"};
char *trig_mode[]={"磁路上升沿","磁路下降沿","光路上升沿","光路下降沿"};
_Bool start_ctrl=0;
extern int flag;
void up_button()
{
	if(cursor==CALIBO)
	{
		switch(caliboration_state)
		{
			case CH1_OFFSET:del_zero_ch1+=calibo_step_zero;break;
			case CH1_K_1:del_k_ch1+=calibo_step_k;break;
			case CH1_K_2:del_k_ch1-=calibo_step_k;break;
			case CH2_OFFSET:del_zero_ch2+=calibo_step_zero;break;
			case CH2_K_1:del_k_ch2+=calibo_step_k;break;
			case CH2_K_2:del_k_ch2-=calibo_step_k;break;
			default:break;
		}
		return;
	}
	if(cursor==0) cursor=16;
	else cursor--;
}

void down_button()
{	
	if(cursor==CALIBO)
	{
		switch(caliboration_state)
		{
			case CH1_OFFSET:del_zero_ch1-=calibo_step_zero;break;
			case CH1_K_1:del_k_ch1-=calibo_step_k;break;
			case CH1_K_2:del_k_ch1+=calibo_step_k;break;
			case CH2_OFFSET:del_zero_ch2-=calibo_step_zero;break;
			case CH2_K_1:del_k_ch2-=calibo_step_k;break;
			case CH2_K_2:del_k_ch2+=calibo_step_k;break;
			default:break;
		}
		return;
	}
	if(cursor==16) cursor=0;
	else cursor++;
}

void left_button()
{
	switch(cursor)
	{
		case T_LIGHT:if(temp_light_set>80)temp_light_set-=0.1;break;
		case T_POOL:if(temp_pool_set>50)temp_pool_set-=0.1;break;
		case I_HORI:if(current_hori>-200)current_hori-=0.1;break;
		case I_SCAN:if(current_scan>0)current_scan-=0.1;DAC_renew();break;
		case I_VERT:if(current_vert>-200)current_vert-=0.1;DAC_renew();break;
		case FREQ:if(freq_scan>5) freq_scan--;DAC_renew();break;
		case SCAN_SHAPE:if(scan_shape_now>0)scan_shape_now--;else scan_shape_now=scan_shape_max-1;DAC_renew();break;
		case TIME_GRID:if(time_grid_now>0)time_grid_now--;else time_grid_now=time_grid_max-1;break;
		case MAG_SCALE:if(mag_scale_now>0)mag_scale_now--;else mag_scale_now=mag_scale_max-1;break;
		case LIGHT_SCALE:if(light_scale_now>0) light_scale_now--;else light_scale_now=light_scale_max-1;break;
		case TRIG_MODE:if(trig_mode_now>0) trig_mode_now--;else trig_mode_now=3;break;
		case MAG_OFFSET:offset_ch1--;break;
		case LIGHT_OFFSET:offset_ch2--;break;
		case TRIG_VALUE:
			if(Trigger_state==1|Trigger_state==2)
			{
				Trigger_set_offset_ch1-=step;
				if(Trigger_set_offset_ch1<-128) Trigger_set_offset_ch1=-128;
			}
			else
			{
				Trigger_set_offset_ch2-=step;
				if(Trigger_set_offset_ch2<-128) Trigger_set_offset_ch2=-128;
			}
			break;
		case MAG_COUPLE:if(Ouhe==0) Ouhe=1;else Ouhe=0;break;
		case LIGHT_COUPLE:if(Ouhe1==0) Ouhe1=1;else Ouhe1=0;break;
		default:break;
	}
}

void right_button()
{
	switch(cursor)
	{
		case T_LIGHT:if(temp_light_set<110)temp_light_set+=0.1;break;
		case T_POOL:if(temp_pool_set<80)temp_pool_set+=0.1;break;
		case I_HORI:if(current_hori<200)current_hori+=0.1;break;
		case I_SCAN:if(current_scan<200)current_scan+=0.1;DAC_renew();break;
		case I_VERT:if(current_vert<200)current_vert+=0.1;DAC_renew();break;
		case FREQ:if(freq_scan<50) freq_scan++;DAC_renew();break;
		case SCAN_SHAPE:if(scan_shape_now<scan_shape_max-1)scan_shape_now++;else scan_shape_now=0;DAC_renew();break;
		case TIME_GRID:if(time_grid_now<time_grid_max-1)time_grid_now++;else time_grid_now=0;break;
		case MAG_SCALE:if(mag_scale_now<mag_scale_max-1)mag_scale_now++;else mag_scale_now=0;break;
		case LIGHT_SCALE:if(light_scale_now<light_scale_max-1) light_scale_now++;else light_scale_now=0;break;
		case TRIG_MODE:if(trig_mode_now<3) trig_mode_now++;else trig_mode_now=0;break;
		case MAG_OFFSET:offset_ch1++;break;
		case LIGHT_OFFSET:offset_ch2++;break;
		case TRIG_VALUE:
			if(Trigger_state==1|Trigger_state==2)
			{
				Trigger_set_offset_ch1+=step;
				if(Trigger_set_offset_ch1>127) Trigger_set_offset_ch1=127;
			}
			else
			{
				Trigger_set_offset_ch2+=step;
				if(Trigger_set_offset_ch2>127) Trigger_set_offset_ch2=127;
			}
			break;
		case MAG_COUPLE:if(Ouhe==0) Ouhe=1;else Ouhe=0;break;
		case LIGHT_COUPLE:if(Ouhe1==0) Ouhe1=1;else Ouhe1=0;break;
		default:break;
	}
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
	HAL_TIM_PWM_Start(&htim8,TIM_CHANNEL_1);
	HAL_TIM_PWM_Start(&htim8,TIM_CHANNEL_2);
	HAL_DMA_Start_IT(&hdma_tim8_ch1,(uint32_t)&GPIOD->IDR,(uint32_t)mem2,S*K);
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

void fun_button()
{
	switch(cursor)
	{
	
		default:break;
	}
}

void renew_menu()
{
	if(cursor!=17) printf("vis step,0\xff\xff\xff");
	else 	printf("vis step,1\xff\xff\xff");
	for(int i=0;i<18;i++)
	{
		 if(cursor==i) continue;
		printf("%s.bco=50779\xff\xff\xff",txtname[i]);
	}
	printf("%s.bco=61277\xff\xff\xff",txtname[cursor]);
	switch(cursor)
	{	
		case CALIBO:
			if(caliboration_state>0&&caliboration_state<7)
			printf("step.txt=\"校准%d/6\"\xff\xff\xff",caliboration_state);
			else if(caliboration_state==7)
				printf("step.txt=\"按确定保存\"\xff\xff\xff");
			break;
		case T_LIGHT:printf("%s.txt=\"%.1f℃\"\xff\xff\xff",txtname[T_LIGHT],temp_light_set);break;
		case T_POOL:printf("%s.txt=\"%.1f℃\"\xff\xff\xff",txtname[T_POOL],temp_pool_set);break;
		case CTRL:
			if(start_ctrl==0) printf("%s.txt=\"开始控温\"\xff\xff\xff",txtname[CTRL]);
			else printf("%s.txt=\"结束控温\"\xff\xff\xff",txtname[CTRL]);
			break;
		case I_HORI:printf("%s.txt=\"%.1fmA\"\xff\xff\xff",txtname[I_HORI],current_hori);break;
		case I_VERT:printf("%s.txt=\"%.1fmA\"\xff\xff\xff",txtname[I_VERT],current_vert);break;
		case I_SCAN:printf("%s.txt=\"%.1fmA\"\xff\xff\xff",txtname[I_SCAN],current_scan);break;
		case SCAN_SHAPE:printf("%s.txt=\"%s\"\xff\xff\xff",txtname[SCAN_SHAPE],scan_shape[scan_shape_now]);break;
		case FREQ:printf("%s.txt=\"%dHz\"\xff\xff\xff",txtname[FREQ],freq_scan);break;
		case TIME_GRID:printf("%s.txt=\"%s/Div\"\xff\xff\xff",txtname[TIME_GRID],time_grid[time_grid_now]);break;
		case MAG_SCALE:printf("%s.txt=\"%s/Div\"\xff\xff\xff",txtname[MAG_SCALE],mag_scale[mag_scale_now]);break;
		case LIGHT_SCALE:printf("%s.txt=\"%s/Div\"\xff\xff\xff",txtname[LIGHT_SCALE],light_scale[light_scale_now]);break;
		case TRIG_MODE:printf("%s.txt=\"%s\"\xff\xff\xff",txtname[TRIG_MODE],trig_mode[trig_mode_now]);break;
		case MAG_COUPLE:
			if(Ouhe==0) printf("%s.txt=\"%s\"\xff\xff\xff",txtname[MAG_COUPLE],"DC");
			else printf("%s.txt=\"%s\"\xff\xff\xff",txtname[MAG_COUPLE],"AC");
			break;
		case LIGHT_COUPLE:
			if(Ouhe1==0) printf("%s.txt=\"%s\"\xff\xff\xff",txtname[LIGHT_COUPLE],"DC");
			else printf("%s.txt=\"%s\"\xff\xff\xff",txtname[LIGHT_COUPLE],"AC");
			break;
		default:break;
	}
}
