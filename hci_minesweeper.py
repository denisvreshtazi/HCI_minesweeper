

# Denis Vreshtazi
#HCI_minesweeper

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import random
import time

FLAG = QImage("./images/flag.png")
BOMB = QImage("./images/bomb.png")

STATUS_READY = 0
STATUS_PLAYING = 1
STATUS_FAILED = 2
STATUS_SUCCESS = 3

STATUS_ICONS = {
    STATUS_READY: "./images/play.png",
    STATUS_PLAYING: "./images/playing.png",
    STATUS_FAILED: "./images/lose.png",
    STATUS_SUCCESS: "./images/award.png",
}

class Quad(QWidget):
    
    # Every rectangle in the field of minesweeper
    expandable = pyqtSignal(int, int)
    clicked = pyqtSignal()
    rightclicked = pyqtSignal()
    ohno = pyqtSignal()
    ohyes= pyqtSignal()
    
    def __init__(self, x, y, *args,  **kwargs):
        super(Quad, self).__init__(*args, **kwargs)
        
        self.setFixedSize(QSize(25, 25))

        self.x = x
        self.y = y


    def reset(self):
        self.is_revealed = False
        self.is_flagged = False
        self.is_mine = False
        self.adjacent_n = 0

        self.update()
    
    
   
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = event.rect()

        if self.is_revealed:
            color = self.palette().color(QPalette.Background)
            outer, inner = Qt.black, color
        else:
            outer, inner = Qt.gray, Qt.lightGray

        p.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(r)

        if self.is_revealed:
            if self.is_mine:
                p.drawPixmap(r, QPixmap(BOMB))

            elif self.adjacent_n >= 0:
                pen = QPen(Qt.blue)
                p.setPen(pen)
                f = p.font()
                f.setBold(True)
                p.setFont(f)
                p.drawText(r, Qt.AlignHCenter | Qt.AlignVCenter, str(self.adjacent_n))

        elif self.is_flagged:
            p.drawPixmap(r, QPixmap(FLAG))
    
            
            
    def flag(self):
            if(self.is_flagged==False) : 
                self.is_flagged = True   
                self.update()              
                self.rightclicked.emit()
        
        
    def reveal(self):
            self.is_revealed = True
            self.update()          
          
                    
    def click(self):
        if not self.is_revealed:
            self.reveal()
            if self.adjacent_n == 0:
                self.expandable.emit(self.x, self.y)
       
        self.clicked.emit()
        self.ohyes.emit()
        
        
    def mouseReleaseEvent(self, e):
            if (e.button() == Qt.RightButton and not self.is_revealed):
                self.flag()     

            elif (e.button() == Qt.LeftButton):
                self.click()

                if self.is_mine:
                    self.ohno.emit()
                    
                 
class MainWindow(QMainWindow):
    #The Completed View  and every widget : time, flags and different levels 
    def __init__(self, box_size, n_mines , *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)	
        
        self.box_size = box_size
        self.n_mines = n_mines
        self.n_flags=n_mines
        
        w = QWidget()
        hb = QHBoxLayout()

        self.flags = QLabel()
        self.clock = QLabel()        

        self.flags.setText("%03d" % self.n_flags + "/%03d" %self.n_mines)
               
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.clock.setText("000")
        
        self.button = QPushButton()
        self.button.setFixedSize(QSize(32, 32))
        self.button.setIconSize(QSize(32, 32))
        self.button.setIcon(QIcon("./images/smiley.png"))
        self.button.setFlat(True)
        self.button.pressed.connect(self.button_pressed)
        
        self.easy_level = QPushButton()
        self.easy_level.setFixedSize(QSize(40, 32))
        self.easy_level.setText("Easy")
        self.easy_level.setFlat(True)
        self.easy_level.pressed.connect(self.easy)
        
        self.medium_level = QPushButton()
        self.medium_level.setFixedSize(QSize(50, 32))
        self.medium_level.setText("Medium")
        self.medium_level.setFlat(True)
        self.medium_level.pressed.connect(self.medium)
        
        self.hard_level = QPushButton()
        self.hard_level.setFixedSize(QSize(40, 32))
        self.hard_level.setText("Hard")
        self.hard_level.setFlat(True)
        self.hard_level.pressed.connect(self.hard)
        
        hb.addWidget(self.flags)
        hb.addWidget(self.button)
        hb.addWidget(self.clock)
        hb.addWidget(self.easy_level)
        hb.addWidget(self.medium_level)
        hb.addWidget(self.hard_level)
        
        vb = QVBoxLayout()
        vb.addLayout(hb)
        
        self.grid = QGridLayout()
        self.grid.setSpacing(5)
        vb.addLayout(self.grid)
        
        w.setLayout(vb)
        self.setCentralWidget(w)

        self.init_map()
        self.update_status(STATUS_READY)
        
        self.reset_map()
        self.update_status(STATUS_READY)

        self.show()
        
        
    def init_map(self):
            # Add positions to the map
            for x in range(0, self.box_size):
                for y in range(0, self.box_size):
                    w = Quad(x, y)
                    self.grid.addWidget(w, y, x)
                    # Connect signal to handle expansion.
                    w.clicked.connect(self.trigger_start)
                    w.rightclicked.connect(self.button_right_clicked)
                    w.expandable.connect(self.expand_reveal)
                    w.ohyes.connect(self.on_reveal)
                    w.ohno.connect(self.game_over)
                    
                    
    def reset_map(self):
            # Clear all mine positions
            for x in range(0, self.box_size):
                for y in range(0, self.box_size):
                    w = self.grid.itemAtPosition(y, x).widget()
                    w.reset()
                    
             # Add mines to the positions
            positions = []
            while len(positions) < self.n_mines:
                x, y = random.randint(0, self.box_size - 1), random.randint(0, self.box_size - 1)
                if (x, y) not in positions:
                    w = self.grid.itemAtPosition(y, x).widget()
                    w.is_mine = True
                    positions.append((x, y))
                    
            self.end_game_n = (self.box_size * self.box_size) - (self.n_mines )
            
                    
            def get_adjacency_n(x, y):
                positions = self.get_surrounding(x, y)
                n_mines = sum(1 if w.is_mine else 0 for w in positions)

                return n_mines

            # Add adjacencies to the positions
            for x in range(0, self.box_size):
                for y in range(0, self.box_size):
                    w = self.grid.itemAtPosition(y, x).widget()
                    w.adjacent_n = get_adjacency_n(x, y)                    
            
                    
                    
    def get_surrounding(self, x, y):
        positions = []
        for xi in range(max(0, x - 1), min(x + 2, self.box_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.box_size)):
                    positions.append(self.grid.itemAtPosition(yi, xi).widget())

        return positions 
            
            
    def button_pressed(self):
        self.update_status(STATUS_READY)
        self.reset_map()
                
                
    def button_right_clicked(self):  
            button = self.sender()   
            if (self.n_flags > 0):
                    self.n_flags = self.n_flags -1
                    self.flags.setText("%03d" % self.n_flags + "/%03d" %self.n_mines)
                
                
    def reveal_map(self):
            for x in range(0, self.box_size):
                for y in range(0, self.box_size):
                    w = self.grid.itemAtPosition(y, x).widget()
                    w.reveal()            
                      
            
    def expand_reveal(self, x, y):
        for xi in range(max(0, x - 1), min(x + 2, self.box_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.box_size)):
                w = self.grid.itemAtPosition(yi, xi).widget()
                if not w.is_mine:
                    w.click()
            
                        
    def trigger_start(self, *args):
            if self.status != STATUS_PLAYING:
                # First click.
                self.update_status(STATUS_PLAYING)
                # Start timer.
                self._timer_start_nsecs = int(time.time()) 
                
                
    def update_status(self, status):
            self.status = status
            self.button.setIcon(QIcon(STATUS_ICONS[self.status])) 
            
            
    def update_time(self):
            if self.status == STATUS_PLAYING:
                n_secs = int(time.time()) - self._timer_start_nsecs
                self.clock.setText("%03d" % n_secs)         


    def on_reveal(self):
        #Check if have won
        self.end_game_n = (self.box_size * self.box_size) - (self.n_mines )    
        
        for x in range(0, self.box_size):
                for y in range(0, self.box_size):
                    w = self.grid.itemAtPosition(y, x).widget()
                    if w.is_revealed:
                        self.end_game_n -= 1 
                        if self.end_game_n == 0:
                            self.win()    
                            
                
    def game_over(self):
        self.reveal_map()
        self.update_status(STATUS_FAILED)     


    def win(self):
            self.reveal_map()
            self.update_status(STATUS_SUCCESS)                
        
                        
    def easy(self):
            self.b_size, self.n_mines = 9,10
            self.n_flags = self.n_mines             
            self.close()
            self.__init__(self.b_size,self.n_mines)
            
            
    def medium(self):
            self.b_size, self.n_mines = 16,40
            self.n_flags = self.n_mines             
            self.close()
            self.__init__(self.b_size,self.n_mines)
            
            
    def hard(self):
            self.b_size, self.n_mines = 22, 99
            self.n_flags = self.n_mines             
            self.close()
            self.__init__(self.b_size,self.n_mines)
            
                   
       
            

                    
                  
                        
if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow(9,1)
    app.exec_()
        
        
        
        
       
        
       
       

       
    
    
    
    
    
    
    
    
    
    
    
