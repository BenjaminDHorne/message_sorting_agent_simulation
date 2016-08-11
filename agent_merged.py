
import networkx as nx
import random
import collections
import numpy

class Agent(object):
    def __init__(self, capacity=1, psend=0.6):
        self.neighbors = []
        self.inbox = []
        self.sent = set()
        self.capacity = capacity
        self.psend = psend
        self.inboxfacts = set()

    def clear(self):
        self.inbox = []
        self.sent = set()
        self.inboxfacts = set()

        
    def stats(self):
        return len(self.inbox), len(self.sent)
    
    def setneighbors(self, nlist):
        self.neighbors = nlist
        
    def fifo_getnewfact(self, factnum):
        #### fixed, reversed ordering for performance
        self.inbox.insert( 0, factnum )

    def fifond_getnewfact(self, factnum):
        if factnum not in self.inboxfacts:
            self.inbox.insert( 0, factnum )
            self.inboxfacts.add( factnum )
        
        
    def lifo_getnewfact(self, factnum):
        ### fixed, reversed ordering for performance
        self.inbox.append( factnum )

    def lifond_getnewfact(self, factnum):
        if factnum not in self.inboxfacts:
            self.inbox.append( factnum )
            self.inboxfacts.add( factnum )
        
    def fifo_gettopfact(self):
        ### fixed, reversed ordering for performance
        return self.inbox.pop()

    def fifond_gettopfact(self):
        fact = self.inbox.pop()
        self.inboxfacts.remove(fact)
        return fact
    
    def lifo_gettopfact(self):
        ### fixed, reversed ordering for performance
        return self.inbox.pop()

    def lifond_gettopfact(self):
        fact = self.inbox.pop()
        self.inboxfacts.remove(fact)
        return fact
    
    def fifo_sendfact(self):
        to_send = []
        for i in xrange(self.capacity):
            if len(self.inbox) == 0:
                break
            fact = self.fifo_gettopfact()
            if fact not in self.sent and random.random() <= self.psend:
                self.sent.add(fact)
                for j in self.neighbors:
                    to_send.append( (fact,j) )
        return to_send
    
    def lifo_sendfact(self):
        to_send = []
        for i in xrange(self.capacity):
            if len(self.inbox) == 0:
                break
            fact = self.lifo_gettopfact()
            if fact not in self.sent and random.random() <= self.psend:
                self.sent.add(fact)                    
                for j in self.neighbors:
                    to_send.append( (fact,j) )
        return to_send

def create_network(num_agents, capacity, psend, num_neighbors = 5, rewire_prob=0):
    x = nx.watts_strogatz_graph(num_agents, num_neighbors, rewire_prob)
    #x = nx.barabasi_albert_graph(num_agents, num_neighbors)
    agents = []
    for i in xrange(num_agents):
        newagent = Agent(capacity, psend)
        newagent.setneighbors( x.neighbors(i) )
        agents.append( newagent )
    return agents

def send_facts(agents, num_agents, numfacts, startindex, changed=[]):
    for fact in xrange(startindex, numfacts+startindex):
        j = random.randint(0,num_agents-1)
        #agents[j].fifo_getnewfact(fact)
        agents[j].lifo_getnewfact(fact)
    if len(changed) > 0:
        for fact in xrange(startindex, numfacts+startindex):
            if random.random() <= 0.5:
                j = random.choice(changed)
                #agents[j].fifo_getnewfact(fact)
                agents[j].lifo_getnewfact(fact)

def one_step_simulation(agents, num_agents, factdist, remove_duplicates, isfifo=True, isdebug=False):
    to_send = []
    idle = 0
    for i in xrange(num_agents):
        sent_by_agent = agents[i].fifo_sendfact()
        to_send.extend(sent_by_agent)
        if isdebug and len(sent_by_agent) == 0:
            idle += 1
            
    random.shuffle(to_send)
    if isfifo:  ##FIFO or FIFOND
        if remove_duplicates:
            if isdebug:
                for (fact,i) in to_send:
                    agents[i].fifond_getnewfact(fact)
                    factdist[fact] += 1
            else:
                for (fact,i) in to_send:
                    agents[i].fifond_getnewfact(fact)
            
        else:
            if isdebug:
                for (fact,i) in to_send:
                    agents[i].fifo_getnewfact(fact)
                    factdist[fact] += 1
            else:
                for (fact,i) in to_send:
                    agents[i].fifo_getnewfact(fact)
            
    else: ## LIFO or LIFOND
        if remove_duplicates:
            if isdebug:
                for (fact,i) in to_send:
                    agents[i].lifond_getnewfact(fact)
                    factdist[fact] += 1
            else:
                for (fact,i) in to_send:
                    agents[i].lifond_getnewfact(fact)
            
        else:
            if isdebug:
                for (fact,i) in to_send:
                    agents[i].lifo_getnewfact(fact)
                    factdist[fact] += 1
            else:
                for (fact,i) in to_send:
                    agents[i].lifo_getnewfact(fact)
    return idle
        
def print_agent_graph(agents, num_agents):
    ndist = []
    for i in xrange(num_agents):
        ndist.append ( len(agents[i].neighbors) )
    ndist.sort()
    print "Neighbor median:", ndist[ num_agents/2 ]
    print 
    
def get_agent_stats(agents, num_agents, isprint=True):
    inbox, known = [],[]
    for i in xrange(num_agents):
        ai, ak = agents[i].stats()
        inbox.append(ai)
        known.append(ak)
    known.sort()
    avginbox = sum(inbox)/float(num_agents)
    avgknown = sum(known)/float(num_agents)
    if isprint:
        print "(min/avg/max) inbox: (%d,%d,%d) known: (%d,%d,%d)"\
            %(min(inbox), avginbox, max(inbox),\
              min(known), avgknown, max(known))
    return avginbox, avgknown

def run_burst_simulation(agents, factdist, remove_duplicates, \
                         num_agents, maxsteps=1500, isfifo=True, isdebug=True):
    incsteps = (maxsteps/5)
    total_idle = 0
    for steps in xrange(maxsteps):
        idle = one_step_simulation(agents, num_agents, factdist, remove_duplicates, isfifo, isdebug)
        total_idle += idle
        if isdebug and steps % incsteps == 0:
            avginbox, avgknown = get_agent_stats(agents, num_agents, isprint=True)
    if isdebug:
        print "Total idle/per agent:", int(total_idle/float(num_agents))
            
    return get_agent_stats(agents, num_agents, isprint=False)

def run_streaming_simulation(agents, factdist, changed, \
                             end_stream, stream_interval, stream_amount, starting_idx, \
                             remove_duplicates,\
                             num_agents, maxsteps=1500, isfifo=True, isdebug=True):
    incsteps = (maxsteps/5)
    last_idx = starting_idx
    total_idle = 0
    for steps in xrange(end_stream):
        idle = one_step_simulation(agents, num_agents, factdist, remove_duplicates, isfifo, isdebug)
        total_idle += idle
        if steps % stream_interval == 0:
            send_facts(agents, num_agents, stream_amount, last_idx, changed)
            last_idx += stream_amount
        if isdebug and steps % incsteps == 0:
            avginbox, avgknown = get_agent_stats(agents, num_agents, isprint=True)
    for steps in xrange(end_stream,maxsteps):
        idle = one_step_simulation(agents, num_agents, factdist, remove_duplicates, isfifo, isdebug)
        total_idle += 1
        if isdebug and steps % incsteps == 0:
            avginbox, avgknown = get_agent_stats(agents, num_agents, isprint=True)
    if isdebug:
        print "Total facts generated", last_idx
        print "Total idle/per agent:", int(total_idle/float(num_agents))
    return get_agent_stats(agents, num_agents, isprint=False)


def clear_agents(agents, num_agents):
    for i in xrange(num_agents):
        agents[i].clear()
        

def print_agent_stat(agents, num_agents):
    numbins = 5
    known = []
    known_facts = set()
    for i in range(num_agents):
        ai, ak = agents[i].stats()
        known.append(ak)
        known_facts = known_facts | agents[i].sent

    print
    print "Total # facts known", len(known_facts)
    sizes, medvals = numpy.histogram(known,bins=numbins)
    print
    print "Agent knowledge distribution:"
    for i in xrange(numbins):
        s,m = sizes[i], medvals[i]
        if s>0:
            print "%d: %.2f -" %(s,m),
    print

def print_fact_stat(factdist):
    numbins = 5
    vals = []
    vals2 = []
    for fact in factdist:
        vals.append( factdist[fact] )
        vals2.append( (factdist[fact], fact) )
    vals2.sort()
    sizes, medvals = numpy.histogram(vals,bins=numbins)
    print
    print "Fact distribution:"

    idx = 0
    for i in xrange(numbins):
        s,m = sizes[i], medvals[i]
        if s>0:
            print "%d: %.2f -" %(s,m),
            # while vals2[idx][0] <= m:
            #     print vals2[idx][1],
            #     idx += 1
            # print
            # raw_input()
    print
    
def change_capacity(agents, num_agents, new_capacity=25, change_prob=0.1):
    for i in xrange(num_agents):
        if random.random() <= change_prob:
            agents[i].capacity = new_capacity

def change_informed(agents, num_agents, new_psend, change_inf_prob):
    changed = []
    for i in xrange(num_agents):
        if random.random() <= change_inf_prob:
            agents[i].psend = new_psend
            changed.append(i)
    return changed

def network_setup(setup):
    changed = []
    agents = create_network(setup['num_agents'], setup['capacity'], \
                            setup['psend'], setup['num_neighbors'], setup['rewire_prob'])
    if setup['is_change_capacities']:
        change_capacity(agents, setup['num_agents'], setup['new_capacity'], setup['change_prob'])
    if setup['is_change_informed']:
        changed = change_informed(agents, setup['num_agents'], \
                                  setup['new_psend'], setup['change_inf_prob'])
    return agents, changed

def run_tests(setup, factdist):

    ##graph creation
    agents, changed = network_setup(setup)
        
    #print_agent_graph(agents, setup['num_agents'])

    ##simulation
    if setup['isfifo']:
        if setup['remove_duplicates']:
            print "FIFOND"
        else:
            print "FIFO"
    else:
        if setup['remove_duplicates']:
            print "LIFOND"
        else:
            print "LIFO"


    if setup['isstream']:
        starting_num_facts = setup['initial_facts']
    else:
        starting_num_facts = setup['num_facts']
    
    avgdist = 0
    for i in xrange(setup['num_repeat']):
        send_facts(agents, setup['num_agents'],starting_num_facts,0 , changed)
        if i == setup['num_repeat']-1:
            if setup['isstream']:
                avginbox, avgknown = run_streaming_simulation(agents, factdist, \
                                                              changed, \
                                                              setup['end_stream'],\
                                                              setup['stream_interval'], \
                                                              setup['stream_amount'], \
                                                              starting_num_facts,\
                                                              setup['remove_duplicates'], \
                                                              setup['num_agents'], setup['maxsteps'], \
                                                              setup['isfifo'], setup['isdebug'])
            else:
                avginbox, avgknown = run_burst_simulation(agents, factdist,\
                                                          setup['remove_duplicates'], \
                                                          setup['num_agents'], setup['maxsteps'], \
                                                          setup['isfifo'], setup['isdebug'])
            if setup['isdebug']:
                print_fact_stat(factdist)
                print_agent_stat(agents, setup['num_agents'])
        else:
            if setup['isstream']:
                avginbox, avgknown = run_streaming_simulation(agents, factdist, \
                                                              changed,\
                                                              setup['end_stream'], \
                                                              setup['stream_interval'], \
                                                              setup['stream_amount'], \
                                                              starting_num_facts,\
                                                              setup['remove_duplicates'], \
                                                              setup['num_agents'], setup['maxsteps'], \
                                                              setup['isfifo'], isdebug=False)
            else:
                avginbox, avgknown = run_burst_simulation(agents, factdist, \
                                                          setup['remove_duplicates'], \
                                                          setup['num_agents'], setup['maxsteps'], \
                                                          setup['isfifo'], isdebug=False)
            agents, changed = network_setup(setup)            

        if setup['isstream']:
            total_facts = setup['initial_facts'] + \
                          (setup['end_stream']/setup['stream_interval'])*setup['stream_amount']
            avgdist += avgknown/float(total_facts)
        else:
            avgdist += avgknown/float(setup['num_facts'])

    print "Overall (percentage facts known): %.2f" %(avgdist/setup['num_repeat'])

if __name__ == "__main__":
    setup = {}
    setup['num_agents'] = 256
    setup['psend'] = 0.6
    setup['capacity'] = 1
    setup['num_neighbors'] = 10
    setup['rewire_prob'] = 0.1
    setup['num_facts'] = 2500
    setup['maxsteps'] = 1000
    setup['num_repeat'] = 1
    setup['isfifo'] = False
    setup['remove_duplicates'] = True
    setup['isdebug'] = True

    ## streaming specs if streaming is used.
    setup['isstream'] = False
    setup['initial_facts'] = 250
    setup['stream_interval'] = 5  ##at each how many steps
    setup['stream_amount'] = 1
    setup['end_stream'] = 10000

    # setup['num_agents'] = 256
    # setup['psend'] = 0.6
    # setup['capacity'] = 1
    # setup['num_neighbors'] = 10
    # setup['num_facts'] = 50000
    # setup['maxsteps'] = 10000
    # setup['num_repeat'] = 1
    
    setup['is_change_capacities'] = False
    setup['new_capacity'] =25
    setup['change_prob'] = 0.5

    setup['is_change_informed'] = False
    setup['new_psend'] = 0.8
    setup['change_inf_prob'] = 0.5   

    ##stats
    factdist = collections.defaultdict(lambda: 0)

    if setup['is_change_capacities']:
        print "Changing capacities to %d by %.1f probability" \
            %(setup['new_capacity'], setup['change_prob'])

    if setup['is_change_informed']:
        print "Changing %.1f percent agents to more informed with %.1f send probability" \
            %(setup['change_inf_prob'], setup['new_psend'])
        
    #run simulation
    # for stream in [False, True]:
    #     if stream:
    #         print "Streaming information (%d facts-%d agents)" \
    #             %((setup['initial_facts'] + (setup['maxsteps']/setup['stream_interval'])*setup['stream_amount']),\
    #             setup['num_agents'])
    #     else:
    #         print "Burst information (%d facts-%d agents)" %(setup['num_facts'],setup['num_agents'])
    #     setup['isstream'] = stream
    #     for fifo in [True, False]:
    #         setup['isfifo'] = fifo
    #         for dup in [False, True]:
    #             setup['remove_duplicates'] = dup
    #             run_tests(setup, factdist)
    #     print

    run_tests(setup, factdist)
