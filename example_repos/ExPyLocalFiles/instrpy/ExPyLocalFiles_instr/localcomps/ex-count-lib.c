int ex_in_rectangle(double x, double y, double xwidth, double yheight)
{
  return x > -xwidth/2 && x < xwidth/2 && y > -yheight/2 && y < yheight/2;
}
