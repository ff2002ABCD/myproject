#include <math.h>  
#include <stdlib.h>  
#include <main.h>
#include "dac.h"
#include "adc.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"
#include "stdio.h"
#include "osc.h"
#include "stdlib.h"
#include "control.h"
#include "measure.h"
#define N 1024

typedef struct{ 
	double real;
	double imag;
}complex;
complex x[N], *W;
int size=0; 
double PI=3.14159265358979;
uint32_t FFT[N];

void output()
{
	int i;
	for(i=0;i<size;i++)
	{	
//		printf("t%d.txt=\"%.4f\"\xff\xff\xff",2*i,x[i].real);
//		printf("t%d.txt=\"%.4f\"\xff\xff\xff",2*i+1,x[i].imag);
//		printf("%.4f",x[i].real);
//		if(x[i].imag>=0.0001)
//		{
//			printf("+%.4fj\xff\xff\xff",x[i].imag);
//		}
//		else if(fabs(x[i].imag)<0.0001)
//		{
//			printf("\xff\xff\xff");
//		}
//		else
//		{
//			printf("%.4fj\xff\xff\xff",x[i].imag);
//		}
		FFT[i]=sqrt((x[i].real*x[i].real+x[i].imag*x[i].imag));
		//printf("%d\xff\xff\xff",FFT[i]);
	}
}

void change()
{
	complex temp;
	unsigned short i=0,j=0,k=0;
	double t;
	for(i=0;i<size;i++)
	{
		k=i;
		j=0;
		t=(log(size)/log(2));
		while( (t--)>0 )
		{
			j=j<<1;
			j|=(k & 1);
			k=k>>1;
		}
		if(j>i)
		{
			temp=x[i];
			x[i]=x[j];
			x[j]=temp;
		}
	}
	//output();
}
void transform()
{
	int i;
	W=(complex *)malloc(sizeof(complex) * size);
	for(i=0;i<size;i++)
	{
		W[i].real=cos(2*PI/size*i);
		W[i].imag=-1*sin(2*PI/size*i);
	}
}
void add(complex a,complex b,complex *c)
{
	c->real=a.real+b.real;
	c->imag=a.imag+b.imag;
}
void sub(complex a,complex b,complex *c)
{
	c->real=a.real-b.real;
	c->imag=a.imag-b.imag;
}
void mul(complex a,complex b,complex *c)
{
	c->real=a.real*b.real - a.imag*b.imag;
	c->imag=a.real*b.imag + a.imag*b.real;
}
void fft()
{
	int i=0,j=0,k=0,m=0;
	complex q,y,z;
	change();
	for(i=0;i<log(size)/log(2) ;i++)
	{
		m=1<<i;
		for(j=0;j<size;j+=2*m)
		{
			for(k=0;k<m;k++)
			{
				mul(x[k+j+m],W[size*k/2/m],&q);
				add(x[j+k],q,&y);
				sub(x[j+k],q,&z);
				x[j+k]=y;
				x[j+k+m]=z;
			}
		}
	}
}
//M:频谱长度,n:频率轴间隔,m：频谱数据间隔,k：幅度
void FFT_display(uint32_t M,uint8_t n,uint8_t m,float k) 
{
	uint32_t j;
	uint32_t temp=0;
	for(j=0;j<M;j++)
	{
		temp=(uint32_t)FFT[m*j+1]*k;
		printf("fill %d,%d,1,%d,YELLOW\xff\xff\xff",n*j+1,384-temp,temp);
		
	}
	delay_ms(50);
	//HAL_TIM_Base_Start_IT(&htim4);
	
}

void dofft(uint8_t ch)
{
	int i;
	size=256;
//size=4;
	if(ch==0)
	{
		for(i=0;i<size;i++)
		{
			x[i].real=ad1[TriggerPoint-offset-325+i];
			x[i].imag=0;
		}
	}
	else
	{
		for(i=0;i<size;i++)
		{
			x[i].real=ad2[TriggerPoint-offset-325+i];
			x[i].imag=0;
		}
	}
	
//	x[0].real=32;
//	x[1].real=64;
//	x[2].real=128;
//	x[3].real=38;
//	for(int i=0;i<64;i++)
//	{
//		x[i].real=32;
//	}
//	for(int i=64;i<128;i++)
//	{
//		x[i].real=192;
//	}
//	for(int i=128;i<192;i++)
//	{
//		x[i].real=32;
//	}
//	for(int i=192;i<256;i++)
//	{
//		x[i].real=192;
//	}
	
	transform();
	fft();
	output();
	FFT_display(128,4,1,0.014);
}
