#include "button.h"
#include "menu.h"
#include "stdio.h"
#include "osc.h"
KEY_STATE KeyState;
KEY_VALUE g_Key;
KEY_TYPE g_KeyActionFlag;
extern int fputc(int ch, FILE* file);
uint16_t long_counter=0;

void Key_Scan(void)
{	
		static uint32_t TimeCnt = 0;
    static uint8_t lock = 0;
		
		static uint8_t Cnt;
    switch (KeyState)
    {
        case   KEY_CHECK:    
            if(!Key)   
            {
                KeyState =  KEY_COMFIRM;  
            }
						TimeCnt = 0;                
            lock = 0;
            break;
        case   KEY_COMFIRM:
            if(!Key)            
            {
                if(0 == KEY0)
                    g_Key = KEY_0;
                else if(0 == KEY1)
                    g_Key = KEY_1;
                else if(0 == KEY2)
                    g_Key = KEY_2;
								else if(0 == KEY3)
                    g_Key = KEY_3;
								else if(0 == KEY4)
                    g_Key = KEY_4;
								else if(0 == KEY5)
                    g_Key = KEY_5;
								if(!lock)   lock = 1;
								TimeCnt++;  
								if(g_Key == KEY_2|g_Key==KEY_3) Cnt=12;
								else Cnt=16;
								if(long_counter==0)
								{
									if(TimeCnt>Cnt*2)         
									{
											g_KeyActionFlag = LONG_KEY;	
											TimeCnt = 0;  
											lock = 0; 
										long_counter++;
										//	KeyState =  KEY_RELEASE;   
									}        
								}
                if(long_counter<10&&long_counter!=0)
								{
									
									if(TimeCnt>Cnt)         
									{
											g_KeyActionFlag = LONG_KEY;	
											TimeCnt = 0;  
											lock = 0; 
										long_counter++;
										//	KeyState =  KEY_RELEASE;   
									}        
								}
								else if(long_counter>=10)
								{
									if(TimeCnt>Cnt/4)         
									{
											g_KeyActionFlag = LONG_KEY;	
											TimeCnt = 0;  
											lock = 0; 
										//	KeyState =  KEY_RELEASE;   
									}      
								}
                
            }   
            else                      
            {		
								long_counter=0;
                if(1==lock)           
                {

                    g_KeyActionFlag = SHORT_KEY;      
                    KeyState =  KEY_RELEASE;   
                }
                
                else         
                {		
										
                    KeyState =  KEY_CHECK;  
                }
            } 
            break;
         //??????
         case  KEY_RELEASE:
             if(Key)                
             { 
								
                 KeyState =  KEY_CHECK;
             } 
             break;
         default: break;
    }
}

void do_key()
{
//	if(CH2_status==1)
//	{
//		for(;j<651;j++,i++)
//		{
//			printf("%c",ad2[i-325]);
//		}
//		printf("\x01\xff\xff\xff");//确保透传结束
//	}
//	else if(CH1_status==1)
//	{
//		for(;j<651;j++,i++)
//		{
//			printf("%c",ad1[i-325]);
//		}
//		printf("\x01\xff\xff\xff");//确保透传结束
//	}
	if(CH1_status==1|CH2_status==1)	if(long_counter==0) for(int i=0;i<200;i++)printf("\x01\xff\xff\xff");
	switch(g_Key)
   {
			case KEY_0:
				
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						
						up_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					if(g_KeyActionFlag==LONG_KEY) 
					{
						up_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			
			case KEY_1:
					 
						if(g_KeyActionFlag==SHORT_KEY) 
						{
							down_button();
							g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
						}
						if(g_KeyActionFlag==LONG_KEY) 
						{
							down_button();
							g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
						}
			break;
			
			case KEY_2:
					 
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						left_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					if(g_KeyActionFlag==LONG_KEY) 
					{
						left_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			case KEY_3:
					 
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						right_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					if(g_KeyActionFlag==LONG_KEY) 
					{
						right_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			
					case KEY_4:
					
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						confirm_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					if(g_KeyActionFlag==LONG_KEY) 
					{
						confirm_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			case KEY_5:
					
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						menu2_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					if(g_KeyActionFlag==LONG_KEY) 
					{
						menu2_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			
			default: break;
	}
}

