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
#include "osc_ui.h"
#include "osc_menu.h"
#include "osc_api.h"
#include "string.h"
#include "hal_exit.h"
#include "osc_cfg.h"
#include "hal_usart.h"
#include "osc_calibrate.h"
#include "osc_param.h"
#include "usbh_app.h"
/* Private includes ----------------------------------------------------------*/
//FOS_TSK_REGISTER(osc_menu_thread,PRIORITY_2,5);/* run as 10ms */
/* create cfg task gui detecter task run as 100 ms */
//FOS_TSK_REGISTER(osc_menu_hide_thread,PRIORITY_4,1000);
/* static link */
static osc_run_msg_def osc_run_msg;
/* LONG press cnt */
#define LONG_PRESS_LIMIT (12)
/* function */
static unsigned char ctrl_menu_sta = 1;
/* single thread */
void osc_single_thread(void)
{
}
/* */
/* check */
void osc_ctrl_change(void)
{
	/* */
	if( ctrl_menu_sta )
	{
		osc_ui_menu_show(0);
		osc_ui_menu1_show(1);
		/* show up */
		osc_ui_vol_scale(2,0);
		osc_ui_vol_scale(3,0);		
	}
	else
	{
		osc_ui_menu1_show(0);	
		osc_ui_menu_show(1);
	}
	/* change */
	ctrl_menu_sta ^= 1;	
}
/* return sta */
unsigned char osc_ctrl_menu_sta(void)
{
	return ctrl_menu_sta;
}
/* return ksc msg */
osc_run_msg_def * get_run_msg(void)
{
  return &osc_run_msg;
}
 


























