/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * <h2><center>&copy; Copyright (c) 2020 STMicroelectronics.
  * All rights reserved.</center></h2>
  *
  * This software component is licensed by ST under Ultimate Liberty license
  * SLA0044, the "License"; You may not use this file except in compliance with
  * the License. You may obtain a copy of the License at:
  *                             www.st.com/SLA0044
  *
  ******************************************************************************
  */
/* Includes ------------------------------------------------------------------*/
#include "fos.h"
#include "hal_tim.h"
#include "osc_ui.h"
#include "gui.h"
#include "string.h"
#include "math.h"
#include "osc_measure.h"
#include "stdio.h"
#include "osc_api.h"
#include "osc_cfg.h"
#include "osc_menu.h"
/* Private includes ----------------------------------------------------------*/
FOS_TSK_REGISTER(osc_measure_thread,PRIORITY_0,1000);/* run as 1s */
/* extern */
extern unsigned char osc_run_mode(void);
extern widget_def measure_group[10];
extern unsigned char osc_X10X1_get(unsigned char chn);
static unsigned short max,min;
/* static freq mearsure */
static int freq_measure_ch(unsigned char chn , char * buf)
{
	/* set data */
	static unsigned int last_sys_time_us[2];
	static unsigned int last_tim2_cnt_pulse[2];	
	/* get time */
	unsigned int now_time = hal_sys_time_us();
	/* calbrate freq */
	unsigned int now_cnt = ( chn == 0 ) ? hal_tim2_cnt() : hal_tim4_cnt();
	/* cnt tes */
	float freq = (float)( now_cnt - last_tim2_cnt_pulse[chn] ) / ((float)( now_time - last_sys_time_us[chn] ) / 1000000) ;
	/* reset */
	last_tim2_cnt_pulse[chn] = now_cnt;
	last_sys_time_us[chn] = now_time;
	/* check */
	if( freq > 1000000 )
	{
		/* gewei */
		if( freq < 10000000 )
		{
		  sprintf(buf,"%1.3fMHz",freq / 1000000.0f);
		}
		else if( freq >= 10000000 && freq < 100000000 )
		{
			sprintf(buf,"%2.2fMHz",freq / 1000000.0f);
		}
		else
		{
			sprintf(buf,"%3.1fMHz",freq / 1000000.0f);
		}
	}
	else if( freq >= 1000 )
	{
		/* gewei */
		if( freq < 10000 )
		{
			sprintf(buf,"%1.3fKHz",freq / 1000.0f);
		}
		else if( freq >= 10000 && freq < 100000 )
		{
			sprintf(buf,"%2.2fKHz",freq / 1000.0f);
		}
		else
		{
			sprintf(buf,"%3.1fKHz",freq / 1000.0f);
		}	
	}
	else
	{
		/* gewei */
		if( freq < 10 )
		{
			sprintf(buf,"%1.3fHz ",freq );
		}
		else if( freq >= 10 && freq < 100 )
		{
			sprintf(buf,"%2.2fHz ",freq );
		}
		else
		{
			sprintf(buf,"%3.1fHz ",freq );
		}		
	}
	/* get len */
	osc_set_str(buf,8);	
	/* return OK */
	return FS_OK;
}
/* period copy */
static void osc_measure_peroid(unsigned char chn,char * bufd)
{
	/* set data */
	static unsigned int last_sys_time_us1[2];
	static unsigned int last_tim2_cnt_pulse1[2];	
	/* get time */
	unsigned int now_time = hal_sys_time_us();
	/* calbrate freq */
	unsigned int now_cnt = ( chn == 0 ) ? hal_tim2_cnt() : hal_tim4_cnt();
	/* cnt tes */
	float freq = (float)( now_cnt - last_tim2_cnt_pulse1[chn] ) / ((float)( now_time - last_sys_time_us1[chn] ) / 1000000) ;
	/* reset */
	last_tim2_cnt_pulse1[chn] = now_cnt;
	last_sys_time_us1[chn] = now_time;
	/* fds */
	float period = 1.0f / freq ;
	char * un;
	/* check */
	if( (int)(period * 1000.0f))
	{
		period *= 1000.0f;
		un = "ms";
	}
	else if( (int)(period * 1000000.0f))
	{
		period *= 1000000.0f;
		un = "us";
	}
	else if( (int)(period * 1000000000.0f))
	{
		period *= 1000000000.0f;
		un = "ns";
	}
	else
	{
		period *= 1.0f;
		un = "s";
	}
	/* sheck */
	sprintf(bufd,"%3.1f%s",period,un);
	/* get len */
	osc_set_str(bufd,7);
}
/* p-p measure */
static int peek_measure_ch(unsigned char chn , char * buf)
{
	/* osc vol scale */
	const osc_vol_scale_def * ovs;
	/* get */
	int ret = osc_api_peek(chn,&max,&min);
	/* check */
	if( ret == FS_OK )
	{
		/* get vol scale */
		ovs = osc_get_vol_scale(chn);
		/* calbrate ppk */
		float peek_mv = ((float)max - (float)min) / 50.0f * ovs->mv_int;
		/* check */
		if( osc_X10X1_get(chn) == 0 )
		{
			/* X 10 */
			peek_mv *= 10;
		}
		/* show */
		if( peek_mv > 1000 )
		{
			/* change */
			sprintf(buf,"%2.1fV", peek_mv / 1000.0f);				
		}
		else
		{
			sprintf(buf,"%3.1fmV", peek_mv );
		}
		/* get len */
		osc_set_str(buf,7);
		/* return OK */
		return FS_OK;
	}
	else
	{
		sprintf(buf,"0.0fmV");
	}
	/* bad data */
	return FS_ERR;
}
/* p-p measure */
static int max_measure_ch(unsigned char chn , char * buf)
{
	/*dd *//* dfe */
	osc_run_msg_def * runmsg8 = get_run_msg();
	/* osc vol scale */
	const osc_vol_scale_def * ovs;
	/* get */
	int ret = osc_api_peek(chn,&min,&max);
	/* check */
	if( ret == FS_OK )
	{
		/* get vol scale */
		ovs = osc_get_vol_scale(chn);
		/* calbrate ppk */
		float max_mv = (runmsg8->vol_offset_scale[chn] - (float)max) / 50.0f * ovs->mv_int;
		/* check */
		if( osc_X10X1_get(chn) == 0 )
		{
			/* X 10 */
			max_mv *= 10;
		}		
		/* show */
		if( max_mv >= 1000 || max_mv <= -1000 )
		{
			/* change */
			sprintf(buf,"%2.1fV", max_mv / 1000.0f);				
		}
		else
		{
			sprintf(buf,"%3.1fmV", max_mv );
		}
		/* get len */
		osc_set_str(buf,7);
		/* return OK */
		return FS_OK;
	}
	else
	{
		sprintf(buf,"0.0fmV");
	}
	/* bad data */
	return FS_ERR;
}
/* p-p measure */
static int min_measure_ch(unsigned char chn , char * buf)
{
	/*dd *//* dfe */
	osc_run_msg_def * runmsg8 = get_run_msg();
	/* osc vol scale */
	const osc_vol_scale_def * ovs;
	/* get */
	int ret = osc_api_peek(chn,&min,&max);
	/* check */
	if( ret == FS_OK )
	{
		/* get vol scale */
		ovs = osc_get_vol_scale(chn);
		/* calbrate ppk */
		float min_mv = (runmsg8->vol_offset_scale[chn] - (float)min) / 50.0f * ovs->mv_int;
		/* check */
		if( osc_X10X1_get(chn) == 0 )
		{
			/* X 10 */
			min_mv *= 10;
		}		
		/* show */
		if( min_mv >= 1000 || min_mv <= -1000 )
		{
			/* change */
			sprintf(buf,"%2.1fV", min_mv / 1000.0f);				
		}
		else
		{
			sprintf(buf,"%3.1fmV", min_mv );
		}
		/* get len */
		osc_set_str(buf,7);
		/* return OK */
		return FS_OK;
	}
	else
	{
		sprintf(buf,"0.0fmV");
	}
	/* bad data */
	return FS_ERR;
}
extern float_t rms_ch[2];
/* p-p measure */
static int rms_measure_ch(unsigned char chn , char * buf)
{
	/*dd *//* dfe */
	osc_run_msg_def * runmsg8 = get_run_msg();
	/* osc vol scale */
	const osc_vol_scale_def * ovs;
	/* get vol scale */
	ovs = osc_get_vol_scale(chn);
	/* calbrate ppk if( osc_X10X1_get(chn) == 0 ) */
	float rms_mv;
	/* get */
	if( chn == 0 )
	{
		rms_mv = (rms_ch[0] * 1.953125f) / 50.0f * ovs->mv_int;	
	}
	else
	{
		rms_mv = (rms_ch[1] * 1.953125f) / 50.0f * ovs->mv_int;	
	}
	/* change */
	if( osc_X10X1_get(chn) == 0 )
	{
		rms_mv *= 10.0f;
	}		
	/* set */
	sprintf(buf,"%3.2fV", rms_mv / 1000.0f);				
	/* get len */
	osc_set_str(buf,7);
	/* return OK */
	return FS_OK;
}
/* check and set str len */
static void osc_set_str(char * bdf,unsigned int limit)
{
	/* get len */
	int len = strlen(bdf);
	/* check */
	if( len < limit )
	{
		memset( bdf + len , ' ' , limit - len );
	}
	/* set tail */
	bdf[limit] = 0;	
	/* end of func */
}
/* check */
static void osc_measure_im(widget_def* wd)
{
	/* get pos */
	unsigned short pox;
	unsigned short poy;
	/* buffer */
	char buffer_m[16];
	/* check item */
	switch(wd->msg.my)
	{
		/* freq */
		case 0:
			freq_measure_ch(wd->msg.mx,buffer_m);
			pox = wd->msg.x + 68;
			poy = wd->msg.y + 3;
			/* set str */
			osc_set_str(buffer_m,8);
			/* show */
			osc_l1_string(wd->dev,pox,poy,buffer_m,81,4,1);	
			/* break */
			break;
		case 1:
			/* position */
			pox = wd->msg.x + 68;
			poy = wd->msg.y + 3;
			/* period */
			osc_measure_peroid(wd->msg.mx,buffer_m);
			/* show */
			osc_l1_string(wd->dev,pox,poy,buffer_m,81,4,1);			
			break;
		case 2:
			/* PPK */
			peek_measure_ch(wd->msg.mx,buffer_m);
			/* position */
			pox = wd->msg.x + 79;
			poy = wd->msg.y + 4;
			/* show */
			osc_l1_string(wd->dev,pox,poy,buffer_m,81,4,1);			
			/* show */
			break;
		case 3:
			/* PPK */
			max_measure_ch(wd->msg.mx,buffer_m);
			/* position */
			pox = wd->msg.x + 79;
			poy = wd->msg.y + 4;
			/* show */
			osc_l1_string(wd->dev,pox,poy,buffer_m,81,4,1);			
			/* show */			
			break;
		case 4:
			/* PPK */
			min_measure_ch(wd->msg.mx,buffer_m);
			/* position */
			pox = wd->msg.x + 79;
			poy = wd->msg.y + 4;
			/* show */
			osc_l1_string(wd->dev,pox,poy,buffer_m,81,4,1);			
			/* show */
			break;
		case 5:
			rms_measure_ch(wd->msg.mx,buffer_m);
			/* position */
			pox = wd->msg.x + 79;
			poy = wd->msg.y + 4;
			/* show */
			osc_l1_string(wd->dev,pox,poy,buffer_m,81,4,1);		
			break;
		case 6:
			break;
		case 7:
			break;
		case 8:
			break;
		case 9:
			break;		
		default:
			break;
	}
}
/* measure thread */
static void osc_measure_thread(void)
{
	/* check run mode */
	if( osc_run_mode() == RUN_STOP_MODE )	
	{
		return;
	}
	/* start measure thread */
	for( int i = 0 ; i < 10 ; i ++ )
	{
		/* check enable */
		if( measure_group[i].msg.upd == 0xE0 )
		{
			/* measure */
			osc_measure_im(&measure_group[i]);
		}
	}
}






























