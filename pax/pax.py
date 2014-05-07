import sys
proposers=[]
acceptors=[]

class Props: #This is a class for proposers
    def __init__(self,num):
        self.num=num
        self.failed=False
        #self.state=None    ##For future functionality
    def fail(self):
        if self.failed==True:
            print "Error, proposer %d was already failed" % self.num
        self.failed=True
    def recover(self):
        if self.failed==False:
            print "Error, proposer %d was already running" % self.num
        self.failed=False
        
def initialize(): #will make a list of valid input file
    L=[]
    for line in sys.stdin:
        print line
        if line[0]!='#' and len(line.split())>1:
            if line.split()[1]=="END":
                return L
            L.append(line.rstrip())
    

print initialize()
