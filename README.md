## Forex / Stock Back Testing Made Easy
Back test your trading strategy on historical prices on any financial markets (Forex/Stock and others). 

main.py is the main file that you need to edit for historical prices file.
Read comments in the files.

Install TA-Lib via Anconda command prompt

$ conda install -c conda-forge ta-lib

You could also install TA-LIB from pre-compiled python wheels. Download from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
Check your Python and make sure you download the right wheel for your platform (Windows/Mac, Python Version etc.)

command on Windows:

pip install C:\Users\matloob\Downloads\TA_Lib-0.4.18-cp38-cp38-win32.whl

main.py file saves output to a csv file, and calls visualise.py which draws a plot of prices, buy and sell signals.

To manually observe the backtesting trading data use jupyter notebook visualise.ipynb
