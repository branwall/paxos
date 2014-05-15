from __future__ import division
import sys
proposers=[]
acceptors=[]
tmax=None
tick=0
mtypes=['PROP','PREP','PROM','ACC','ACCD','REJ']
message_print_type={'PROP':'PROPOSE','PREP':'PREPARE','PROM':'PROMISE','ACC':'ACCEPT','ACCD':'ACCEPTED','REJ':'REJECTED'}
ctypes=['P','A']
class C: #This is a class for both proposers and acceptors, and the type is stored in self.ty
    def __init__(self,num,ty):
        self.num=num
        assert ctypes.count(ty)>0
        self.ty=ty
        self.failed=False
        self.lastpromised=None # for acceptor
        self.highestproposal=None #for acceptor
        self.acceptedvalue=None #for acceptor
        self.currentproposalnum=None #for Proposer
        self.currentproposalval=None #For Proposer
        self.consensus=None
        self.promlist={} #For promise messages to Proposer
        self.acclist={} #For accepted messages to Proposer
        self.rejlist={} #For rejected messages to proposer
    def fail(self):
        self.failed=True
    def recover(self):
        self.failed=False
    def display(self):
        print " -----------------"
        print "|   %s # %d  |" % (("Proposer" if self.ty == 'P' else "Acceptor"), self.num)
        print "|   Failed?  %s   |" % ("yes" if self.failed==True else "no")
        print (("|  Last Prom = %d  |" % self.lastpromised)
               if self.ty=='A' 
               else ("|CurrentProp=%d(%d)|" % self.currentproposalnum,self.currentproposalval))
        if self.ty=='A':
            print ("| Highest Prop = %d|" % self.highestproposal) 
        print " -----------------"
        if self.ty=='P':
            print "ACCs",self.acclist
            print "REJs",self.rejlist
class Message: #Message which a proposer might send to an acceptor or vice versa
    def __init__(self,ty,dest,source,propid,prior=None,val=None):
        assert mtypes.index(ty)>=0
        self.kind=ty
        self.dst=dest
        self.src=source
        self.propid=propid
        self.prior=prior
        self.val=val
    def minidisplay(self):
        print "%d: Msg type %s from %s%d to %s%d" % (self.propid, self.kind, self.src.ty,
                                                     self.src.num, self.dst.ty,self.dst.num)
class Network: #Defines a queue structure and enq and deq operations.  Accepts a list of messages.
    def __init__(self):
        self.counter=0
        self.queue=[]
    def enq(self,msg):
        self.queue.append(msg)
    def deq(self):
        for c,i in enumerate(self.queue):
            if i.src.failed==False and i.dst.failed==False:
                return self.queue.pop(c)
    def display(self):
        print "-----Network:-----"
        for i in self.queue:
            Message.minidisplay(i)
        print "------------------"
class Event: #These encode info received from stdin to be passed around when running sim.
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

def initialize(): #will make a list of valid input file
    L=[]
    for line in sys.stdin:
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

def etick(li): #Returns the first tick in a list of events
    return li[0].tick

def tf(t): #Returns a string containing the proper format for the tick, given its length of digits.
    if t<10:
        return "  " + str(t)
    elif t<100:
        return " " + str(t)
    return str(t)

def process_events(t,li,n): #tick to process, 
    global tick
    for c,i in enumerate(li):
        tickformat=tf(t)
        if i.tick>t:
            return li[c:]
        if i.ty=="P":
            print "%s:    -> %s%d PROPOSE v=%d" % (tickformat,i.c.ty,i.c.num,i.value)
            n.counter+=1
            old_prop=i.c.currentproposalnum
            i.c.currentproposalval=i.value
            i.c.currentproposalnum=n.counter
            for cc,ii in enumerate(acceptors):
                Network.enq(n,Message("PREP",ii,i.c,n.counter,old_prop,i.value))
            tick+=1
        elif i.ty=="F":
            C.fail(i.c)
            print "%s: ** %s%d FAILS **" % (tickformat,i.c.ty,i.c.num)
        elif i.ty=="R":
            C.recover(i.c)
            print "%s: ** %s%d RECOVERS **" % (tickformat,i.c.ty,i.c.num)

def deliver_msg(n):
    m=Network.deq(n)
    sc=m.src # source computer
    dc=m.dst # destination computer
    t=m.kind # message type
    tickformat=tf(tick)
    if t=='PROP': #If a proposal message is received
        print "Error, proposals must come from outside the system"
    elif t=='PREP': #If a 'prepare' message is received and proposal ID is what's expected, send a PROM
        print "%s: %s%d -> %s%d %s n=%d" % (tickformat,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid) 
        if dc.highestproposal<=m.propid:
            old_proposal=dc.highestproposal
            old_proposal_val=dc.lastpromised
            if dc.acceptedvalue!=None:
                old_proposal_val=dc.acceptedvalue
            dc.lastpromised=m.val
            dc.highestproposal=m.propid
            Network.enq(n,Message('PROM',sc,dc,m.propid,old_proposal,old_proposal_val))
    elif t=='PROM': #If a promise is received, make a note in the Proposer's dictionary. Send ACC if maj. reached.
        if sc.acceptedvalue!=None:
            dc.promlist['prev']=sc.acceptedvalue
        if m.propid in dc.promlist:
            dc.promlist[m.propid]+=1
        else:
            dc.promlist[m.propid]=1

        if dc.promlist[m.propid]>(len(acceptors)/2) and dc.promlist[m.propid]-1<(len(acceptors)/2): 
            # we have an majority (assume we've already done this if we have more than necessary for a majority.
            if 'prev' in dc.promlist:
                val=dc.promlist['prev']
                del dc.promlist['prev']
            else:
                val=dc.currentproposalval
            for c,i in enumerate(acceptors):
                Network.enq(n,Message('ACC',i,dc,m.propid,None,val))
        if sc.acceptedvalue==None:
            print "%s: %s%d -> %s%d %s n=%d (Prior: None)" % (tickformat,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid)
        else: 
            print ("%s: %s%d -> %s%d %s n=%d (Prior: n=%d, v=%d)" % 
                   (tickformat,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid,m.prior,m.val)) 
    elif t=='ACC': #If we receive an ACCEPT message, decide whether to reject it or store it to memory and send accepted.
        print "%s: %s%d -> %s%d %s n=%d v=%d" % (tickformat,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid,m.val)
        if dc.highestproposal>m.propid:
            Network.enq(n,Message('REJ',sc,dc,m.propid,None,None))
        else:
            dc.acceptedvalue=m.val
            Network.enq(n,Message('ACCD',sc,dc,m.propid,None,m.val))
    elif t== 'REJ': #Make note of rejections, restart proposal if too many.
        print "%s: %s%d -> %s%d %s n=%d" % (tickformat,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid) 
        if m.propid in dc.rejlist:
            dc.rejlist[m.propid]+=1
        else:
            dc.rejlist[m.propid]=1
        if dc.rejlist[m.propid]>len(acceptors)/2 and dc.rejlist[m.propid]-1<(len(acceptors)/2):
            #repropose
            n.counter+=1
            dc.currentproposalnum=n.counter
            for cc,ii in enumerate(acceptors):
                Network.enq(n,Message("PREP",ii,dc,n.counter))
    else: #t=='ACCD': Store this in memory, decide whether consensus was reached.
        if m.propid in dc.acclist:
            dc.acclist[m.propid]+=1
        else:
            dc.acclist[m.propid]=1
        if dc.acclist[m.propid]>len(acceptors)/2 and dc.acclist[m.propid]-1<(len(acceptors)/2):
            dc.consensus=m.val
        print "%s: %s%d -> %s%d %s n=%d v=%d" % (tickformat,sc.ty,sc.num,dc.ty,dc.num,message_print_type[t],m.propid,m.val) 
def consensus(comp):
    if comp.consensus!=None:
        print "%s%d has reached consensus (proposed %d, accepted %d)" % (comp.ty,comp.num,comp.currentproposalval,comp.consensus)
    else:
        print "%s%d did not reach consensus" % (comp.ty,comp.num)

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
        ty=None
        if ntwk.queue == [] and elist == None:
            print ""
            for i in proposers:
                consensus(i)
            return
        elif elist!=None and etick(elist)==tick:
            elist = process_events(tick,elist,ntwk)
            if network_empty(ntwk.queue)!=True:
                deliver_msg(ntwk)
        elif network_empty(ntwk.queue)!=True:
            deliver_msg(ntwk)
        else: #No events or active network
            print "%s:" % tf(tick)
        tick+=1
    print ""
    for i in proposers:
        consensus(i)

def main():
    L=initialize()
    n=Network()
    E=[]
    for i in range(1,len(L)):
        E.append(Event(L[i]))
    runsim(E,n)

main()
