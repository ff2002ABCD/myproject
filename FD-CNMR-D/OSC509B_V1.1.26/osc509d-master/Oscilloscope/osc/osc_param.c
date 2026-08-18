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
#include "osc_menu.h"
#include "string.h"
#include "osc_cfg.h"
#include "osc_param.h"
#include "k24c02.h"
#include "osc.h"
#include "hal_iic.h"
#include "main.h"
/* Private includes ----------------------------------------------------------*/
#define OSC_FLASH_EEPROM_ADDR  ( 0x08000000 + 0x20000 * 7 )
/* Includes ------------------------------------------------------------------*/
FOS_TSK_REGISTER(osc_param_thread,PRIORITY_IDLE,100); /* gui detecter task run as idle */
FOS_INODE_REGISTER("osc_thread",osc_param_heap,osc_param_init,0,4);
/* FOS task */
/* iic sta change */
FOS_TSK_REGISTER(hal_iic_sta,PRIORITY_4,100);
/* tmp param */
static osc_run_msg_def osc_m_tmp;
/* dfe */
static osc_run_msg_def * runmsg;
/* sta */
extern void osc_param_sys_set(unsigned int * src , unsigned char b_data,unsigned char index);
static int osc_flash_eeprom_read(osc_run_msg_def * ormd,unsigned int *);
static int osc_flash_eeprom_write(osc_run_msg_def * orew);
extern unsigned int hal_sys_time_us(void);
extern unsigned int touch_idle_cnt;
extern unsigned char cal_step_start;
/* heap init */
static int osc_param_heap(void)
{
	return FS_OK;
}
/* check sum */
static unsigned char osc_param_check(unsigned char * dat,unsigned int len)
{
	/* sum */
	unsigned char xor_t = 0;
	/* ce */
	for( int i = 0 ; i < len ; i ++ )
	{
		xor_t += dat[i];
	}
	/* return */
	return xor_t;
}
/* write flash */
void osc_write_flash_block(unsigned int addr,void * d)
{
	/* check*/
	unsigned char * dfeee = (unsigned char *)d;
	/* need erase flash */
	HAL_FLASH_Unlock();
	/* resd */
	for( int i = 0 ; i < 4 ; i ++ )
	{
		HAL_FLASH_Program(32,(unsigned int)addr + i * 32 ,(unsigned int)&dfeee[i*32]);
	}			
}
/* first check */
static int osc_flash_eeprom_init(void)
{
	unsigned int dep = 0;
	/* sey */
	int ret = osc_flash_eeprom_read(&osc_m_tmp,&dep);
	/* check */
	if( ret == FS_OK )
	{
		if( dep > 1000 )
		{
			/* need erase flash */
			HAL_FLASH_Unlock();
			/* set */
#if OSC_STM32H750	
			/* set */
			FLASH_Erase_Sector(7,FLASH_BANK_1,FLASH_VOLTAGE_RANGE_3);	
#else
			for( int i = 0 ; i < 16 ; i ++ )
			{
				FLASH_Erase_Sector(7*16+i,FLASH_BANK_1,0x20);	
			}
#endif		
			/* check */
			osc_flash_eeprom_write(&osc_m_tmp);
		}
		/* progmer */
		return FS_OK;
	}
	/* ok */
	return FS_ERR;
}
/* osc param read */
static int osc_flash_eeprom_read(osc_run_msg_def * ormd,unsigned int * ind)
{
	/* tm 0*/
	unsigned char rd[128];
	osc_run_msg_def * or_f;
	unsigned int t_i = 0xffff;
		/* check */
	unsigned char * flash_eeprom_addr_base = (unsigned char *)OSC_FLASH_EEPROM_ADDR;
	/* read */
	for( int i = 0 ; i < 1024 ; i ++ )
	{
		unsigned char * tpf = &flash_eeprom_addr_base[i * 128];
		/* read */
		memcpy(rd,tpf,128);
		/* check */
		or_f = ( osc_run_msg_def * )rd;
		/* check */
		if( or_f->check == osc_param_check((unsigned char *)or_f,sizeof(osc_run_msg_def)- 1))
		{
			/* ok . next */
			t_i = i;
		}
		else
		{
			/* check available */
			if( t_i == 0xffff )
			{
				/* error */
				return FS_ERR;
			}
			else
			{
				/* copy */
				tpf = &flash_eeprom_addr_base[t_i * 128];
				/* get */
				memcpy(ormd,tpf,sizeof(osc_run_msg_def));
				/* x */
				*ind = t_i;
				/* return */
				return FS_OK;
			}
		}
	}
	/* error */
	return FS_ERR;
}
/* static write */
static int osc_flash_eeprom_write(osc_run_msg_def * orew)
{
	/* get */
	unsigned char wd[128];
		/* check */
	unsigned char * flash_eeprom_addr_base = (unsigned char *)OSC_FLASH_EEPROM_ADDR;
	/* read */
	for( int i = 0 ; i < 1024 ; i ++ )
	{
		/* read */
		memcpy(wd,&flash_eeprom_addr_base[i * 128] , 128);
		/* check 0xFF */
		int j;
		/* check 0xff */
		for( j = 0 ; j < 128 ; j ++ )
		{
			if( wd[j] != 0xff )
			{
				break;
			}
		}
		/* check */
		if( j == 128 )
		{
			/* ok get write */
			osc_write_flash_block((unsigned int)flash_eeprom_addr_base + i * 128,orew);
			/* return */
			return FS_OK;
		}
	}
	/* error */
	return FS_ERR;
}
/* osc_param_init */
static int osc_param_init(void)
{
	/* init */
	int rett = osc_flash_eeprom_init();
	/* get osc */
	runmsg = get_run_msg();
	/* check */
	if( rett == FS_OK )
	{
		/* check ok */
		memcpy(runmsg,&osc_m_tmp,sizeof(osc_m_tmp));
	  /* ok */
	}
	else
	{
		/* init */
		memset(runmsg,0,sizeof(osc_run_msg_def));		
		/* set default vol offset */
		runmsg->vol_offset_scale[0] = 400 / 2;//middle
		runmsg->vol_offset_scale[1] = 400 / 2 + 50;//middle
		/* set vol scale */
		runmsg->vol_scale_ch[0] = 6;//2V div
		runmsg->vol_scale_ch[1] = 6;//2V div
		/* set trig scale */
		runmsg->trig_vol_level_ch[0] = 400 / 2 - 50 ;//middle
		runmsg->trig_vol_level_ch[1] = 400 / 2 + 50;//middle
		/* time */
		runmsg->time_scale = 5;
		osc_param_sys_set(&runmsg->sys_menu_set,1,7);
		osc_param_sys_set(&runmsg->sys_menu_set,1,10);
		/* trig */
//		runmsg->trig_source = 1;
		/* set default measure item */
		runmsg->measure_item[0] = (1<<0)|(1<<2);
		runmsg->measure_item[1] = (1<<0)|(1<<2);
		/* set */
		const unsigned short cal_buffer0[14] = {6432,5982,5528,5079,4627,4175,3728,6437,5987,5534,5085,4632,4180,3735};
		/* default */
		memcpy(runmsg->pos_zero_pwm_ch1,cal_buffer0,sizeof(runmsg->pos_zero_pwm_ch1));
		memcpy(runmsg->pos_zero_pwm_ch2,cal_buffer0,sizeof(runmsg->pos_zero_pwm_ch2));
		/* backlight */
		runmsg->back_light_per = 60;
		/* set id */
		runmsg->check = osc_param_check((unsigned char *)runmsg,sizeof(osc_m_tmp)- 1);	
		/* copy data */
		memcpy(&osc_m_tmp,runmsg,sizeof(osc_m_tmp));		
		/* save data */
		osc_flash_eeprom_write(&osc_m_tmp);
		/* end */		
	}
	/* return */
	return FS_OK;
}
/* thread */
void osc_param_thread(void)
{
	static unsigned int pt0 = 0;
	/* check */
	if( hal_sys_time_us() - pt0 < 2 * 1000 * 1000 )
	{
		return;
	}
	/* up */
	pt0 = hal_sys_time_us();
	/* check idle */
	if( touch_idle_cnt < 150 )
	{
		return;
	}
	/* check */
	if( cal_step_start )
	{
		return;
	}
	/* clear */
	touch_idle_cnt = 0;
	/* tesf */
	unsigned char * tmp = (unsigned char *)&osc_m_tmp;
	unsigned char * rum = (unsigned char *)runmsg;
	/* check */
	if( memcmp(tmp,rum,sizeof(osc_m_tmp)) != 0 )
	{
		/* diff */
		memcpy(tmp,rum,sizeof(osc_m_tmp));
		/* set check xor */
		runmsg->check = osc_param_check(tmp,sizeof(osc_m_tmp)- 1);
		osc_m_tmp.check = runmsg->check;
		/* save */
		osc_flash_eeprom_write(&osc_m_tmp);
	}
}
/* param save */
void osc_param_save_noload(void)
{
	/* tesf */
	unsigned char * tmp = (unsigned char *)&osc_m_tmp;
	unsigned char * rum = (unsigned char *)runmsg;
	/* check */
	if( memcmp(tmp,rum,sizeof(osc_m_tmp)) != 0 )
	{
		/* diff */
		memcpy(tmp,rum,sizeof(osc_m_tmp));
		/* set check xor */
		runmsg->check = osc_param_check(tmp,sizeof(osc_m_tmp)- 1);
		osc_m_tmp.check = runmsg->check;
		/* save */
		osc_flash_eeprom_write(&osc_m_tmp);
	}	
}
/* restor the default param */
void osc_reset_param(void)
{
	/* need erase flash */
	HAL_FLASH_Unlock();
#if OSC_STM32H750	
	/* set */
	FLASH_Erase_Sector(7,FLASH_BANK_1,FLASH_VOLTAGE_RANGE_3);	
#else
	for( int i = 0 ; i < 16 ; i ++ )
	{
		FLASH_Erase_Sector(7*16+i,FLASH_BANK_1,0x20);	
	}
#endif	
	/* reset */
	NVIC_SystemReset();		
}





















