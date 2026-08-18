#include "MATHFUN.H"

unsigned int intLinearX[INTLINEARN],intLinearY[INTLINEARN];

void int2char(char * datap,unsigned int num,unsigned char dot,unsigned char ln)
{
	bit dotx=0;
	if(dot)
		dotx=1;
	datap +=ln-1;
	if(!num)
	{
		*datap--='0';
		ln--;
		dot--;
	}
	while(num)
	{
		if(dotx)
		{
			if(dot--)
			{
				*datap--=num%10+0x30;
				num/=10;
			}
			else
			{
				dotx=0;
				*datap--='.';
			}
		}
		else
		{
			*datap--=num%10+0x30;
			num/=10;
		}
		ln--;
	}
	if(dotx)
	{
		ln-=dot+2;
		for(;dot>0;dot--)
			*datap--='0';
		*datap--='.';
		*datap--='0';
	}
	for(;ln>0;ln--)
		*datap--=' ';
}

unsigned long xt1,xt2;

unsigned int intLinear(unsigned int x)
{
	unsigned char i;
	if(x<=intLinearX[0])
		return intLinearY[0];
	else if(x>=intLinearX[INTLINEARN-1])
		return intLinearY[INTLINEARN-1];
	for(i=1;i<INTLINEARN;i++)
		if(x<intLinearX[i])
		{
			xt1=x;
			xt2=intLinearX[i-1];
			xt1-=xt2;
			x=intLinearY[i]-intLinearY[i-1];
			xt2=x;
			xt1*=xt2;
			x=intLinearX[i]-intLinearX[i-1];
			xt2=x;
			xt1/=xt2;
			xt2=intLinearY[i-1];
			xt1+=xt2;
			return xt1;
		}
	return 0;
} 

void vflt1(char yl[],char ul[],char u)
{
	int s,t;
	s=(int)u+ul[0]+(int)yl[0]*(VFLTXN-1)+yl[1];
	t=s;
	s/=(VFLTXN+1);
	yl[0]=s;
	t-=s*(VFLTXN+1);
	yl[1]=t;
	ul[0]=u;
}

void vflt3(unsigned int data yl[],unsigned int data ul[],unsigned int data u)
{
	long data s,t;
	s=(long)u+ul[0]+(long)yl[0]*(VFLTXN-1)+yl[1];
	t=s;
	s/=(VFLTXN+1);
	yl[0]=s;
	t-=s*(VFLTXN+1);
	yl[1]=t;
	ul[0]=u;
}

