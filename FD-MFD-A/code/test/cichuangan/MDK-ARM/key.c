#include "key.h"
#include "stdio.h"

KEY_STATE KeyState;
KEY_VALUE g_Key;
KEY_TYPE g_KeyActionFlag;
extern int fputc(int ch, FILE* file);

void Key_Scan(void)
{	
		static uint32_t TimeCnt = 0;
    static uint8_t lock = 0;
		static uint16_t long_counter=0;
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
								if(!lock)   lock = 1;
								TimeCnt++;  
								Cnt=10;
								if(long_counter==0)//µÚÒ»´Î¼ì²â
								{
									if(g_Key == KEY_0)
									{
										if(TimeCnt>Cnt*10)         
										{
											g_KeyActionFlag = LONG_KEY;	
											TimeCnt = 0;  
											lock = 0;
											KeyState =  KEY_RELEASE;  
										}
									}
									else
									{
										if(TimeCnt>Cnt*5)         
										{
											g_KeyActionFlag = LONG_KEY;	
											TimeCnt = 0;  
											lock = 0; 
											long_counter++;
										}
									}
								}
                if(long_counter!=0)
								{
									
									if(TimeCnt>Cnt*3)         
									{
											g_KeyActionFlag = LONG_KEY;	
											TimeCnt = 0;  
											lock = 0; 
										long_counter++;
										 
									}        
								}
                
            }   
            else                      
            {		
								
                if(1==lock&&long_counter==0)           
                {

                    g_KeyActionFlag = SHORT_KEY;      
                    KeyState =  KEY_RELEASE;   
                }
                
                else         
                {		
										
                    KeyState =  KEY_CHECK;  
                }
								long_counter=0;
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
			case KEY_0:
				
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						modify_num+=1;
						if(modify_num==7) modify_num=0;
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					else if(g_KeyActionFlag==LONG_KEY) 
					{
							flag_write=1;
							printf("k0changan\r\n");
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			
			case KEY_1:
					 
						if(g_KeyActionFlag==SHORT_KEY) 
						{
							if(modify_num==0) return;
							*modify_now+=0.01;
							printf("modify_now++\r\n");
							g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
						}
						else if(g_KeyActionFlag==LONG_KEY) 
						{
							if(modify_num==0) return;
							*modify_now+=0.05;
							printf("modify_now++\r\n");
							g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
						}
			break;
			
			case KEY_2:
					 
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						if(modify_num==0) return;
						*modify_now-=0.01;
						printf("modify_now--\r\n");
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					else if(g_KeyActionFlag==LONG_KEY) 
					{
						if(modify_num==0) return;
						*modify_now-=0.05;
						printf("modify_now--\r\n");
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			
			default: break;
	}
}