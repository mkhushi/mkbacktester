import matplotlib.pyplot as plt

class visualise:

    def __init__(self,data):
        self.data = data

        # Chart look and feel
        self.line_color = 'blue'
        self.buy_marker = '^'
        self.sell_marker = 'v'
        self.hold_marker = 'None'
        self.buy_marker_color = 'green'
        self.sell_marker_color = 'red'
        self.hold_marker_color = 'grey'
        self.marker_size = 9
        
        
        
        arr_action = []
        arr_action.extend(data['action'])
        self.arr_open = []
        self.arr_open.extend(data['open'])
        self.arr_buy =[]
        self.arr_sell = []
        self.arr_hold = []
        for i in range(len(self.arr_open)):
            if arr_action[i] == "buy" or arr_action[i] == "short_buy":
                self.arr_buy.append((i, self.arr_open[i]))
            elif arr_action[i] == "sell" or arr_action[i] == "short":
                
                self.arr_sell.append((i, self.arr_open[i]))
            elif arr_action[i] == "hold":
                self.arr_hold.append((i, self.arr_open[i]))
            #else:
            #    print("Unrecognised Action!!")

    def plotFig(self):
        plt.plot(self.arr_open,color=self.line_color,marker='None')
        x,y = zip(*self.arr_buy)
        plt.plot(x, y,markerfacecolor=self.buy_marker_color, linestyle='None',marker=self.buy_marker, markersize=self.marker_size,markeredgecolor=self.buy_marker_color)
        x,y = zip(*self.arr_sell)
        plt.plot(x, y, markerfacecolor=self.sell_marker_color,linestyle='None', marker=self.sell_marker, markersize=self.marker_size,markeredgecolor=self.sell_marker_color)
        x,y = zip(*self.arr_hold)
        plt.plot(x, y, markerfacecolor=self.hold_marker_color,linestyle='None', marker=self.hold_marker, markersize=self.marker_size,markeredgecolor=self.hold_marker_color)
        plt.show()

    