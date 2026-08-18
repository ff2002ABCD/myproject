#ifndef MATHFUN_H
#define MATHFUN_H

extern void int2char(char * datap,unsigned int num,unsigned char dot,unsigned char ln);	   //从datap开始ln个字节,dot位小数

#define INTLINEARN 9
extern unsigned int intLinearX[INTLINEARN],intLinearY[INTLINEARN];
extern unsigned int intLinear(unsigned int x); 		//非线性修正

//digital filter,yl[0]=current output,yl[1]=rest data,ul[0]=last input,u=current input
//Yk+1=((VFLT1N-1)Yk+Uk-1+Uk)/(VFLT1N+1)
#define VFLTXN	1000 
extern void vflt1(char yl[2],char ul[1],char u); 		
extern void vflt3(unsigned int data yl[2],unsigned int data ul[1],unsigned int data u);	

#endif