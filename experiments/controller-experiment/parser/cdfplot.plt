set xlabel 'FCT(s)'
set ylabel 'CDF'

set terminal png size 1024,768 enhanced font "Helvetica,26"

set output 'cdf_p=90.png'
set grid
set grid lw 2
#set logscale x
set key above
#files = ["fifo_fct","ps_fct","2d_fct"]
set autoscale x

plot 'output.txt' u 1:3 title 'DCTCP-Offline' w lines lw 5, \
'output.txt' u 2:3 title 'DCTCP-Online' w lines lw 5
