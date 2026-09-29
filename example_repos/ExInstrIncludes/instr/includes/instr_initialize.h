if ( !foobar_valid_beamline( sector, beamline ) )
  exit(1);
lambdamin=Lmin;
lambdamax=Lmax;
XW=1.05*(WidthC+2*WidthT);
YH=1.05*Yheight;
sprintf(options1,"user1 bins=201 limits=[-%g,%g]",XW/2,XW/2);
sprintf(options4,"user1 bins=201 limits=[-%g,%g]",YH/2,YH/2);
sprintf(options2,"user1 bins=201 limits=[-%g,%g], user2 bins=201 limits=[-%g,%g]",XW/2,XW/2,YH/2,YH/2);
sprintf(options3,"user1 bins=201 limits=[-%g,%g], user2 bins=201 limits=[-%g,%g]",1.05*(WidthC/2),1.05*(WidthC/2),1.05*Yheight/2,1.05*Yheight/2);
sprintf(srcdef,"2015");
if (beamline==1) {
  TCollmin=0;
  TCollmax=0.058;
 } else if (beamline==2) {
  TCollmin=0;
  TCollmax=0.06;
 }
 else {
   TCollmin=0.011;
   TCollmax=0.071;
 }
#pragma acc update device(TCollmin,TCollmax)
if (strcasestr(sector,"N")) {
  iBeamlines=iBeamlinesN;
  DeltaX=-0.0585; DeltaZ=0.0925;
 } else if (strcasestr(sector,"W")) {
  iBeamlines=iBeamlinesW;
  DeltaX=0.0585; DeltaZ=0.0925;
 } else if (strcasestr(sector,"S")) {
  iBeamlines=iBeamlinesS;
  DeltaX=0.0585; DeltaZ=-0.0925;
 } else if (strcasestr(sector,"E")) {
  iBeamlines=iBeamlinesE;
  DeltaX=-0.0585; DeltaZ=-0.0925;
 }
ANGLE=iBeamlines[beamline-1]-90;
#pragma acc update device(EminTh,EmaxTh,EminC,EmaxC)
