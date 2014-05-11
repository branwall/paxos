import sys
proposers=[]
acceptors=[]
tmax=None
tick=0
mtypes=['PROP','PREP','PROM','ACC','ACCD','REJ']
ctypes=['P','A']
class C: 
    def __init__(self,num,ty):
        self.num=num
        assert ctypes.count(ty)>0
        self.ty=ty
        self.failed=False
        #self.state=None    ##For future functionality
    def fail(self):
        self.failed=True
    def recover(self):
        self.failed=False
    def display(self):
        print " -----------------"
        print "|   %s # %d  |" % (("Proposer" if self.ty == 'P' else "Acceptor"), self.num)
        print "|   Failed?  %s   |" % ("yes" if self.failed==True else "no")
        print " -----------------"

class Message:
    def __init__(self,ty,dest,source,propid,prior=None,val=None):
        assert mtypes.index(ty)>=0
        self.kind=ty
        self.dst=dest
        self.src=source
        self.propid=propid
        self.prior=prior
        self.val=val
    def display(self):
        print "/////////////////////////////"
        print "Message of type %s" % self.kind
        print "from"
        C.display(self.src)
        print "to"
        C.display(self.dst)
        print "Proposal ID: %d" % self.propid
        print "Prior Proposal?", self.prior
        print "Value?", self.val
        print "/////////////////////////////"
    def minidisplay(self):
        print "%d: Msg type %s from %s%d to %s%d" % (self.propid,
                                                     self.kind,
                                                     self.src.ty,
                                                     self.src.num,
                                                     self.dst.ty,
                                                     self.dst.num)
class Network:
    def __init__(self):
        self.counter=0
        self.queue=[]
    def enq(self,msg):
        self.queue.append(msg)
    def deq(self):
        for i in self.queue:
            if i.src.failed==True or i.dst.failed==True:
                return None
            self.queue.pop(0)
    def display(self):
        print "-----Network:-----"
        for i in self.queue:
            Message.minidisplay(i)
        print "------------------"
class Event:
    def __init__(self,string):
        x=string.split()
        self.tick=int(x[0])
        assert x[1]=="PROPOSE" or x[1]=="FAIL" or x[1]=="RECOVER"
        self.ty=x[1][0] # ie, ty will be 'P' or 'F' or 'R'
        if self.ty=="P":
            self.value=int(x[3])
            self.c = proposers[int(x[2])-1]
        else:
            self.c = proposers[int(x[3])-1] if x[2]=="PROPOSER" else acceptors[int(x[3])-1]
            self.value=None    
    def display(self):
        print "%d: Event type %s" % (self.tick, self.ty)
        if self.ty == 'P':
            print "(Proposer %d proposes %d)\n" % (self.c.num, self.value)
        else:
            print "(%s %s %d)\n" % ( ("Fail" if self.ty=='F' else "Recover"),
                                   self.c.ty, self.c.num)

def whois():
    for p in proposers:
        C.display(p)
    for a in acceptors:
        C.display(a)
def initialize(): #will make a list of valid input file
    L=[]
    for line in sys.stdin:
        #print line
        if line[0]!='#' and len(line.split())>1 and line.split()[1]!="END":
            L.append(line.rstrip())
    
    setupvars=L[0].split()
    for i in range(0,int(setupvars[0])):
        proposers.append(C(i+1,'P'))
    for i in range(0,int(setupvars[1])):
        acceptors.append(C(i+1,'A'))
    global tmax
    tmax=int(setupvars[2])
    return L

def etick(li):
    return li[0].tick

def process_events(t,li):
    print "Processing all events at tick %d from events list" % t
    for i in li:
        Event.display(i)

def deliver_msg(n):
    print "Delivering the first of the following:"
    Network.display(n)

def runsim(elist, ntwk):
    while tick<=tmax:
        if ntwk.queue == [] and elist == []:
            print "No more events, fix this"
            return
        elif elist!=[] and etick(elist)==tick:
            process_events(tick,elist)
        elif ntwk.queue!=[]:
            deliver_msg(ntwk)
        
        global tick
        tick+=1


def main():
    L=initialize()
    n=Network()
    E=[]
    for i in range(1,len(L)):
        E.append(Event(L[i]))
    
    runsim(E,n)

main()
