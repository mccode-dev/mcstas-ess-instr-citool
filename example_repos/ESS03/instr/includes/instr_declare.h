#include "foobar.c"

double calcAlpha(double length, double radius) {
  // calculate angle of arm after curved guide
  return RAD2DEG * length/radius;
}

double calcX(double length, double radius) {
  // calculate position and angle of arm after curved guide
  double alpha = DEG2RAD * calcAlpha(length, radius);
  return radius*(1.0-cos(alpha));
}

double calcZ(double length, double radius) {
  // calculate position and angle of arm after curved guide
  double alpha = DEG2RAD * calcAlpha(length, radius);
  return radius*sin(alpha);
}

double XW, YH;
char options1[256],options2[256],options3[256],options4[256];
char srcdef[128];
double WidthC=0.072,WidthT=0.108;
double lambdamin, lambdamax;
double TCollmin;
double TCollmax;
#pragma acc declare create(TCollmin,TCollmax)
double EminTh=20, EmaxTh=100, EminC=0, EmaxC=20;
#pragma acc declare create(EminTh,EmaxTh,EminC,EmaxC)
/* 10 beamlines in sector N and E  - plus one location added for drawing */
double iBeamlinesN[] = { 30.0,  36.0,  42.0,  48.0,  54.0,  60.0,  66.0,  72.0,  78.0,  84.0,  90.0};
double iBeamlinesE[] = {-30.0, -36.0, -42.0, -48.0, -54.0, -60.0, -66.0, -72.0, -78.0, -84.0, -90.0};
/* 11 beamlines in sector S and W - plus one location added for drawing */
double iBeamlinesW[] = { 150.0,  144.7,  138.0,  132.7,  126.0,  120.7,  114.0,  108.7,  102.0,  96.7,  90.0,  84.0};
double iBeamlinesS[] = {-150.0, -144.7, -138.0, -132.7, -126.0, -120.7, -114.0, -108.7, -102.0, -96.7, -90.0, -84.0};
double* iBeamlines;
double ANGLE;
double DeltaX,DeltaZ;
