
硬件平台：STM32F103R8T6  ；
软件实现：CH375 的底层驱动程序；

 硬件连接：           STM32      CH375
   	      PC0-PC7  <--->  D0-D7
	             PB5  <----  INT#
                              PB6  ---->  A0 
	              PB7  ---->  CS# 
	              PB8  ---->  WR#
	              PB9  ---->  RD# 