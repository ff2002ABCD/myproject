#include "button.h"
#include "menu.h"
#include "stdio.h"

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
                if(0 == KEYUP)
                    g_Key = KEY_UP;
                else if(0 == KEYDOWN)
                    g_Key = KEY_DOWN;
                else if(0 == KEYLEFT)
                    g_Key = KEY_LEFT;
								else if(0 == KEYRIGHT)
                    g_Key = KEY_RIGHT;
								else if(0 == KEYCONFIRM)
                    g_Key = KEY_CONFIRM;
								else if(0 == KEYCANCEL)
                    g_Key = KEY_CANCEL;
								else if(0 == KEYFUN)
                    g_Key = KEY_FUN;
								if(!lock)   lock = 1;
								TimeCnt++;  
								Cnt=16;
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
	switch(g_Key)
   {
			case KEY_UP:
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						up_button();renew_menu();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					if(g_KeyActionFlag==LONG_KEY) 
					{
						up_button();renew_menu();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			
			case KEY_DOWN:
						if(g_KeyActionFlag==SHORT_KEY) 
						{
							down_button();renew_menu();
							g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
						}
						if(g_KeyActionFlag==LONG_KEY) 
						{
							down_button();renew_menu();
							g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
						}
			break;
			
			case KEY_LEFT:
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						left_button();renew_menu();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					if(g_KeyActionFlag==LONG_KEY) 
					{
						left_button();
						renew_menu();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			case KEY_RIGHT:
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						right_button();
						
						renew_menu();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					if(g_KeyActionFlag==LONG_KEY) 
					{
					right_button();
						renew_menu();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			
			case KEY_CONFIRM:
				if(g_KeyActionFlag==SHORT_KEY) 
				{
					confirm_button();renew_menu();
					g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
				}
				if(g_KeyActionFlag==LONG_KEY) 
				{
					confirm_button();renew_menu();
					g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
				}
			break;
			case KEY_CANCEL:
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						cancel_button();renew_menu();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					if(g_KeyActionFlag==LONG_KEY) 
					{
						cancel_button();renew_menu();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			case KEY_FUN:
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						fun_button();renew_menu();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					if(g_KeyActionFlag==LONG_KEY) 
					{
						fun_button();renew_menu();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			default: break;
	}
}

