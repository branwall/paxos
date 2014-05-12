import sys
proposers=[]
acceptors=[]
tmax=None
tick=0
mtypes=['PROP','PREP','PROM','ACC','ACCD','REJ']
message_print_type={'PROP':'PROPOSE','PREP':'PREPARE','PROM':'PROMISE','ACC':'ACCEPT','ACCD':'ACCEPTED','REJ':'REJECTED'}
ctypes=['P','A']
class C: 
    def __init__(self,num,ty):
        self.num=num
        assert ctypes.count(ty)>0
        self.ty=ty
        self.lastprom=None #proposer uses this for last prop'd
        self.failed=False
        self.state=None if ty=='A' else []    ##in acceptor, proposal number, in proposer a list of promises
        self.reached=[]
        self.acclist=[]
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
            return self.queue.pop(0)
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

def process_events(t,li,n): #tick to process, 
    for c,i in enumerate(li):
        if i.tick>t:
            return li[c:]
        if i.ty=="P":
            print "%d:    -> %s%d  PROPOSE v=%d" % (t,i.c.ty,i.c.num,i.value)
            i.c.lastprom=i.value
            n.counter+=1
            for cc,ii in enumerate(acceptors):
                Network.enq(n,Message("PREP",ii,i.c,n.counter,None,i.value)) # don't forget prior & value
        elif i.ty=="F":
            C.fail(i.c)
            print "%d: ** %s%d FAILS **" % (t,i.c.ty,i.c.num)
        elif i.ty=="R":
            C.recover(i.c)
            print "%d: ** %s%d RECOVERS **" % (t,i.c.ty,i.c.num)
        
            
def majority(statelist):
    thresh=len(acceptors)/2
    ct=0
    statelist.reverse()
    last=statelist[0][1] # set equal to most recently recv'd proposal ID
    for i in statelist: #each I is a list of (acceptor, proposal id, prior value
        if i[1] == last:
            ct+=1
            if ct>=thresh:
                statelist.reverse()
                return last
        else:
            last=i[1]
            ct=1
    statelist.reverse()
    return None

def prunepropid(statelist,pruneid):
    import copy
    l2=copy.deepcopy(statelist)
    for i in l2:
        if i[1]==pruneid: #XXX: Should this be <= ? do I care about old proposal #s?
            l2.remove(i)
    return l2
        
def getval(statelist,checkid,comp):
    for i in statelist:
        if i[1]==checkid:
            return i[2] if i[2]!=None else comp.lastprom #this might need to be fixed in case I have different prior vals
    

def deliver_msg(n):
    m=Network.deq(n)
    sc=m.src # source computer
    dc=m.dst # destination computer
    t=m.kind # message type
    if t=='PROP':
        print "Error, proposals must come from outside the system"
    elif t=='PREP':
        print "%d: %s%d -> %s%d %s n=%d" % (tick,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid) 
        s_old=dc.state
        if s_old>m.val:
            Network.enq(n,Message('REJ',sc,dc,m.val,s_old))
            print "PRIOR PROPOSAL NUMBER WAS", dc.state
        else:
            dc.state=m.val
            dc.lastprom=m.val # should I pass this as the val in line below???
            Network.enq(n,Message('PROM',sc,dc,m.propid,s_old,dc.state))
    elif t=='PROM':
        dc.state.append([sc,m.propid,m.prior])
        x=majority(dc.state)
        if x!=None and dc.reached.count(m.propid)==0:
            dc.reached.append(x)
            for c,i in enumerate(acceptors):
                Network.enq(n,Message('ACC',i,dc,x,None,getval(dc.state,x,dc)))
            dc.state=prunepropid(dc.state,x)
        if m.prior==None:
            print "%d: %s%d -> %s%d %s n=%d (Prior: None)" % (tick,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid)
        else:
            print "%d: %s%d -> %s%d %s n=%d (Prior: n=%d, v=%d)" % (tick,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid,m.prior,sc.lastprom) 
    elif t=='ACC':
        print "%d: %s%d -> %s%d %s n=%d v=%d" % (tick,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid,m.val) 
        Network.enq(n,Message('ACCD',sc,dc,m.propid,None,m.val))
    elif t== 'REJ':
        print "%d: %s%d -> %s%d %s n=%d" % (tick,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid) 
    else: #t=='ACCD':
        dc.acclist.append([m.propid,m.val])
        print "%d: %s%d -> %s%d %s n=%d v=%d" % (tick,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid,m.val) 
                
    
def consensus(comp):
    comp.acclist.reverse()
    thresh=len(acceptors)/2
    count=0
    last=comp.acclist[0][0] #most recently acc'd prop num
    for i in comp.acclist:
        if i[0]==last:
            count+=1
            if count>=thresh:
                print "%s%d has reached consensus (proposed %d, accepted %d)" % (comp.ty,comp.num,comp.lastprom,i[1])
                return
        else:
            count=1
    print "%s%d did not reach consensus" % (comp.ty,comp.num)
    return

def network_empty(q):
    if q==[]:
        return True
    if q[0].src.failed==True or q[0].dst.failed==True:
        return network_empty(q[1:])
    else:
        return False 

def runsim(elist, ntwk):
    global tick
    while tick<=tmax:
        if ntwk.queue == [] and elist == None:
            print ""
            for i in proposers:
                consensus(i)
            return
        elif elist!=None and etick(elist)==tick:
            elist = process_events(tick,elist,ntwk)
        elif network_empty(ntwk.queue)!=True:
            deliver_msg(ntwk)
        else: #No events or active network
            print "%d:" % tick
        tick+=1
    print "sim ended bc u hit max time"


def main():
    L=initialize()
    n=Network()
    E=[]
    for i in range(1,len(L)):
        E.append(Event(L[i]))
    
    runsim(E,n)

main()
