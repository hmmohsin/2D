set xlabel 'FCT(s)'
set ylabel 'CDF'

set terminal png size 1024,768 enhanced font "Helvetica,26"

set output 'cdf_p=90.png'
set grid
set grid lw 2
set logscale x
set key above
#files = ["VL2-2D-Offline"]

plot 'output.txt' u 1:5 title '2D-Offline' w lines lw 5, \
'output.txt' u 2:5 title '2D-Online-0' w lines lw 5, \
'output.txt' u 3:5 title '2D-Online-1' w lines lw 5, \
'output.txt' u 4:5 title '2D-Online-2' w lines lw 5
