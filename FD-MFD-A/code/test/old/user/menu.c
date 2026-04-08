#include "menu.h"
#include "key.h"
extern int fputc(int ch, FILE* file);

PAGE page;
CURSOR_MAIN cursor_main;
CURSOR_MEASURE_COIL cursor_measure_coil;
CURSOR_MEASURE_COIL_CURRENT cursor_measure_coil_current;
CURSOR_SELECT_INPUTMODE cursor_select_inputmode;
CURSOR_GENERATE_COORDINATES cursor_generate_coordinates;	
CURSOR_MEASUER_START cursor_measuer_start;
CALIBO_STATE calibo_state=NONE;
_Bool input_mode;//0ÊÖ¶¯ 1×Ô¶¯
_Bool input_judge;//0´íÎó 1ÕýÈ·
_Bool output_flag;//1³É¹¦ 0Ê§°Ü

float x0,y0,z0,x1=1,y1=1,z1=1;
uint8_t s1,s2,s3,s4,e1,e2,e3,e4,u1,u2,u3,u4,p1,p2,p3,p4,a1,a2,a3,a4;
uint8_t beishu=10;

unsigned int group_num,sheet_num,cursor_group_num,cursor_sheet_num;

void up_button()
{
	switch(page)
	{
		default:break;
		case MAIN://Ö÷Ò³Ãæ ÉÏ
			switch(cursor_main)
			{
				case CALIBO:
					printf("calibo.bco=50779\xff\xff\xff");
					printf("data_query.bco=61277\xff\xff\xff");
					printf("data_out.bco=61277\xff\xff\xff");
					cursor_main=DATA;
				break;
				
				case MEA_GND:
					printf("calibo.bco=61277\xff\xff\xff");
					printf("mea_gnd.bco=50779\xff\xff\xff");
					cursor_main=CALIBO;
				break;
				
				case MEA_COIL:
					printf("mea_gnd.bco=61277\xff\xff\xff");
					printf("mea_coil1.bco=50779\xff\xff\xff");
					printf("mea_coil2.bco=50779\xff\xff\xff");
					cursor_main=MEA_GND;
				break;
				
				case DATA:
					printf("data_query.bco=50779\xff\xff\xff");
					printf("data_out.bco=50779\xff\xff\xff");
					printf("mea_coil1.bco=61277\xff\xff\xff");
					printf("mea_coil2.bco=61277\xff\xff\xff");
					cursor_main=MEA_COIL;
				break;
				default:break;
			}
			
		break;
		
		case XY_CALIBO:
			
		break;
		
		case Z_CALIBO:
			
		break;
		
		
		case PLACE:
			
		break;
		
		case XY_CALIBO_1:
			
		break;
		
		case Z_CALIBO_1:
			
		break;
		
		case CALIBO_SUCCESS://Ð£×¼³É¹¦ ÉÏ
			printf("page Ö÷Ò³Ãæ\xff\xff\xff");
			page=MAIN;
			cursor_main=CALIBO;
		break;
		
		case MEASURE_GROUND:
			
		break;
		
		case AUTO_SETZERO:
			
		break;
		
		case MEASURE_COIL://ÏßÈ¦´Å³¡²âÁ¿ ÉÏ
			if(cursor_measure_coil==DATA_RECORD)
			{
				cursor_measure_coil=SWITCH_MODE;
				printf("data_record.bco=50779\xff\xff\xff");
				printf("switch_mode.bco=61277\xff\xff\xff");
			}
			else
			{
				cursor_measure_coil=DATA_RECORD;
				printf("data_record.bco=61277\xff\xff\xff");
				printf("switch_mode.bco=50779\xff\xff\xff");
			}
		break;
		
		case SELECT_INPUTMODE://Ñ¡ÔñÊäÈë·½Ê½ ÉÏ
				if(cursor_select_inputmode==MANUAL)
				{
					cursor_select_inputmode=AUTO;
					printf("auto1.bco=61277\xff\xff\xff");
					printf("auto2.bco=61277\xff\xff\xff");
					printf("manual1.bco=50779\xff\xff\xff");
					printf("manual2.bco=50779\xff\xff\xff");
				}
				else
				{
					cursor_select_inputmode=MANUAL;
					printf("auto1.bco=50779\xff\xff\xff");
					printf("auto2.bco=50779\xff\xff\xff");
					printf("manual1.bco=61277\xff\xff\xff");
					printf("manual2.bco=61277\xff\xff\xff");
				}
		break;
		
		case GENERATE_COORDINATES://×ø±êÉú³É ÉÏ
			switch(cursor_generate_coordinates)
			{
				case START1:
					printf("s1.bco=50779\xff\xff\xff");
					printf("u4.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=STEP4;
					break;
				case START2:
					printf("s2.bco=50779\xff\xff\xff");
					printf("s1.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=START1;
				break;
				case START3:
					printf("s3.bco=50779\xff\xff\xff");
					printf("s2.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=START2;
					break;
				case START4:
					printf("s4.bco=50779\xff\xff\xff");
					printf("s3.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=START3;
					break;
				case END1:
					printf("e1.bco=50779\xff\xff\xff");
					printf("s4.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=START4;
					break;
				case END2:
					printf("e2.bco=50779\xff\xff\xff");
					printf("e1.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=END1;
				break;
				case END3:
					printf("e3.bco=50779\xff\xff\xff");
					printf("e2.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=END2;
					break;
				case END4:
					printf("e4.bco=50779\xff\xff\xff");
					printf("e3.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=END3;
					break;
				case STEP1:
					printf("u1.bco=50779\xff\xff\xff");
					printf("e4.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=END4;
					break;
				case STEP2:
					printf("u2.bco=50779\xff\xff\xff");
					printf("u1.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=STEP1;
				break;
				case STEP3:
					printf("u3.bco=50779\xff\xff\xff");
					printf("u2.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=STEP2;
				break;
				case STEP4:
					printf("u4.bco=50779\xff\xff\xff");
					printf("u3.bco=61277\xff\xff\xff");
					cursor_generate_coordinates=STEP3;
				break;
			}
		break;
		
		case MEASUER_START://ÊÖ¶¯²É¼¯Ò³ ÉÏ
			switch(cursor_measuer_start)
			{
				case P1:
					printf("p1.bco=50779\xff\xff\xff");
					printf("p4.bco=61277\xff\xff\xff");
					cursor_measuer_start=P4;
				break;
				case P2:
					printf("p2.bco=50779\xff\xff\xff");
					printf("p1.bco=61277\xff\xff\xff");
					cursor_measuer_start=P1;
				break;
				case P3:
					printf("p3.bco=50779\xff\xff\xff");
					printf("p2.bco=61277\xff\xff\xff");
					cursor_measuer_start=P2;
				break;
				case P4:
					printf("p4.bco=50779\xff\xff\xff");
					printf("p3.bco=61277\xff\xff\xff");
					cursor_measuer_start=P3;
				break;
			}
		break;
		
		case MEASUER_START_1:
			
		break;
		
		case DATA_OUTPUT://Ñ¡Ôñ²é¿´×é ÉÏ
			
			printf("t%d.bco=50779\xff\xff\xff",cursor_group_num%16);
			if(cursor_group_num!=0) cursor_group_num--;
			else cursor_group_num=15;
			printf("t%d.bco=61277\xff\xff\xff",cursor_group_num);
			
		break;
		
		case DATA_SHEET:
			if(sheet_now!=0)sheet_now--;
			data_sheet();
		break;
		
		case OUTPUTING:
			
		break;
		
		case OUTPUT_COMPLETE://µ¼³öÍê³É ÉÏ
			printf("page Êý¾Ý²éÑ¯ºÍµ¼³ö\xff\xff\xff");
			page=DATA_OUTPUT;
		break;
	}
}

void confirm_button()
{
	switch(page)
	{
		default:break;
		case MAIN://Ö÷Ò³ È·¶¨
			switch(cursor_main)
			{
				case CALIBO:
					printf("page ÏòÉÏ¹Ì¶¨\xff\xff\xff");
					page=PLACE_UP;
					
				break;
					
				case MEA_GND:
					printf("page µØ´Å³¡²âÁ¿\xff\xff\xff");
					page=MEASURE_GROUND;
				break;
				
				case MEA_COIL:
					printf("page ×Ô¶¯ÖÃÁã\xff\xff\xff");
					page=AUTO_SETZERO;
				break;
				
				case DATA:
					printf("page Êý¾Ý²éÑ¯ºÍµ¼³ö\xff\xff\xff");
					page=DATA_OUTPUT;
					cursor_sheet_num=0;
					cursor_group_num=0;
				break;
				case CAL:
					Flash_writeK();
				//	HAL_Delay(500);
				//	printf("vis k,0\xff\xff\xff");
					cursor_main=CALIBO;
				break;
				default:break;
			}
			
		break;
		//confirm
		case PLACE_UP:
			printf("page Ð£×¼XYÖáÁãµã\xff\xff\xff");
			page=XY_CALIBO;
			calibo_state=X0Y0;
			break;
		case XY_CALIBO:
			printf("page ÏòÓÒ¹Ì¶¨\xff\xff\xff");
			page=PLACE_RIGHT;
			break;
		break;
		case PLACE_RIGHT:
			printf("page Ð£×¼ZÖáÁãµã\xff\xff\xff");
			page=Z_CALIBO;
			calibo_state=Z0;
			break;
		case Z_CALIBO:
			page=PLACE;
			printf("page ·ÅÖÃÆ÷¼þ\xff\xff\xff");
			calibo_state=NONE;
		break;
		
		case PLACE:
			page=XY_CALIBO_1;
			printf("page Ð£×¼XYÖáÏµÊý\xff\xff\xff");
			calibo_state=X1Y1;
		break;
		
		case XY_CALIBO_1:
			page=PLACE_RIGHT_1;
			printf("page ÏòÓÒ¹Ì¶¨\xff\xff\xff");
		break;
		
		case PLACE_RIGHT_1:
			page=Z_CALIBO_1;
			printf("page Ð£×¼ZÖáÏµÊý\xff\xff\xff");
			calibo_state=Z1;
			break;
		case Z_CALIBO_1:
			page=CALIBO_SUCCESS;
			printf("page Ð£×¼Íê³É\xff\xff\xff");
			calibo_state=NONE;
		break;
		
		case CALIBO_SUCCESS:
			printf("page Ö÷Ò³Ãæ\xff\xff\xff");
			page=MAIN;
			cursor_main=CALIBO;
		break;
		//confirm
		case MEASURE_GROUND:
			
		break;
		
		case AUTO_SETZERO:
			printf("page ÏßÈ¦´Å³¡²âÁ¿\xff\xff\xff");
			Current=100;
			page=MEASURE_COIL;
			cursor_measure_coil=DATA_RECORD;
			cursor_measure_coil_current=A1;
		break;
		
		case MEASURE_COIL:
			if(cursor_measure_coil==SWITCH_MODE)
			{
				printf("page ÊäÈë·½Ê½Ñ¡Ôñ\xff\xff\xff");
				page=SELECT_INPUTMODE;
				cursor_select_inputmode=MANUAL;
				return;
			}
			if(input_mode==0)
			{
				printf("page µÚXX×éÊý¾Ý²É¼¯\xff\xff\xff");
				page=MEASUER_START;
				cursor_measuer_start=P1;
				group_now=group_num;
				number_now=0;
			}
			else
			{
				printf("page ¸¨ÖúÉú³É×ø±ê\xff\xff\xff");
				group_now=group_num;
				number_now=0;
				page=GENERATE_COORDINATES;
				cursor_generate_coordinates=START1;
				printf("vis t17,0\xff\xff\xff");
				printf("vis t18,0\xff\xff\xff");
			}
		break;
		//confirm
		case SELECT_INPUTMODE:
			if(cursor_select_inputmode==MANUAL)
			{
				input_mode=0;
				printf("page ÏßÈ¦´Å³¡²âÁ¿\xff\xff\xff");
				page=MEASURE_COIL;
				cursor_measure_coil=DATA_RECORD;
				cursor_measure_coil_current=A1;
			}
			else
			{
				input_mode=1;
				printf("page ÏßÈ¦´Å³¡²âÁ¿\xff\xff\xff");
				page=MEASURE_COIL;
				cursor_measure_coil=DATA_RECORD;
				cursor_measure_coil_current=A1;
			}
		break;
		//confirm
		case GENERATE_COORDINATES:
			gener_cordinate();
			if(input_judge==0)
			{
				printf("vis t17,1\xff\xff\xff");
				printf("vis t18,1\xff\xff\xff");
				break;
			}
			else
			{
				page=MEASUER_START_1;
				printf("page ¸¨ÖúÊý¾Ý²É¼¯\xff\xff\xff");
			}
		break;
		
		case MEASUER_START_1:
			table_length[group_now]=number_now;
			position=test_position[number_now];
			record_data();
			if(number_now<position_num-1) number_now++;
			else
			{
				page=MEASURE_COIL;
				printf("page ÏßÈ¦´Å³¡²âÁ¿\xff\xff\xff");
				if(table_length[group_now]!=0) group_num++;
			}
		break;
		
		case MEASUER_START:
			table_length[group_now]=number_now;
			position=pos_measure_start/100;
			record_data();
			if(number_now<MAX_NUMBER-1) number_now++;
			else number_now=0;
		break;
		
		case DATA_OUTPUT:
			printf("page Êý¾Ý±í¸ñ\xff\xff\xff");
			page=DATA_SHEET;
			sheet_now=0;
			sheet_length=table_length[cursor_group_num]/6;
			data_sheet();
		break;
		//confirm
		case DATA_SHEET:
			printf("page µ¼³öÖÐ\xff\xff\xff");
			page=OUTPUTING;
			printf("t2.txt=\"initing..\"\xff\xff\xff");
			ch376_init();
			printf("t2.txt=\"writing..\"\xff\xff\xff");
			printf("j0.val=50\xff\xff\xff");
			ch376_writetest();
			printf("j0.val=100\xff\xff\xff");
			printf("page µ¼³öÍê³É\xff\xff\xff");
			page=OUTPUT_COMPLETE;
			if(output_flag) printf("t1.txt=\"µ¼³öÍê³É!\"\xff\xff\xff");
			else printf("t1.txt=\"µ¼³öÊ§°Ü!\"\xff\xff\xff");
		break;
		
		case OUTPUTING:
			
		break;
		
		case OUTPUT_COMPLETE:
			printf("page Êý¾Ý²éÑ¯ºÍµ¼³ö\xff\xff\xff");
			cursor_group_num=0;
			page=DATA_OUTPUT;
		break;
	}
}

void down_button()
{
	switch(page)
	{
		default:break;
		case MAIN:
			switch(cursor_main)
			{
				case CALIBO:
					printf("calibo.bco=50779\xff\xff\xff");
					printf("mea_gnd.bco=61277\xff\xff\xff");
					cursor_main=MEA_GND;
				break;
				
				case MEA_GND:
					printf("mea_gnd.bco=50779\xff\xff\xff");
					printf("mea_coil1.bco=61277\xff\xff\xff");
					printf("mea_coil2.bco=61277\xff\xff\xff");
				cursor_main=MEA_COIL;
				break;
				
				case MEA_COIL:
					printf("mea_coil1.bco=50779\xff\xff\xff");
					printf("mea_coil2.bco=50779\xff\xff\xff");
					printf("data_query.bco=61277\xff\xff\xff");
					printf("data_out.bco=61277\xff\xff\xff");
					cursor_main=DATA;
				break;
				
				case DATA:
					printf("data_query.bco=50779\xff\xff\xff");
					printf("data_out.bco=50779\xff\xff\xff");
					printf("calibo.bco=61277\xff\xff\xff");
					cursor_main=CALIBO;
				break;
				default:break;
			}
			
		break;
		//down
		case XY_CALIBO:
			
		break;
		
		case Z_CALIBO:
			
		break;
		
		case PLACE:
			
		break;
		
		case XY_CALIBO_1:
			
		break;
		
		case Z_CALIBO_1:
			
		break;
		//down
		case CALIBO_SUCCESS:
			printf("page Ö÷Ò³Ãæ\xff\xff\xff");
			page=MAIN;
			cursor_main=CALIBO;
		break;
		
		case MEASURE_GROUND:
			
		break;
		
		case AUTO_SETZERO:
			
		break;
		
		case MEASURE_COIL:
			if(cursor_measure_coil==DATA_RECORD)
			{
				cursor_measure_coil=SWITCH_MODE;
				printf("data_record.bco=50779\xff\xff\xff");
				printf("switch_mode.bco=61277\xff\xff\xff");
			}
			else
			{
				cursor_measure_coil=DATA_RECORD;
				printf("data_record.bco=61277\xff\xff\xff");
				printf("switch_mode.bco=50779\xff\xff\xff");
			}
		break;
		//down
		case SELECT_INPUTMODE:
			if(cursor_select_inputmode==MANUAL)
				{
					cursor_select_inputmode=AUTO;
					printf("auto1.bco=61277\xff\xff\xff");
					printf("auto2.bco=61277\xff\xff\xff");
					printf("manual1.bco=50779\xff\xff\xff");
					printf("manual2.bco=50779\xff\xff\xff");
				}
				else
				{
					cursor_select_inputmode=MANUAL;
					printf("auto1.bco=50779\xff\xff\xff");
					printf("auto2.bco=50779\xff\xff\xff");
					printf("manual1.bco=61277\xff\xff\xff");
					printf("manual2.bco=61277\xff\xff\xff");
				}
		break;
		//down
		case GENERATE_COORDINATES:	
			func_button();
		break;
		//down
		case MEASUER_START:
			func_button();
		break;
		
		case MEASUER_START_1:
			
		break;
		
		case DATA_OUTPUT:
			printf("t%d.bco=50779\xff\xff\xff",cursor_group_num);
			if(cursor_group_num<MAX_GROUP-1)cursor_group_num++;
			else cursor_group_num=0;
//			cursor_sheet_num=cursor_group_num/16;
//			for(int i=0;i<16;i++)
//			{
//				printf("t%d.txt=\"µÚ%d×é\"\xff\xff\xff",i,cursor_sheet_num*16+i);
//			}
			printf("t%d.bco=61277\xff\xff\xff",cursor_group_num);
		break;
		//down
		case DATA_SHEET:
			if(sheet_now!=sheet_length) sheet_now++;
			data_sheet();
		break;
		
		case OUTPUTING:
			
		break;
		
		case OUTPUT_COMPLETE:
			printf("page Êý¾Ý²éÑ¯ºÍµ¼³ö\xff\xff\xff");
			page=DATA_OUTPUT;
		break;
	}
}

void cancel_button()
{
	
	switch(page)
	{
		default:break;
		case MAIN:
			
		break;
		
		case PLACE_UP:
			page=MAIN;
			printf("page Ö÷Ò³Ãæ\xff\xff\xff");
			cursor_main=CALIBO;
			calibo_state=NONE;
		break;
//		
		case XY_CALIBO:
//			page=PLACE_UP;
//			printf("page ÏòÉÏ¹Ì¶¨\xff\xff\xff");
//				page=MAIN;
//				printf("page Ö÷Ò³Ãæ\xff\xff\xff");
//				cursor_main=CALIBO;
//				calibo_state=NONE;
		break;
//			
		case PLACE_RIGHT:
//			page=XY_CALIBO;
//			printf("page Ð£×¼XYÖáÁãµã\xff\xff\xff");
//				page=MAIN;
//				printf("page Ö÷Ò³Ãæ\xff\xff\xff");
//				cursor_main=CALIBO;
//				calibo_state=NONE;
//				calibo_state=X0Y0;
			break;
//		case Z_CALIBO:
//			page=PLACE_RIGHT;
//			printf("page ÏòÓÒ¹Ì¶¨\xff\xff\xff");
//				page=MAIN;
//				printf("page Ö÷Ò³Ãæ\xff\xff\xff");
//				cursor_main=CALIBO;
//				calibo_state=NONE;
//		break;
//		
//		case PLACE:
//			printf("page Ð£×¼ZÖáÁãµã\xff\xff\xff");
//			page=Z_CALIBO;
//			calibo_state=Z0;
//		break;
//		
//		case XY_CALIBO_1:
//			printf("page ·ÅÖÃÆ÷¼þ\xff\xff\xff");
//			page=PLACE;
//			calibo_state=NONE;
//		break;
//		case PLACE_RIGHT_1:
//			printf("page Ð£×¼XYÖáÏµÊý\xff\xff\xffý");
//			page=XY_CALIBO_1;
//			calibo_state=X1Y1;
//		break;
//		case Z_CALIBO_1:
//			page=PLACE_RIGHT_1;
//			printf("page ÏòÓÒ¹Ì¶¨\xff\xff\xff");
//		break;
		//cancel
		case CALIBO_SUCCESS:
			printf("page Ö÷Ò³Ãæ\xff\xff\xff");
			page=MAIN;
			cursor_main=CALIBO;
		break;
		
		case MEASURE_GROUND:
			printf("page Ö÷Ò³Ãæ\xff\xff\xff");
			page=MAIN;
			cursor_main=CALIBO;
		break;
		
		case AUTO_SETZERO:
			printf("page Ö÷Ò³Ãæ\xff\xff\xff");
			page=MAIN;
			cursor_main=CALIBO;
		break;
		
		case MEASURE_COIL:
			printf("page Ö÷Ò³Ãæ\xff\xff\xff");
			page=MAIN;
			cursor_main=CALIBO;
		break;
		
		case SELECT_INPUTMODE:
			printf("page ÏßÈ¦´Å³¡²âÁ¿\xff\xff\xff");
			page=MEASURE_COIL;
		break;
		//cancel
		case GENERATE_COORDINATES:
			page=MEASURE_COIL;
			printf("page ÏßÈ¦´Å³¡²âÁ¿\xff\xff\xff");
		break;
		
		case MEASUER_START:
			page=MEASURE_COIL;
			printf("page ÏßÈ¦´Å³¡²âÁ¿\xff\xff\xff");
			if(table_length[group_now]!=0) group_num++;
		break;
		
		case MEASUER_START_1:
			page=MEASURE_COIL;
			printf("page ÏßÈ¦´Å³¡²âÁ¿\xff\xff\xff");
			if(table_length[group_now]!=0) group_num++;
		break;
		
		case DATA_OUTPUT:
			printf("page Ö÷Ò³Ãæ\xff\xff\xff");
			cursor_main=CALIBO;
			page=MAIN;
		break;
		//cancel
		case DATA_SHEET:
			printf("page Êý¾Ý²éÑ¯ºÍµ¼³ö\xff\xff\xff");
			page=DATA_OUTPUT;
			cursor_group_num=0;
		break;
		
		case OUTPUTING:
			
		break;
		
		case OUTPUT_COMPLETE:
			page=DATA_OUTPUT;
			printf("page Êý¾Ý²éÑ¯ºÍµ¼³ö\xff\xff\xff");
		break;
	}
}

void func_button()
{	
	if(page==MAIN)
	{
		if(flag_10s==1)
		{
			flag_10s=0;
			printf("vis k,1\xff\xff\xff");
			cursor_main=CAL;
		}
	}
	else if(page==MEASURE_COIL)
	{
		if(beishu==1)
		{beishu=10;printf("move p0,80,277,80,277,0,0\xff\xff\xff");}
		else if(beishu==10){beishu=100;printf("move p0,59,277,59,277,0,0\xff\xff\xff");}
		else if(beishu==100){beishu=1;printf("move p0,111,277,111,277,0,0\xff\xff\xff");}
	}
	else if(page==GENERATE_COORDINATES) 
	{
		switch(cursor_generate_coordinates)
		{
			case START1:
				printf("s1.bco=50779\xff\xff\xff");
				printf("s2.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=START2;
				break;
			case START2:
				printf("s2.bco=50779\xff\xff\xff");
				printf("s3.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=START3;
			break;
			case START3:
				printf("s3.bco=50779\xff\xff\xff");
				printf("s4.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=START4;
				break;
			case START4:
				printf("s4.bco=50779\xff\xff\xff");
				printf("e1.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=END1;
				break;
			case END1:
				printf("e1.bco=50779\xff\xff\xff");
				printf("e2.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=END2;
				break;
			case END2:
				printf("e2.bco=50779\xff\xff\xff");
				printf("e3.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=END3;
			break;
			case END3:
				printf("e3.bco=50779\xff\xff\xff");
				printf("e4.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=END4;
				break;
			case END4:
				printf("e4.bco=50779\xff\xff\xff");
				printf("u1.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=STEP1;
				break;
			case STEP1:
				printf("u1.bco=50779\xff\xff\xff");
				printf("u2.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=STEP2;
				break;
			case STEP2:
				printf("u2.bco=50779\xff\xff\xff");
				printf("u3.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=STEP3;
			break;
			case STEP3:
				printf("u3.bco=50779\xff\xff\xff");
				printf("u4.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=STEP4;
			break;
			case STEP4:
				printf("u4.bco=50779\xff\xff\xff");
				printf("s1.bco=61277\xff\xff\xff");
				cursor_generate_coordinates=START1;
			break;
		}
	}
	else if(page==MEASUER_START)
	{
		switch(cursor_measuer_start)
		{
			case P1:
				printf("p1.bco=50779\xff\xff\xff");
				printf("p2.bco=61277\xff\xff\xff");
				cursor_measuer_start=P2;
			break;
			case P2:
				printf("p2.bco=50779\xff\xff\xff");
				printf("p3.bco=61277\xff\xff\xff");
				cursor_measuer_start=P3;
			break;
			case P3:
				printf("p3.bco=50779\xff\xff\xff");
				printf("p4.bco=61277\xff\xff\xff");
				cursor_measuer_start=P4;
			break;
			case P4:
				printf("p4.bco=50779\xff\xff\xff");
				printf("p1.bco=61277\xff\xff\xff");
				cursor_measuer_start=P1;
			break;
		}
	}
	else confirm_button();
}

void clockwise()
{
	switch(page)
	{
		case MEASURE_COIL:
			Current+=0.1*beishu;
			if(Current>MAX_CURRENT) Current=MAX_CURRENT;
			printf("a.txt=\"%.1f\"\xff\xff\xff",Current);
		break;
		case MAIN:if(cursor_main==CAL) k+=0.01;else down_button();break;
		case GENERATE_COORDINATES:
		switch(cursor_generate_coordinates)
		{
			case START1:
					start_position_int+=1000;
					break;
				case START2:
					start_position_int+=100;
					break;
				case START3:
					start_position_int+=10;
					break;
				case START4:
					start_position_int+=1;
					break;
				case END1:
					end_position_int+=1000;
					break;
				case END2:
					end_position_int+=100;
					break;
				case END3:
					end_position_int+=10;
					break;
				case END4:
					end_position_int+=1;
					break;
				case STEP1:
					position_step_int+=1000;
					break;
				case STEP2:
					position_step_int+=100;
					break;
				case STEP3:
					position_step_int+=10;
					break;
				case STEP4:
					position_step_int+=1;
					break;
		}
		if(start_position_int>=9000) start_position_int=9000;
		if(start_position_int<=0) start_position_int=0;
		if(end_position_int>=9000)end_position_int=9000;
		if(end_position_int<=0) end_position_int=0;
		if(position_step_int>=9000) position_step_int=9000;
		if(position_step_int<=0) position_step_int=0;
		printf("s1.txt=\"%d\"\xff\xff\xff",start_position_int/1000);
		printf("s2.txt=\"%d\"\xff\xff\xff",start_position_int/100%10);
		printf("s3.txt=\"%d\"\xff\xff\xff",start_position_int/10%10);
		printf("s4.txt=\"%d\"\xff\xff\xff",start_position_int%10);
		printf("e1.txt=\"%d\"\xff\xff\xff",end_position_int/1000);
		printf("e2.txt=\"%d\"\xff\xff\xff",end_position_int/100%10);
		printf("e3.txt=\"%d\"\xff\xff\xff",end_position_int/10%10);
		printf("e4.txt=\"%d\"\xff\xff\xff",end_position_int%10);
		printf("u1.txt=\"%d\"\xff\xff\xff",position_step_int/1000);
		printf("u2.txt=\"%d\"\xff\xff\xff",position_step_int/100%10);
		printf("u3.txt=\"%d\"\xff\xff\xff",position_step_int/10%10);
		printf("u4.txt=\"%d\"\xff\xff\xff",position_step_int%10);
		break;
		case MEASUER_START:
			switch(cursor_measuer_start)
			{
				case P1:
					pos_measure_start+=1000;		
				break;
				case P2:
					pos_measure_start+=100;				
				break;
				case P3:
					pos_measure_start+=10;				
				break;
				case P4:
					pos_measure_start+=1;
				break;
			}
			if(pos_measure_start>=9000) pos_measure_start=9000;
			if(pos_measure_start<=0) pos_measure_start=0;
			printf("p1.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)/1000);	
			printf("p2.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)/100%10);	
			printf("p3.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)/10%10);	
			printf("p4.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)%10);	
		break;
		
		default:down_button();break;
	}
}

void counter_clockwise()
{
	switch(page)
	{
		case GENERATE_COORDINATES:
			switch(cursor_generate_coordinates)
			{
				case START1:
					start_position_int-=1000;
					break;
				case START2:
					start_position_int-=100;
					break;
				case START3:
					start_position_int-=10;
					break;
				case START4:
					start_position_int-=1;
					break;
				case END1:
					end_position_int-=1000;
					break;
				case END2:
					end_position_int-=100;
					break;
				case END3:
					end_position_int-=10;
					break;
				case END4:
					end_position_int-=1;
					break;
				case STEP1:
					position_step_int-=1000;
					break;
				case STEP2:
					position_step_int-=100;
					break;
				case STEP3:
					position_step_int-=10;
					break;
				case STEP4:
					position_step_int-=1;
					break;
			}
			if(start_position_int>=9000) start_position_int=9000;
			if(start_position_int<=0) start_position_int=0;
			if(end_position_int>=9000)end_position_int=9000;
			if(end_position_int<=0) end_position_int=0;
			if(position_step_int>=9000) position_step_int=9000;
			if(position_step_int<=0) position_step_int=0;
			printf("s1.txt=\"%d\"\xff\xff\xff",start_position_int/1000);
			printf("s2.txt=\"%d\"\xff\xff\xff",start_position_int/100%10);
			printf("s3.txt=\"%d\"\xff\xff\xff",start_position_int/10%10);
			printf("s4.txt=\"%d\"\xff\xff\xff",start_position_int%10);
			printf("e1.txt=\"%d\"\xff\xff\xff",end_position_int/1000);
			printf("e2.txt=\"%d\"\xff\xff\xff",end_position_int/100%10);
			printf("e3.txt=\"%d\"\xff\xff\xff",end_position_int/10%10);
			printf("e4.txt=\"%d\"\xff\xff\xff",end_position_int%10);
			printf("u1.txt=\"%d\"\xff\xff\xff",position_step_int/1000);
			printf("u2.txt=\"%d\"\xff\xff\xff",position_step_int/100%10);
			printf("u3.txt=\"%d\"\xff\xff\xff",position_step_int/10%10);
			printf("u4.txt=\"%d\"\xff\xff\xff",position_step_int%10);
		break;
		case MEASURE_COIL:
		{
			Current-=0.1*beishu;
			if(Current<-MAX_CURRENT) Current=-MAX_CURRENT;
			printf("a.txt=\"%.1f\"\xff\xff\xff",Current);
		}	break;	
		case MAIN:if(cursor_main==CAL) k-=0.01;else up_button();break;
		case MEASUER_START:
			switch(cursor_measuer_start)
			{
				case P1:
					pos_measure_start-=1000;		
				break;
				case P2:
					pos_measure_start-=100;				
				break;
				case P3:
					pos_measure_start-=10;				
				break;
				case P4:
					pos_measure_start-=1;
				break;
			}	
			if(pos_measure_start>=9000) pos_measure_start=9000;
			if(pos_measure_start<=0) pos_measure_start=0;
			printf("p1.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)/1000);	
			printf("p2.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)/100%10);	
			printf("p3.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)/10%10);	
			printf("p4.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)%10);	
		break;
		default:up_button();break;
	}
}