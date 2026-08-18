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
#include "osc.h"
#include "gui.h"
#include "fos.h"
/* five channels */
const chn_manage_def chn_m[] = 
{
	{
		.BG_0 = COLOR_CH1_BG_0,
		.BG_1 = COLOR_CH1_BG_1,
		.BG_F = COLOR_CH1_BG_F,
		.GR_0 = COLOR_CH1_GR_0,
		.GR_1 = COLOR_CH1_GR_1,
		.GR_F = COLOR_CH1_GR_F,
	},
	{
		.BG_0 = COLOR_CH2_BG_0,
		.BG_1 = COLOR_CH2_BG_1,
		.BG_F = COLOR_CH2_BG_F,
		.GR_0 = COLOR_CH2_GR_0,
		.GR_1 = COLOR_CH2_GR_1,
		.GR_F = COLOR_CH2_GR_F,
	},	
	{
		.BG_0 = COLOR_MATH0_BG_0,
		.BG_1 = COLOR_MATH0_BG_1,
		.BG_F = COLOR_MATH0_BG_F,
		.GR_0 = COLOR_MATH0_GR_0,
		.GR_1 = COLOR_MATH0_GR_1,
		.GR_F = COLOR_MATH0_GR_F,
	},
	{
		.BG_0 = COLOR_MATH1_BG_0,
		.BG_1 = COLOR_MATH1_BG_1,
		.BG_F = COLOR_MATH1_BG_F,
		.GR_0 = COLOR_MATH1_GR_0,
		.GR_1 = COLOR_MATH1_GR_1,
		.GR_F = COLOR_MATH1_GR_F,
	},	
	{
		.BG_0 = COLOR_MATH2_BG_0,
		.BG_1 = COLOR_MATH2_BG_1,
		.BG_F = COLOR_MATH2_BG_F,
		.GR_0 = COLOR_MATH2_GR_0,
		.GR_1 = COLOR_MATH2_GR_1,
		.GR_F = COLOR_MATH2_GR_F,
	},	
};
/* osc draw lines */
void osc_draw_lines(gui_dev_def * dev,unsigned short x1, unsigned short y1, unsigned short x2, unsigned short y2,unsigned short mode,unsigned short chn,unsigned short index)
{
	/* defines */
	int xerr = 0 , yerr = 0 , delta_x , delta_y , distance; 
	int incx,incy,uRow,uCol; 
	/* dir */
	delta_x = x2 - x1;
	delta_y = y2 - y1; 
	uRow = x1; 
	uCol = y1; 
	/* dir */
	if( delta_x > 0 ) 
	{ 
		incx = 1; 
	}
	else if( delta_x == 0 )
	{
		incx = 0;
	}
	else
	{
		incx = -1 ; 
		delta_x = -delta_x;
	}
	/* dir y delta */
	if( delta_y > 0 ) 
	{ 
		incy = 1; 
	}
	else if( delta_y ==0 )
	{
		incy = 0;
	}
	else
	{
		incy = -1 ; 
		delta_y = -delta_y;
	}
	/* distance */ 
	if( delta_x > delta_y )
	{ 
		distance = delta_x;
	}
	else 
	{
		distance = delta_y; 
	}
	/* get chn */
	const chn_manage_def * chn_d = &chn_m[chn];
  /* draw points */
	for( int t = 0 ; t <= distance + 1 ; t++ ) 
	{
		/* draw point or clear point */	 
		if( mode == 0 ) /* draw */
		{
			/* get point */
			unsigned char piox = dev->read_point(uRow,uCol);
			/* chn */
			if( piox == COLOR_GRID_POINT ) // chn1
			{
				dev->set_noload_point(uRow,uCol,index ? chn_d->GR_1 : chn_d->GR_0);
			}
			else if( piox == COLOR_GRID_AREA_BG )
			{
				dev->set_noload_point(uRow,uCol,index ? chn_d->BG_1 : chn_d->BG_0);
			}
			else if( piox == chn_d->GR_0 && index == 1 )
			{
				dev->set_noload_point(uRow,uCol,chn_d->GR_F);
			}
			else if( piox == chn_d->GR_1 && index == 0 )
			{
				dev->set_noload_point(uRow,uCol,chn_d->GR_F);		 
			}
			else if( piox == chn_d->BG_0 && index == 1 )
			{
				dev->set_noload_point(uRow,uCol,chn_d->BG_F);
			}
			else if( piox == chn_d->BG_1 && index == 0 )
			{
				dev->set_noload_point(uRow,uCol,chn_d->BG_F);	 
			}		
			else
			{
				/* other point .error */
				piox = 0;
			}
		}
		else
		{
			/* clear */
			unsigned char piox = dev->read_point(uRow,uCol);
			/* chn */
			if( piox == chn_d->BG_0 && index == 0 )
			{	
				dev->set_noload_point(uRow,uCol,COLOR_GRID_AREA_BG);
			}
			else if( piox == chn_d->BG_1 && index == 1 )			 
			{
				dev->set_noload_point(uRow,uCol,COLOR_GRID_AREA_BG);
			}		 
			else if( piox == chn_d->GR_0 && index == 0 )			 
			{
				dev->set_noload_point(uRow,uCol,COLOR_GRID_POINT);
			}
			else if( piox == chn_d->GR_1 && index == 1 )			 
			{
				dev->set_noload_point(uRow,uCol,COLOR_GRID_POINT);
			}		 
			else if( piox == chn_d->GR_F )		
			{
				dev->set_noload_point(uRow,uCol,index ? chn_d->GR_0 : chn_d->GR_1);
			}
			else if( piox == chn_d->BG_F )		
			{
				dev->set_noload_point(uRow,uCol,index ? chn_d->BG_0 : chn_d->BG_1);
			}
			else
			{
				/* other point */
				piox = 0;
			}
		}
		/* inc */
		xerr += delta_x ; 
		yerr += delta_y ;
		/* next line */  
		if( xerr > distance ) 
		{ 
			xerr -= distance; 
			uRow += incx; 
		} 
		/* next */
		if( yerr > distance ) 
		{ 
			yerr -= distance; 
			uCol += incy; 
		} 
	}
}
/* osc create and clear lines group */
void osc_create_lines(gui_dev_def * dev,unsigned short * line_d,unsigned char mode,unsigned short index,unsigned char chn ,unsigned short zm)
{
	/* get msg area */
	draw_area_def *  msg_area = get_draw_area_msg();
	/* skip some points */
	int it = 0;
	/* get it */
	if( zm == 2 )
	{
		it = 175;
	}
	else if(  zm == 5 )
	{
		it = 280;
	}
	else if(  zm == 10 )
	{
		it = 315;
	}
	else
	{
		
	}
	/* draws */
	for( int i = 0 ; i < msg_area->pixel_horizontal * msg_area->num_horizontal - 1 ; i += zm )
	{
	/* create lines */
		osc_draw_lines(dev,msg_area->start_pos_x + i,msg_area->start_pos_y + line_d[it] , msg_area->start_pos_x + i + zm ,msg_area->start_pos_y + line_d[it+1],mode,chn,index);
		/* increm */
		it ++;
	}
}
/* void clear area */
void osc_clear_area(gui_dev_def * dev,unsigned short start_x,unsigned short start_y)
{
	/* get msg area */
	draw_area_def *  msg_area = get_draw_area_msg();
	
	/* area */
	for( int j = msg_area->start_pos_y ; j < msg_area->stop_pos_y ; j ++ )
	{
		/* read */
		unsigned char piox = dev->read_point(start_x,j);
		/* for */
		for( int i = 0 ; i < 5 ; i ++ )
		{
			/* get chn */
			const chn_manage_def * chn_d = &chn_m[i];
			/* chn */
			if( piox == chn_d->BG_0 )
			{	
				dev->set_noload_point(start_x,j,COLOR_GRID_AREA_BG);
			} 
			else if( piox == chn_d->BG_1 )
			{	
				dev->set_noload_point(start_x,j,COLOR_GRID_AREA_BG);
			} 		
			else if( piox == chn_d->BG_F )
			{	
				dev->set_noload_point(start_x,j,COLOR_GRID_AREA_BG);
			}			
			else if( piox == chn_d->GR_0 )			 
			{
				dev->set_noload_point(start_x,j,COLOR_GRID_POINT);
			}
			else if( piox == chn_d->GR_1 )			 
			{
				dev->set_noload_point(start_x,j,COLOR_GRID_POINT);
			}
			else if( piox == chn_d->GR_F )			 
			{
				dev->set_noload_point(start_x,j,COLOR_GRID_POINT);
			}			
			else
			{
				
			}
		}
  }
}
/* void */
void osc_clear_screen(gui_dev_def * dev)
{
	/* check */
	if( dev == 0 )
	{
		return;
	}
	/* get msg area */
	draw_area_def *  msg_area = get_draw_area_msg();
	/* for */
	for( int i = msg_area->start_pos_x ; i < msg_area->stop_pos_x ; i ++ )
	{
		osc_clear_area(dev,i,0);
	}
}
/* osc create points */
void osc_create_points_xy(gui_dev_def * dev,unsigned short * x_p,unsigned short *y_p , unsigned char mode,unsigned char index,unsigned char chn)
{
	/* get chn */
	const chn_manage_def * chn_d = &chn_m[chn];
  /* draw points */
	for( int t = 0 ; t < 400 ; t++ ) 
	{
		/* draw point or clear point */	 
		if( mode == 0 ) /* draw */
		{
			/* get point */
			unsigned char piox = dev->read_point(x_p[t],y_p[t]);
			/* chn */
			if( piox == COLOR_GRID_POINT ) // chn1
			{
				dev->set_noload_point(x_p[t],y_p[t],index ? chn_d->GR_1 : chn_d->GR_0);
			}
			else if( piox == COLOR_GRID_AREA_BG )
			{
				dev->set_noload_point(x_p[t],y_p[t],index ? chn_d->BG_1 : chn_d->BG_0);
			}
			else if( piox == chn_d->GR_0 && index == 1 )
			{
				dev->set_noload_point(x_p[t],y_p[t],chn_d->GR_F);
			}
			else if( piox == chn_d->GR_1 && index == 0 )
			{
				dev->set_noload_point(x_p[t],y_p[t],chn_d->GR_F);		 
			}
			else if( piox == chn_d->BG_0 && index == 1 )
			{
				dev->set_noload_point(x_p[t],y_p[t],chn_d->BG_F);
			}
			else if( piox == chn_d->BG_1 && index == 0 )
			{
				dev->set_noload_point(x_p[t],y_p[t],chn_d->BG_F);	 
			}		
			else
			{
				/* other point .error */
				piox = 0;
			}
		}
		else
		{
			/* clear */
			unsigned char piox = dev->read_point(x_p[t],y_p[t]);
			/* chn */
			if( piox == chn_d->BG_0 && index == 0 )
			{	
				dev->set_noload_point(x_p[t],y_p[t],COLOR_GRID_AREA_BG);
			}
			else if( piox == chn_d->BG_1 && index == 1 )			 
			{
				dev->set_noload_point(x_p[t],y_p[t],COLOR_GRID_AREA_BG);
			}		 
			else if( piox == chn_d->GR_0 && index == 0 )			 
			{
				dev->set_noload_point(x_p[t],y_p[t],COLOR_GRID_POINT);
			}
			else if( piox == chn_d->GR_1 && index == 1 )			 
			{
				dev->set_noload_point(x_p[t],y_p[t],COLOR_GRID_POINT);
			}		 
			else if( piox == chn_d->GR_F )		
			{
				dev->set_noload_point(x_p[t],y_p[t],index ? chn_d->GR_0 : chn_d->GR_1);
			}
			else if( piox == chn_d->BG_F )		
			{
				dev->set_noload_point(x_p[t],y_p[t],index ? chn_d->BG_0 : chn_d->BG_1);
			}
			else
			{
				/* other point */
				piox = 0;
			}
		}
	}
}












